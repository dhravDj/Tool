"""Rust source code parser and structural extractor."""

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


class RustParser(BaseLanguageParser):
    """Parser for Rust source files extracting modules, uses, structs, enums, traits, and functions."""

    @property
    def language(self) -> str:
        return "rs"

    @property
    def supported_extensions(self) -> list[str]:
        return ["rs"]

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
        syntax_validation = SyntaxValidationResult(parser_used="rust-parser")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith(("//", "/*", "*")))
        code_lines_count = total_lines - blank_lines - comment_lines

        # 1. Use declarations
        use_pattern = re.compile(r"""(?:pub\s+)?use\s+([A-Za-z0-9_:]+(?:\{[^}]+\})?);""")
        for match in use_pattern.finditer(content):
            use_path = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            root_crate = use_path.split("::")[0]
            is_internal = root_crate in ("crate", "super", "self")
            is_std = root_crate in ("std", "core", "alloc")
            is_ext = not is_internal and not is_std

            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=use_path,
                    imported_symbols=[use_path.split("::")[-1]],
                    is_relative=is_internal,
                    is_external=is_ext,
                    line_number=line_no,
                )
            )
            if is_ext and root_crate not in [d.name for d in dependencies]:
                dependencies.append(CodeDependency(name=root_crate, dependency_type="external_crate"))

        # 2. Structs, Enums, Traits
        item_pattern = re.compile(r"""(?:pub(?:\([^)]+\))?\s+)?(struct|enum|trait)\s+(\w+)""")
        for match in item_pattern.finditer(content):
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
                    visibility="public" if "pub" in match.group(0) else "private",
                    source_reference=match.group(0).strip(),
                )
            )

        # 3. Functions
        func_pattern = re.compile(
            r"""(?:pub(?:\([^)]+\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)"""
        )
        for match in func_pattern.finditer(content):
            f_name = match.group(1)
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
                    visibility="public" if "pub" in match.group(0) else "private",
                    source_reference=f"fn {f_name}(...)",
                )
            )

        # 4. Diagnostics: unsafe blocks & unwrap()
        for match in re.finditer(r"""\bunsafe\s*\{""", content):
            line_no = content[: match.start()].count("\n") + 1
            diagnostics.append(
                CodeDiagnostic(
                    diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                    rule_id="RUST-UNSAFE-BLOCK",
                    severity="warning",
                    message="Unsafe block detected. Requires manual memory safety audit.",
                    file_path=filename,
                    start_line=line_no,
                    end_line=line_no,
                    column=1,
                    tool_name="rust-security-scanner",
                    suggested_remediation="Verify invariants or encapsulate in safe abstraction.",
                )
            )

        if ".unwrap()" in content:
            diagnostics.append(
                CodeDiagnostic(
                    diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                    rule_id="RUST-UNWRAP-CALL",
                    severity="info",
                    message="Direct call to .unwrap() may cause panic on None or Err values.",
                    file_path=filename,
                    start_line=1,
                    end_line=1,
                    column=1,
                    tool_name="rust-analyzer",
                    suggested_remediation="Use ? operator, match, or unwrap_or_default() for robust error handling.",
                )
            )

        func_count = sum(1 for s in symbols if s.symbol_type == "function")
        class_count = sum(1 for s in symbols if s.symbol_type in ("struct", "enum", "trait"))
        branch_count = len(re.findall(r"""\b(?:if|match|for|while|loop)\b|&&|\|\|""", content))

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
