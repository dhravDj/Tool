"""SQL parser and schema relationship analyzer using SQLGlot."""

import re
import uuid
from typing import Any

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.modules.code_intelligence.parsers.base import BaseLanguageParser
from app.modules.code_intelligence.schemas.code_document import (
    CodeDependency,
    CodeDiagnostic,
    CodeImport,
    CodeMetrics,
    CodeSymbol,
    SyntaxValidationResult,
)


class SQLParser(BaseLanguageParser):
    """Static SQL parser extracting tables, columns, constraints, queries, and schema graphs."""

    @property
    def language(self) -> str:
        return "sql"

    @property
    def supported_extensions(self) -> list[str]:
        return ["sql", "ddl", "dml"]

    def parse(
        self,
        content: str,
        filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> tuple[
        list[CodeSymbol],
        list[CodeImport],
        list[CodeDependency],
        CodeMetrics,
        list[CodeDiagnostic],
        SyntaxValidationResult,
    ]:
        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        dependencies: list[CodeDependency] = []
        diagnostics: list[CodeDiagnostic] = []
        syntax_validation = SyntaxValidationResult(parser_used="sqlglot")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith("--"))

        # 1. SQLGlot Static Parsing
        statements: list[Any] = []
        try:
            statements = [stmt for stmt in sqlglot.parse(content) if stmt is not None]
        except ParseError as e:
            syntax_validation.is_valid = False
            syntax_validation.errors.append(str(e))
            diagnostics.append(
                CodeDiagnostic(
                    diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                    rule_id="SQL-SYNTAX-ERROR",
                    severity="error",
                    message=f"SQL Parse Error: {e}",
                    file_path=filename,
                    start_line=1,
                    end_line=1,
                    column=1,
                    tool_name="sqlglot",
                    suggested_remediation="Verify SQL syntax compliance for the target dialect.",
                )
            )

        # 2. Extract DDL Tables, Views, Columns, Constraints
        table_count = 0
        view_count = 0
        join_count = 0
        tables_seen: set[str] = set()

        for stmt in statements:
            if isinstance(stmt, exp.Create):
                # Tables or Views
                kind = stmt.args.get("kind", "").upper()
                schema = stmt.this
                if isinstance(schema, exp.Schema):
                    table_name = schema.this.name if schema.this else "unknown_table"
                    sym_type = "view" if "VIEW" in kind else "table"
                    if sym_type == "table":
                        table_count += 1
                    else:
                        view_count += 1

                    tables_seen.add(table_name.lower())
                    cols: list[str] = []
                    has_pk = False

                    for expr in schema.expressions:
                        if isinstance(expr, exp.ColumnDef):
                            c_name = expr.name
                            c_type = str(expr.kind) if expr.kind else "ANY"
                            col_sig = f"{c_name} {c_type}"
                            cols.append(col_sig)

                            # Check primary key or foreign key
                            for constraint in expr.args.get("constraints", []):
                                c_str = str(constraint).upper()
                                if "PRIMARY KEY" in c_str:
                                    has_pk = True
                                if "REFERENCES" in c_str or "FOREIGN KEY" in c_str:
                                    # Extract referenced table
                                    ref_match = re.search(r"REFERENCES\s+([A-Za-z0-9_]+)", c_str, re.IGNORECASE)
                                    if ref_match:
                                        target_table = ref_match.group(1)
                                        dependencies.append(
                                            CodeDependency(
                                                name=target_table,
                                                dependency_type="foreign_key_table",
                                            )
                                        )
                                        imports.append(
                                            CodeImport(
                                                statement=f"REFERENCES {target_table}",
                                                module_name=target_table,
                                                imported_symbols=[target_table],
                                                is_relative=True,
                                                is_external=False,
                                                line_number=1,
                                            )
                                        )

                    if sym_type == "table" and not has_pk:
                        diagnostics.append(
                            CodeDiagnostic(
                                diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                                rule_id="SQL-MISSING-PK",
                                severity="info",
                                message=f"Table '{table_name}' has no explicit PRIMARY KEY constraint.",
                                file_path=filename,
                                start_line=1,
                                end_line=1,
                                column=1,
                                tool_name="sql-analyzer",
                                suggested_remediation="Add a primary key column to ensure row identity.",
                            )
                        )

                    symbols.append(
                        CodeSymbol(
                            symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                            name=table_name,
                            symbol_type=sym_type,
                            start_line=1,
                            end_line=1,
                            parameters=cols,
                            documentation=f"{len(cols)} columns defined",
                            source_reference=f"CREATE {kind} {table_name}",
                        )
                    )

            elif isinstance(stmt, exp.Select):
                # Count joins and CTEs
                joins = stmt.args.get("joins", [])
                join_count += len(joins)
                for j in joins:
                    if hasattr(j.this, "name") and j.this.name:
                        joined_tbl = j.this.name
                        if joined_tbl.lower() not in tables_seen:
                            dependencies.append(
                                CodeDependency(
                                    name=joined_tbl,
                                    dependency_type="referenced_table",
                                )
                            )

            elif isinstance(stmt, exp.Drop):
                kind = stmt.args.get("kind", "").upper()
                name = str(stmt.this)
                diagnostics.append(
                    CodeDiagnostic(
                        diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                        rule_id="SQL-DESTRUCTIVE-DDL",
                        severity="warning",
                        message=f"Destructive DDL statement detected: DROP {kind} {name}.",
                        file_path=filename,
                        start_line=1,
                        end_line=1,
                        column=1,
                        tool_name="sql-security-scanner",
                        suggested_remediation="Ensure drop script has appropriate backup and permission safeguards.",
                    )
                )

        code_lines = total_lines - blank_lines - comment_lines
        complexity = float(1 + join_count + len(statements))

        metrics = CodeMetrics(
            total_lines=total_lines,
            code_lines=max(0, code_lines),
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=len([s for s in symbols if s.symbol_type == "view"]),
            class_count=table_count,
            import_count=len(imports),
            cyclomatic_complexity=round(complexity, 1),
            nesting_depth=2 if join_count > 0 else 1,
        )

        return symbols, imports, dependencies, metrics, diagnostics, syntax_validation
