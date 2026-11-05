"""Markdown visual intelligence report generator."""

from app.modules.image_intelligence.schemas.image_document import ImageDocument, RegionType


class ImageMarkdownGenerator:
    """Generates human-readable GitHub Flavored Markdown (GFM) reports from ImageDocument."""

    @staticmethod
    def generate(doc: ImageDocument) -> str:
        """Construct detailed Markdown report."""
        meta = doc.metadata
        analysis = doc.analysis
        lines: list[str] = []

        # Title & Overview
        lines.append(f"# Visual Intelligence Report: `{doc.filename}`\n")
        lines.append(f"**Image ID:** `{doc.image_id}`  ")
        lines.append(f"**Analyzed At:** `{doc.created_at}`  ")
        lines.append(f"**Format:** `{meta.format.upper()}` | **Dimensions:** `{meta.width} × {meta.height}` ({meta.aspect_ratio}:1) | **Color:** `{meta.color_mode}` ({meta.bit_depth}-bit)\n")

        # Visual Scene Summary
        lines.append("## 1. Visual Scene Summary\n")
        lines.append(f"> {analysis.caption}\n")
        lines.append(f"- **Scene Classification:** `{analysis.scene_type}`")
        if analysis.dominant_colors:
            colors_formatted = " ".join([f"`{c}`" for c in analysis.dominant_colors])
            lines.append(f"- **Dominant Palette:** {colors_formatted}")
        lines.append("")

        # Visual Objects & Regions
        lines.append("## 2. Detected Visual Regions\n")
        object_regions = [r for r in doc.regions if r.region_type in (RegionType.OBJECT, RegionType.FACE)]
        if object_regions:
            lines.append("| Region ID | Label | Bounding Box [ymin, xmin, ymax, xmax] | Confidence | Provenance |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for r in object_regions[:15]:
                bbox_str = f"[{r.bounding_box[0]:.2f}, {r.bounding_box[1]:.2f}, {r.bounding_box[2]:.2f}, {r.bounding_box[3]:.2f}]"
                lines.append(f"| `{r.region_id}` | **{r.label}** | `{bbox_str}` | {r.confidence * 100:.1f}% | `{r.provenance}` |")
            lines.append("")
        else:
            lines.append("_No discrete foreground objects isolated._\n")

        # Diagram Analysis
        if analysis.diagram.is_diagram:
            lines.append("## 3. Technical Diagram & Flowchart Analysis\n")
            diag = analysis.diagram
            lines.append(f"- **Diagram Type:** `{diag.diagram_type}` (Confidence: {diag.confidence * 100:.1f}%)")
            lines.append(f"- **Flow Direction:** `{diag.flow_direction}`")
            lines.append(f"- **Total Nodes:** {len(diag.nodes)} | **Connectors:** {diag.connectors_count}\n")
            if diag.nodes:
                lines.append("### Identified Nodes")
                for n in diag.nodes[:10]:
                    lines.append(f"- **{n.get('node_id')}**: {n.get('label')}")
                lines.append("")

        # Chart Analysis
        if analysis.chart.is_chart:
            lines.append("## 4. Statistical Chart & Data Analysis\n")
            ch = analysis.chart
            lines.append(f"- **Chart Type:** `{ch.chart_type}` (Confidence: {ch.confidence * 100:.1f}%)")
            if ch.title:
                lines.append(f"- **Chart Title:** **{ch.title}**")
            if ch.x_axis_label:
                lines.append(f"- **X-Axis:** `{ch.x_axis_label}` | **Y-Axis:** `{ch.y_axis_label}`")
            if ch.series_data:
                lines.append("\n### Data Series Points")
                lines.append("| Series / Item | Value | Unit |")
                lines.append("| :--- | :--- | :--- |")
                for s in ch.series_data[:12]:
                    lines.append(f"| {s.get('label')} | **{s.get('value')}** | {s.get('unit', '-')} |")
            lines.append("")

        # OCR Text Layer
        lines.append("## 5. Optical Character Recognition (OCR)\n")
        lines.append(f"- **Word Count:** {analysis.ocr_word_count} words")
        lines.append(f"- **Average Confidence:** {analysis.ocr_average_confidence * 100:.1f}%\n")
        if analysis.ocr_full_text.strip():
            lines.append("```text")
            lines.append(analysis.ocr_full_text.strip())
            lines.append("```\n")
        else:
            lines.append("_No text recognized in this image._\n")

        # Technical Metadata & Privacy
        lines.append("## 6. Technical & Privacy Metadata\n")
        lines.append(f"- **File Size:** {meta.file_size:,} bytes")
        lines.append(f"- **DPI:** {meta.dpi or 'Default (72x72)'}")
        lines.append(f"- **Transparency:** `{'Yes' if meta.has_transparency else 'No'}`")
        lines.append(f"- **Animated:** `{'Yes (' + str(meta.frame_count) + ' frames)' if meta.is_animated else 'No'}`")
        lines.append(f"- **GPS Privacy Scrubbing:** `{'ACTIVE (GPS data redacted)' if meta.gps_redacted else 'None'}`")

        if meta.exif_scrubbed:
            lines.append("\n### Safe EXIF Tags")
            for k, v in meta.exif_scrubbed.items():
                lines.append(f"- **{k}:** `{v}`")
        lines.append("")

        # Warnings
        if doc.warnings:
            lines.append("## ⚠️ Pipeline Warnings\n")
            for w in doc.warnings:
                lines.append(f"- {w}")
            lines.append("")

        return "\n".join(lines)
