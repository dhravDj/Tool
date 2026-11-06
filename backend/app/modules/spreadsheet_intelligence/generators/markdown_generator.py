"""Human-readable Markdown report generator for SpreadsheetDocument."""

from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    SpreadsheetDocument,
)


class SpreadsheetMarkdownGenerator:
    """Renders rich markdown overview, table previews, and profiling findings."""

    @staticmethod
    def generate(doc: SpreadsheetDocument, max_preview_rows: int = 10) -> str:
        lines: list[str] = []

        # 1. Header
        meta = doc.workbook_metadata
        lines.append(f"# Spreadsheet Intelligence Report: {meta.filename}")
        lines.append("")
        lines.append("## 1. Workbook Overview")
        lines.append("")
        lines.append("| Property | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| **Filename** | `{meta.filename}` |")
        lines.append(f"| **Format** | `{meta.format.upper()}` |")
        lines.append(f"| **Worksheets** | {len(doc.worksheets)} |")
        if meta.creator:
            lines.append(f"| **Author / Creator** | {meta.creator} |")
        if meta.created_at:
            lines.append(f"| **Created** | {meta.created_at} |")
        if meta.modified_at:
            lines.append(f"| **Modified** | {meta.modified_at} |")
        lines.append("")

        # 2. Worksheet Summaries
        lines.append("## 2. Worksheet Catalog")
        lines.append("")
        lines.append("| # | Sheet Name | Visibility | Dimensions | Total Rows | Total Cols | Tables | Charts |")
        lines.append("| :-: | :--- | :--- | :--- | :-: | :-: | :-: | :-: |")

        total_formulas = 0
        for ws in doc.worksheets:
            vis_badge = ws.visibility.value.upper()
            lines.append(
                f"| {ws.position} | **{ws.name}** | `{vis_badge}` | `{ws.dimensions or 'N/A'}` | "
                f"{ws.total_rows:,} | {ws.total_columns:,} | {len(ws.tables)} | {len(ws.charts)} |"
            )
            # Count formulas
            for r in ws.rows:
                total_formulas += sum(1 for c in r.cells if c.formula)

        lines.append("")
        lines.append(f"**Total Formulas Detected Across Workbook:** {total_formulas}")
        lines.append("")

        # 3. Sheet Previews & Profiling
        for ws in doc.worksheets:
            lines.append(f"### Worksheet: {ws.name} ({ws.visibility.value})")
            lines.append("")

            # Tables preview
            if ws.rows:
                lines.append(f"**Table Data Preview (first {min(max_preview_rows, len(ws.rows))} rows):**")
                lines.append("")

                preview_rows = ws.rows[:max_preview_rows]
                max_col = max((max((c.column for c in r.cells), default=0) for r in preview_rows), default=1)
                max_col = min(max_col, 15)  # Cap markdown table at 15 columns for readability

                headers = [ws.columns[i].name or f"Col {i+1}" for i in range(min(len(ws.columns), max_col))]
                if not headers:
                    headers = [f"Col {i+1}" for i in range(max_col)]

                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join([":---"] * len(headers)) + " |")

                for r in preview_rows:
                    cells_map = {c.column: c for c in r.cells}
                    row_vals = []
                    for c_idx in range(1, len(headers) + 1):
                        cell = cells_map.get(c_idx)
                        if cell:
                            val_str = str(cell.formatted_value if cell.formatted_value is not None else cell.raw_value or "")
                            clean_str = val_str.replace("\n", " ").replace("|", "\\|")[:40]
                            row_vals.append(clean_str)
                        else:
                            row_vals.append("")
                    lines.append("| " + " | ".join(row_vals) + " |")

                lines.append("")

            # Data Profiling insights
            if ws.profiling:
                prof = ws.profiling
                lines.append("**Data Quality & Profiling:**")
                lines.append("")
                lines.append(f"- **Populated Cells:** {prof.populated_cells:,}")
                lines.append(f"- **Empty Rows:** {prof.empty_rows_count:,}")
                lines.append(f"- **Duplicate Rows:** {prof.duplicate_rows_count:,}")
                if prof.candidate_primary_keys:
                    pks = ", ".join(f"`{k}`" for k in prof.candidate_primary_keys)
                    lines.append(f"- **Candidate Primary Keys (100% unique & non-null):** {pks}")
                lines.append("")

                lines.append("| Column | Inferred Type | Nulls | Unique | Min | Max | Mean | Std Dev |")
                lines.append("| :--- | :--- | :-: | :-: | :--- | :--- | :-: | :-: |")
                for cp in prof.column_profiles[:15]:
                    min_s = str(cp.min_value)[:20] if cp.min_value is not None else "-"
                    max_s = str(cp.max_value)[:20] if cp.max_value is not None else "-"
                    mean_s = f"{cp.mean:.2f}" if cp.mean is not None else "-"
                    std_s = f"{cp.std_dev:.2f}" if cp.std_dev is not None else "-"
                    lines.append(
                        f"| **{cp.column_name}** | `{cp.inferred_type}` | {cp.null_count} | "
                        f"{cp.unique_count} | {min_s} | {max_s} | {mean_s} | {std_s} |"
                    )
                lines.append("")

            # Formulas in sheet
            sheet_formulas = []
            for r in ws.rows:
                for c in r.cells:
                    if c.formula:
                        sheet_formulas.append((c.address, c.formula, c.cached_value))

            if sheet_formulas:
                lines.append(f"**Formulas in {ws.name} ({len(sheet_formulas)} total):**")
                lines.append("")
                lines.append("| Cell | Formula | Cached Value |")
                lines.append("| :-: | :--- | :--- |")
                for addr, formula, cached in sheet_formulas[:15]:
                    lines.append(f"| `{addr}` | `{formula}` | `{cached if cached is not None else 'N/A'}` |")
                if len(sheet_formulas) > 15:
                    lines.append(f"*... and {len(sheet_formulas) - 15} additional formulas.*")
                lines.append("")

        if doc.warnings:
            lines.append("## 3. Extraction Warnings")
            lines.append("")
            for w in doc.warnings:
                lines.append(f"- ⚠️ {w}")
            lines.append("")

        return "\n".join(lines)
