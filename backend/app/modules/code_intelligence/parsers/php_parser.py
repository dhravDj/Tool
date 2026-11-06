"""PHP source code parser and security auditor."""

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


class PHPParser(BaseLanguageParser):
    """Parser for PHP files extracting namespaces, classes, methods, and security vulnerabilities."""

    @property
    def language(self) -> str:
        return "php"

    @property
    def supported_extensions(self) -> list[str]:
        return ["php", "phtml"]

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
        syntax_validation = SyntaxValidationResult(parser_used="php-parser")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith(("//", "#", "/*", "*")))
        code_lines_count = total_lines - blank_lines - comment_lines

        # 1. Namespaces and Use statements
        use_pattern = re.compile(r"""use\s+([A-Za-z0-9_\\]+)(?:\s+as\s+(\w+))?;""")
        for match in use_pattern.finditer(content):
            target = match.group(1)
            alias = match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            root_ns = target.split("\\")[0]
            is_ext = root_ns not in ("App", "Database", "Tests")

            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=target,
                    imported_symbols=[alias or target.split("\\")[-1]],
                    is_relative=not is_ext,
                    is_external=is_ext,
                    alias=alias,
                    line_number=line_no,
                )
            )
            if is_ext and root_ns not in [d.name for d in dependencies]:
                dependencies.append(CodeDependency(name=root_ns, dependency_type="composer_package"))

        # 2. Classes, Interfaces, Traits
        class_pattern = re.compile(r"""(?:abstract\s+|final\s+)?(class|interface|trait)\s+(\w+)""")
        for match in class_pattern.finditer(content):
            kind = match.group(1)
            name = match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=name,
                    symbol_type=kind,
                    start_line=line_no,
                    end_line=line_no,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        # 3. Functions & Methods
        func_pattern = re.compile(
            r"""(?:(?:public|protected|private|static)\s+)*function\s+(\w+)\s*\(([^)]*)\)"""
        )
        for match in func_pattern.finditer(content):
            name = match.group(1)
            raw_params = [p.strip() for p in match.group(2).split(",") if p.strip()]
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=name,
                    symbol_type="function",
                    start_line=line_no,
                    end_line=line_no,
                    parameters=raw_params,
                    visibility="public",
                    source_reference=f"function {name}(...)",
                )
            )

        # 4. Diagnostics: Dangerous PHP execution functions
        dangerous_php = [
            ("eval", "SEC-PHP-EVAL", "error", "Arbitrary code execution via eval()."),
            ("shell_exec", "SEC-PHP-SHELL-EXEC", "error", "Direct command execution via shell_exec()."),
            ("passthru", "SEC-PHP-PASSTHRU", "error", "Direct command execution via passthru()."),
            ("exec", "SEC-PHP-EXEC", "warning", "System execution call via exec()."),
        ]

        for func_name, rule_id, sev, msg in dangerous_php:
            for match in re.finditer(rf"\b{func_name}\s*\(", content):
                line_no = content[: match.start()].count("\n") + 1
                diagnostics.append(
                    CodeDiagnostic(
                        diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                        rule_id=rule_id,
                        severity=sev,
                        message=msg,
                        file_path=filename,
                        start_line=line_no,
                        end_line=line_no,
                        column=1,
                        tool_name="php-security-scanner",
                        evidence=match.group(0).strip(),
                        suggested_remediation="Avoid executing dynamic shell commands or arbitrary code.",
                    )
                )

        func_count = sum(1 for s in symbols if s.symbol_type == "function")
        class_count = sum(1 for s in symbols if s.symbol_type in ("class", "interface", "trait"))
        branch_count = len(re.findall(r"""\b(?:if|else\s+if|switch|case|foreach|for|while)\b|&&|\|\|""", content))

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
