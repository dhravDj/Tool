"""Markdown generator for Presentation Intelligence documents.

Preserves slide boundaries, titles, bullet nesting, tables, charts, and separate speaker notes.
"""

from app.modules.presentation_intelligence.schemas.presentation_document import (
    ElementType,
    PresentationDocument,
)


class PresentationMarkdownGenerator:
    """Generates structured, clean Markdown representation of a presentation."""

    @classmethod
    def generate(cls, doc: PresentationDocument) -> str:
        """Convert PresentationDocument into rich hierarchical Markdown."""
        lines: list[str] = []

        # 1. Presentation Title & Metadata Header
        pres_title = doc.metadata.title or "Untitled Presentation"
        lines.append(f"# {pres_title}")
        lines.append("")

        meta_info: list[str] = []
        if doc.metadata.author:
            meta_info.append(f"**Author:** {doc.metadata.author}")
        if doc.metadata.created_at:
            meta_info.append(f"**Date:** {doc.metadata.created_at[:10]}")
        meta_info.append(f"**Total Slides:** {doc.slide_count}")
        if doc.metadata.hidden_slide_count > 0:
            meta_info.append(f"**Hidden Slides:** {doc.metadata.hidden_slide_count}")
        lines.append(" | ".join(meta_info))
        lines.append("")
        lines.append("---")
        lines.append("")

        # 2. Iterate Slides
        for slide in doc.slides:
            slide_header = f"## Slide {slide.slide_number}: {slide.title or 'Untitled Slide'}"
            if slide.hidden:
                slide_header += " *(Hidden)*"
            lines.append(slide_header)
            lines.append("")

            # Find matching charts and tables for this slide
            slide_tables = [t for t in doc.tables if t.slide_id == slide.slide_id or t.slide_number == slide.slide_number]
            slide_charts = [c for c in doc.charts if c.slide_id == slide.slide_id or c.slide_number == slide.slide_number]
            slide_diagrams = [d for d in doc.diagrams if d.slide_id == slide.slide_id or d.slide_number == slide.slide_number]

            # Visible elements
            for elem in slide.elements:
                if elem.element_type == ElementType.TITLE:
                    # Already in slide header or print subtitle if distinct
                    if elem.text and elem.text.strip() != (slide.title or "").strip():
                        lines.append(f"### {elem.text.strip()}")
                        lines.append("")

                elif elem.element_type == ElementType.TEXT:
                    if elem.paragraphs:
                        for p in elem.paragraphs:
                            indent = "  " * p.level
                            prefix = "* " if p.bullet or p.level > 0 else ""
                            lines.append(f"{indent}{prefix}{p.text.strip()}")
                        lines.append("")
                    elif elem.text:
                        lines.append(elem.text.strip())
                        lines.append("")

                elif elem.element_type == ElementType.IMAGE:
                    alt = elem.text.replace("[Image: ", "").rstrip("]") if elem.text else "Image"
                    asset_ref = elem.asset_reference or "embedded_image"
                    lines.append(f"![{alt}]({asset_ref})")
                    lines.append("")

            # Tables
            for tbl in slide_tables:
                lines.append("### Table")
                lines.append("")
                if tbl.headers:
                    lines.append("| " + " | ".join(h.replace("\n", " ") for h in tbl.headers) + " |")
                    lines.append("| " + " | ".join("---" for _ in tbl.headers) + " |")
                    # data rows (skip header row if row 0 was used)
                    data_rows = tbl.rows[1:] if tbl.has_header and len(tbl.rows) > 1 else tbl.rows
                    for row in data_rows:
                        row_vals = [cell.text.replace("\n", " ").replace("|", "\\|") for cell in row]
                        lines.append("| " + " | ".join(row_vals) + " |")
                elif tbl.rows:
                    first_row = tbl.rows[0]
                    lines.append("| " + " | ".join(f"Col {idx + 1}" for idx in range(len(first_row))) + " |")
                    lines.append("| " + " | ".join("---" for _ in first_row) + " |")
                    for row in tbl.rows:
                        row_vals = [cell.text.replace("\n", " ").replace("|", "\\|") for cell in row]
                        lines.append("| " + " | ".join(row_vals) + " |")
                lines.append("")

            # Charts
            for ch in slide_charts:
                lines.append(f"### Chart: {ch.chart_type.value.capitalize()}{(' - ' + ch.title) if ch.title else ''}")
                lines.append("")
                if ch.categories and ch.series:
                    # Render series data table
                    hdr = ["Category"] + [s.name for s in ch.series]
                    lines.append("| " + " | ".join(hdr) + " |")
                    lines.append("| " + " | ".join("---" for _ in hdr) + " |")
                    for cat_idx, cat in enumerate(ch.categories):
                        row_vals = [cat]
                        for s in ch.series:
                            val_str = str(s.values[cat_idx]) if cat_idx < len(s.values) and s.values[cat_idx] is not None else ""
                            row_vals.append(val_str)
                        lines.append("| " + " | ".join(row_vals) + " |")
                elif ch.series:
                    for s in ch.series:
                        lines.append(f"- **{s.name}**: {', '.join(str(v) for v in s.values if v is not None)}")
                lines.append("")

            # Diagrams
            for diag in slide_diagrams:
                lines.append("### Diagram Structure")
                lines.append("")
                if diag.nodes:
                    lines.append("**Nodes:**")
                    for n in diag.nodes:
                        lines.append(f"- `[{n.node_id}]` {n.label} ({n.shape_type})")
                if diag.edges:
                    lines.append("**Connections:**")
                    for e in diag.edges:
                        lines.append(f"- {e.source_id} -> {e.target_id}{f' ({e.label})' if e.label else ''}")
                lines.append("")

            # Speaker Notes (Distinct section)
            if slide.speaker_notes and slide.speaker_notes.strip():
                lines.append("### Speaker Notes")
                lines.append("")
                lines.append(slide.speaker_notes.strip())
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines).strip() + "\n"
