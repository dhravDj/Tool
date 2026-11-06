"""HTML and CSS web styling and markup parsers."""

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


class HTMLParser(BaseLanguageParser):
    """HTML document structure and embedded resource extractor."""

    @property
    def language(self) -> str:
        return "html"

    @property
    def supported_extensions(self) -> list[str]:
        return ["html", "htm"]

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
        syntax_validation = SyntaxValidationResult(parser_used="html-parser")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith("<!--"))
        code_lines_count = total_lines - blank_lines - comment_lines

        # 1. External scripts and stylesheet links
        script_pattern = re.compile(r"""<script[^>]+src=['"]([^'"]+)['"][^>]*>""", re.IGNORECASE)
        for match in script_pattern.finditer(content):
            src = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            is_ext = src.startswith("http") or src.startswith("//")
            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=src,
                    imported_symbols=["script"],
                    is_relative=not is_ext,
                    is_external=is_ext,
                    line_number=line_no,
                )
            )
            if is_ext:
                dependencies.append(CodeDependency(name=src, dependency_type="cdn_script"))

        link_pattern = re.compile(r"""<link[^>]+href=['"]([^'"]+)['"][^>]*>""", re.IGNORECASE)
        for match in link_pattern.finditer(content):
            href = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            is_ext = href.startswith("http") or href.startswith("//")
            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=href,
                    imported_symbols=["stylesheet"],
                    is_relative=not is_ext,
                    is_external=is_ext,
                    line_number=line_no,
                )
            )

        # 2. Main Landmark Elements
        tag_pattern = re.compile(r"""<(header|main|footer|nav|form|table|section|article)\b[^>]*>""", re.IGNORECASE)
        for match in tag_pattern.finditer(content):
            tag_name = match.group(1)
            line_no = content[: match.start()].count("\n") + 1
            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=tag_name,
                    symbol_type="element",
                    start_line=line_no,
                    end_line=line_no,
                    visibility="public",
                    source_reference=match.group(0).strip(),
                )
            )

        # 3. Security Diagnostics: Inline scripts and insecure HTTP resources
        if "<script>" in content or "<script type=\"text/javascript\">" in content:
            diagnostics.append(
                CodeDiagnostic(
                    diagnostic_id=f"diag_{uuid.uuid4().hex[:8]}",
                    rule_id="HTML-INLINE-SCRIPT",
                    severity="warning",
                    message="Inline <script> block detected. Violates strict Content Security Policy (CSP).",
                    file_path=filename,
                    start_line=1,
                    end_line=1,
                    column=1,
                    tool_name="html-security-checker",
                    suggested_remediation="Move JavaScript logic to external bundled assets.",
                )
            )

        metrics = CodeMetrics(
            total_lines=total_lines,
            code_lines=max(0, code_lines_count),
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=len(symbols),
            class_count=len(imports),
            import_count=len(imports),
            cyclomatic_complexity=1.0,
            nesting_depth=2,
        )

        return symbols, imports, dependencies, metrics, diagnostics, syntax_validation


class CSSParser(BaseLanguageParser):
    """CSS stylesheet structure, media queries, and rules extractor."""

    @property
    def language(self) -> str:
        return "css"

    @property
    def supported_extensions(self) -> list[str]:
        return ["css"]

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
        syntax_validation = SyntaxValidationResult(parser_used="css-parser")

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith("/*"))
        code_lines_count = total_lines - blank_lines - comment_lines

        # 1. @import directives
        import_pattern = re.compile(r"""@import\s+(?:url\(['"]?([^'")]+)['"]?\)|['"]([^'"]+)['"]);""")
        for match in import_pattern.finditer(content):
            target = match.group(1) or match.group(2)
            line_no = content[: match.start()].count("\n") + 1
            is_ext = target.startswith("http") or target.startswith("//")
            imports.append(
                CodeImport(
                    statement=match.group(0).strip(),
                    module_name=target,
                    imported_symbols=["stylesheet"],
                    is_relative=not is_ext,
                    is_external=is_ext,
                    line_number=line_no,
                )
            )

        # 2. Selectors & Media Queries
        rule_pattern = re.compile(r"""([^{}]+)\s*\{([^}]+)\}""")
        for match in rule_pattern.finditer(content):
            selector = match.group(1).strip()
            line_no = content[: match.start()].count("\n") + 1
            if selector.startswith("@media"):
                sym_type = "media_query"
            elif selector.startswith("@keyframes"):
                sym_type = "keyframes"
            else:
                sym_type = "selector"

            symbols.append(
                CodeSymbol(
                    symbol_id=f"sym_{uuid.uuid4().hex[:8]}",
                    name=selector[:60],
                    symbol_type=sym_type,
                    start_line=line_no,
                    end_line=line_no,
                    source_reference=selector[:80],
                )
            )

        metrics = CodeMetrics(
            total_lines=total_lines,
            code_lines=max(0, code_lines_count),
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=len([s for s in symbols if s.symbol_type == "selector"]),
            class_count=len([s for s in symbols if s.symbol_type == "media_query"]),
            import_count=len(imports),
            cyclomatic_complexity=float(1 + len([s for s in symbols if s.symbol_type == "media_query"])),
            nesting_depth=2,
        )

        return symbols, imports, dependencies, metrics, diagnostics, syntax_validation
