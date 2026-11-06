"""Markdown report generator for Code Intelligence documents."""

from app.modules.code_intelligence.schemas.code_document import CodeDocument


class CodeMarkdownGenerator:
    """Generates an executive technical markdown report for analyzed source code."""

    def generate(self, doc: CodeDocument) -> str:
        md: list[str] = [
            f"# Code Intelligence Report — `{doc.file_metadata.get('filename', 'Source Code')}`",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Language:** `{doc.language.upper()}`",
            f"- **Encoding:** `{doc.encoding}`",
            f"- **Total Lines:** {doc.metrics.total_lines} ({doc.metrics.code_lines} code, {doc.metrics.comment_lines} comments, {doc.metrics.blank_lines} blank)",
            f"- **Cyclomatic Complexity:** `{doc.metrics.cyclomatic_complexity}`",
            f"- **Syntax Valid:** `{'✓ Valid' if doc.syntax_validation.is_valid else '✗ Syntax Errors Detected'}`",
            f"- **Symbols Identified:** {len(doc.symbols)} ({doc.metrics.function_count} functions/methods, {doc.metrics.class_count} classes/structs)",
            f"- **External Dependencies:** {len(doc.dependencies)}",
            f"- **Static Diagnostics:** {len(doc.diagnostics)} findings",
            "",
            "---",
            "",
            "## 2. Quantitative Code Metrics",
            "",
            "| Metric | Value |",
            "| :--- | :--- |",
            f"| Total Lines | `{doc.metrics.total_lines}` |",
            f"| Code Lines | `{doc.metrics.code_lines}` |",
            f"| Comment Lines | `{doc.metrics.comment_lines}` |",
            f"| Blank Lines | `{doc.metrics.blank_lines}` |",
            f"| Functions / Methods | `{doc.metrics.function_count}` |",
            f"| Classes / Types / Structs | `{doc.metrics.class_count}` |",
            f"| Average Function Length | `{doc.metrics.avg_function_length} lines` |",
            f"| Maximum Function Length | `{doc.metrics.max_function_length} lines` |",
            f"| Cyclomatic Complexity | `{doc.metrics.cyclomatic_complexity}` |",
            f"| Maximum Nesting Depth | `{doc.metrics.nesting_depth}` |",
            "",
            "---",
            "",
            "## 3. Extracted Symbols & Signatures",
            "",
        ]

        if not doc.symbols:
            md.append("*No top-level functions, classes, or structures identified.*")
            md.append("")
        else:
            md.append("| Symbol | Type | Line | Parameters / Signature | Visibility |")
            md.append("| :--- | :--- | :---: | :--- | :---: |")
            for sym in doc.symbols:
                param_str = ", ".join(sym.parameters) if sym.parameters else "-"
                md.append(f"| `{sym.name}` | `{sym.symbol_type}` | L{sym.start_line} | `{param_str}` | {sym.visibility} |")
            md.append("")

        md.extend([
            "---",
            "",
            "## 4. Imports & External Dependencies",
            "",
        ])

        if not doc.imports:
            md.append("*No import statements or external package dependencies.*")
            md.append("")
        else:
            md.append("| Module / Package | Type | Statement | Line |")
            md.append("| :--- | :---: | :--- | :---: |")
            for imp in doc.imports:
                m_type = "External" if imp.is_external else "Internal/Relative"
                md.append(f"| `{imp.module_name}` | {m_type} | `{imp.statement}` | L{imp.line_number} |")
            md.append("")

        md.extend([
            "---",
            "",
            "## 5. Static Diagnostics & Security Findings",
            "",
        ])

        if not doc.diagnostics:
            md.append("✓ **Zero static analysis warnings or security alerts detected.**")
            md.append("")
        else:
            md.append("| Rule ID | Severity | Line | Message | Remediation |")
            md.append("| :--- | :---: | :---: | :--- | :--- |")
            for diag in doc.diagnostics:
                sev_badge = f"**{diag.severity.upper()}**"
                remed = diag.suggested_remediation or "-"
                md.append(f"| `{diag.rule_id}` | {sev_badge} | L{diag.start_line} | {diag.message} | {remed} |")
            md.append("")

        return "\n".join(md)
