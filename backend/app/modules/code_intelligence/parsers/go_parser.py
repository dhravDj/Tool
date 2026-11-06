"""Go source code parser and structural extractor."""

import re
import uuid
from typing import Any

from app.modules.code_intelligence.parsers.base import BaseLanguageParser
from app.modules.code_intelligence.schemas.code_document import (
    CodeDependency,
    CodeDiagnostic,
    CodeImport,
    CodeMetrics,
    CodeSymbol,
    SyntaxValidationResult,
)


class GoParser(BaseLanguageParser):
    """Parser for Go source files extracting package, imports, structs, interfaces, functions, and receiver methods."""

    @property
    def language(self) -> str:
        return "go"

    @property
    def supported_extensions(self) -> list[str]:
        return ["go"]

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
        syntax_validation = SyntaxValidationResult(parser_used="go-parser")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith("//"))
        code_lines_count = total_lines - blank_lines - comment_lines

        # 1. Imports
        # Single import: import "fmt" OR Block import: import ( "fmt" \n "github.com/..." )
        single_import = re.compile(r"""import\s+['"]([^'"]+)['"]""")
        for match in single_import.finditer(content):
            pkg = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            is_ext = "/" in pkg and not pkg.startswith("net/") and not pkg.startswith("crypto/")
            imports.append(
                CodeImport(
                    statement=f'import "{pkg}"',
                    module_name=pkg,
                    imported_symbols=[pkg.split("/")[-1]],
                    is_relative=False,
                    is_external=is_ext,
                    line_number=line_no,
                )
            )
            if is_ext and pkg not in [d.name for d in dependencies]:
                dependencies.append(CodeDependency(name=pkg, dependency_type="external"))

        block_import = re.compile(r"""import\s*\(([^)]+)\)""")
        for match in block_import.finditer(content):
            block_body = match.group(1)
            for pkg_match in re.finditer(r"""['"]([^'"]+)['"]""", block_body):
                pkg = pkg_match.group(1)
                line_no = content[: match.start()].count("\n") + 1
                is_ext = "/" in pkg and not pkg.startswith("net/") and not pkg.startswith("crypto/")
                imports.append(
                    CodeImport(
                        statement=f'import "{pkg}"',
                        module_name=pkg,
                        imported_symbols=[pkg.split("/")[-1]],
                        is_relative=False,
                        is_external=is_ext,
                        line_number=line_no,
                    )
                )
                if is_ext and pkg not in [d.name for d in dependencies]:
                    dependencies.append(CodeDependency(name=pkg, dependency_type="external"))

        # 2. Structs & Interfaces
        type_def = re.compile(r"""type\s+(\w+)\s+(struct|interface)\s*\{""")
        for match in type_def.finditer(content):
            name = match.group(1)
            kind = match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=name,
                    symbol_type=kind,
                    start_line=line_no,
                    end_line=line_no,
                    visibility="public" if name[0].isupper() else "private",
                    source_reference=match.group(0).strip(),
                )
            )

        # 3. Functions & Methods
        # func (r *Receiver) MethodName(params) (returns) { OR func FuncName(params) {
        func_pattern = re.compile(r"""func\s+(?:\(([^)]+)\)\s+)?(\w+)\s*\(([^)]*)\)""")
        for match in func_pattern.finditer(content):
            receiver = match.group(1)
            f_name = match.group(2)
            raw_params = [p.strip() for p in match.group(3).split(",") if p.strip()]
            line_no = content[: match.start()].count("\n") + 1
            sym_type = "method" if receiver else "function"
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=f_name,
                    symbol_type=sym_type,
                    start_line=line_no,
                    end_line=line_no,
                    parameters=raw_params,
                    visibility="public" if f_name[0].isupper() else "private",
                    source_reference=f"func {f'({receiver}) ' if receiver else ''}{f_name}(...)",
                )
            )

        # 4. Diagnostics: panic() usage
        if "panic(" in content:
            diagnostics.append(
                CodeDiagnostic(
                    diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                    rule_id="GO-PANIC-USAGE",
                    severity="warning",
                    message="Direct call to panic() detected. Prefer returning explicit error values.",
                    file_path=filename,
                    start_line=1,
                    end_line=1,
                    column=1,
                    tool_name="go-analyzer",
                    suggested_remediation="Return (result, error) following idiomatic Go error handling.",
                )
            )

        func_count = sum(1 for s in symbols if s.symbol_type in ("function", "method"))
        class_count = sum(1 for s in symbols if s.symbol_type in ("struct", "interface"))
        branch_count = len(re.findall(r"""\b(?:if|for|switch|case|select)\b|&&|\|\|""", content))

        metrics = CodeMetrics(
            total_lines=total_lines,
            code_lines=max(0, code_lines_count),
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=func_count,
            class_count=class_count,
            import_count=len(imports),
            avg_function_length=round(float(code_lines_count / max(1, func_count)), 1) if func_count else 0.0,
            cyclomatic_complexity=float(1 + branch_count),
            nesting_depth=2,
        )

        return symbols, imports, dependencies, metrics, diagnostics, syntax_validation
