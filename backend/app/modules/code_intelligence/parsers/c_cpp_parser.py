"""C and C++ source code parser and security analyzer."""

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


class CCppParser(BaseLanguageParser):
    """Parser for C and C++ source files extracting includes, functions, structs, classes, and memory risks."""

    @property
    def language(self) -> str:
        return "c"

    @property
    def supported_extensions(self) -> list[str]:
        return ["c", "h", "cpp", "cc", "cxx", "hpp"]

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
        syntax_validation = SyntaxValidationResult(parser_used="c-cpp-parser")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())

        comment_lines = 0
        in_block_comment = False
        code_lines_count = 0

        for line in lines:
            s = line.strip()
            if in_block_comment:
                comment_lines += 1
                if "*/" in s:
                    in_block_comment = False
            elif s.startswith("/*"):
                comment_lines += 1
                if "*/" not in s:
                    in_block_comment = True
            elif s.startswith("//"):
                comment_lines += 1
            elif not s:
                pass
            else:
                code_lines_count += 1

        # 1. Includes (#include <...> vs #include "...")
        include_pattern = re.compile(r"""#include\s+([<"])([^>"]+)([>"])""")
        for match in include_pattern.finditer(content):
            delim_start = match.group(1)
            header_path = match.group(2)
            is_system = delim_start == "<"
            line_no = content[: match.start()].count("\n") + 1

            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=header_path,
                    imported_symbols=[header_path],
                    is_relative=not is_system,
                    is_external=is_system,
                    line_number=line_no,
                )
            )
            if is_system and header_path not in [d.name for d in dependencies]:
                dependencies.append(CodeDependency(name=header_path, dependency_type="system_header"))

        # 2. Classes and Structs
        struct_pattern = re.compile(r"""(?:typedef\s+)?(struct|class|enum)\s+(\w+)\s*\{""")
        for match in struct_pattern.finditer(content):
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

        # 3. Functions: return_type name(args) {
        func_pattern = re.compile(
            r"""(?:[a-zA-Z0-9_*&<>]+\s+)+(\w+)\s*\(([^)]*)\)\s*(?:const)?\s*\{"""
        )
        for match in func_pattern.finditer(content):
            f_name = match.group(1)
            if f_name in ("if", "while", "for", "switch", "catch"):
                continue
            raw_params = [p.strip() for p in match.group(2).split(",") if p.strip()]
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=f_name,
                    symbol_type="function",
                    start_line=line_no,
                    end_line=line_no,
                    parameters=raw_params,
                    visibility="public",
                    source_reference=f"{f_name}(...)",
                )
            )

        # 4. Diagnostics: Unsafe C buffer and string functions
        unsafe_funcs = [
            ("gets", "SEC-C-GETS", "error", "Usage of gets() is inherently unsafe and leads to buffer overflows. Use fgets()."),
            ("strcpy", "SEC-C-STRCPY", "warning", "strcpy() does not check buffer boundaries. Consider strncpy() or strlcpy()."),
            ("strcat", "SEC-C-STRCAT", "warning", "strcat() does not check destination buffer boundaries. Consider strncat()."),
            ("sprintf", "SEC-C-SPRINTF", "warning", "sprintf() is vulnerable to buffer overflows. Use snprintf()."),
        ]

        for func_name, rule_id, sev, msg in unsafe_funcs:
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
                        tool_name="c-security-checker",
                        evidence=match.group(0).strip(),
                        suggested_remediation="Replace with bounded-buffer equivalent.",
                    )
                )

        branch_count = len(re.findall(r"""\b(?:if|else\s+if|case|for|while|catch)\b|\?|&&|\|\|""", content))
        complexity = float(1 + branch_count)

        func_count = sum(1 for s in symbols if s.symbol_type == "function")
        class_count = sum(1 for s in symbols if s.symbol_type in ("class", "struct"))

        metrics = CodeMetrics(
            total_lines=total_lines,
            code_lines=code_lines_count,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=func_count,
            class_count=class_count,
            import_count=len(imports),
            avg_function_length=round(float(code_lines_count / max(1, func_count)), 1) if func_count else 0.0,
            cyclomatic_complexity=round(complexity, 1),
            nesting_depth=2,
        )

        return symbols, imports, dependencies, metrics, diagnostics, syntax_validation
