"""Markdown report generator for Structured Data Intelligence documents."""

from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    StructuredDataDocument,
)


class StructuredMarkdownGenerator:
    """Generates an executive technical markdown report for analyzed structured datasets."""

    def generate(self, doc: StructuredDataDocument) -> str:
        md: list[str] = [
            f"# Structured Data Intelligence Report — `{doc.format.upper()}` Dataset",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Format:** `{doc.format.upper()}`",
            f"- **Root Structure:** `{doc.root_type}`",
            f"- **Records / Rows:** {doc.data_profile.total_rows}",
            f"- **Fields / Columns:** {doc.data_profile.total_columns}",
            f"- **Validation Status:** `{'✓ Valid' if doc.validation_results.is_valid else '✗ Validation Warnings/Errors'}`",
            f"- **Candidate Keys:** {', '.join([f'`{k}`' for k in doc.data_profile.candidate_keys]) if doc.data_profile.candidate_keys else 'None'}",
            f"- **Missing Cells Ratio:** `{doc.data_profile.missing_cells_ratio * 100:.1f}%`",
            "",
            "---",
            "",
            "## 2. Column & Field Profiles",
            "",
        ]

        if not doc.data_profile.column_profiles:
            md.append("*No columnar data or leaf properties profiled.*")
            md.append("")
        else:
            md.append("| Field Name | Inferred Type | Null % | Unique | Min Value | Max Value |")
            md.append("| :--- | :---: | :---: | :---: | :--- | :--- |")
            for col in doc.data_profile.column_profiles:
                u_badge = "✓ Yes" if col.is_unique else "No"
                min_s = str(col.statistics.min_value)[:20] if col.statistics.min_value is not None else "-"
                max_s = str(col.statistics.max_value)[:20] if col.statistics.max_value is not None else "-"
                md.append(f"| `{col.name}` | `{col.data_type}` | {col.null_percentage:.1f}% | {u_badge} | {min_s} | {max_s} |")
            md.append("")

        md.extend([
            "---",
            "",
            "## 3. Structural Validation & Security Alerts",
            "",
        ])

        if doc.validation_results.duplicate_keys:
            md.append(f"⚠️ **Duplicate Keys Detected:** {', '.join([f'`{k}`' for k in doc.validation_results.duplicate_keys])}")
            md.append("")

        if doc.validation_results.security_warnings:
            for sec in doc.validation_results.security_warnings:
                md.append(f"🛡️ **Security Alert:** {sec}")
            md.append("")

        if not doc.validation_results.duplicate_keys and not doc.validation_results.security_warnings:
            md.append("✓ **Zero duplicate keys, XXE, or security alerts detected.**")
            md.append("")

        return "\n".join(md)
