"""Markdown writer for universal content extraction (Mode B)."""

import re

from app.modules.converters.schemas import UniversalContent, UniversalTable


class MarkdownWriter:
    """Converts UniversalContent into clean GitHub Flavored Markdown."""

    @classmethod
    def write(cls, content: UniversalContent) -> str:
        lines: list[str] = []

        # YAML Frontmatter if metadata exists
        if content.metadata or content.author:
            lines.append("---")
            if content.title:
                lines.append(f'title: "{cls._escape_yaml(content.title)}"')
            if content.author:
                lines.append(f'author: "{cls._escape_yaml(content.author)}"')
            lines.append(f'source_file: "{cls._escape_yaml(content.source_filename)}"')
            lines.append(f'source_format: "{content.source_format}"')
            if content.page_count > 1:
                lines.append(f"page_count: {content.page_count}")
            lines.append("---")
            lines.append("")

        # Document Header
        if content.title:
            lines.append(f"# {content.title}\n")

        # Media transcripts
        if content.transcript_segments:
            lines.append("## Transcript\n")
            for seg in content.transcript_segments:
                start_m, start_s = divmod(int(seg.start_seconds), 60)
                time_str = f"`{start_m:02d}:{start_s:02d}`"
                speaker = f"**{seg.speaker}**: " if seg.speaker else ""
                lines.append(f"- {time_str} {speaker}{seg.text}")
            lines.append("")

        # Sections
        if content.sections:
            for sec in content.sections:
                lvl = max(1, min(6, sec.level))
                prefix = "#" * lvl
                if sec.page_or_slide_number:
                    lines.append(f"{prefix} {sec.title} *(# {sec.page_or_slide_number})*\n")
                else:
                    lines.append(f"{prefix} {sec.title}\n")

                if sec.content:
                    lines.append(f"{sec.content.strip()}\n")

        # Paragraphs (if no sections present)
        elif content.paragraphs:
            for p in content.paragraphs:
                p_clean = p.strip()
                if p_clean:
                    lines.append(f"{p_clean}\n")

        # Code blocks
        if content.code_blocks:
            for cb in content.code_blocks:
                lang = cb.language.lower().strip() or ""
                if cb.caption:
                    lines.append(f"**{cb.caption}**\n")
                lines.append(f"```{lang}\n{cb.code.strip()}\n```\n")

        # Tables
        if content.tables:
            for tbl in content.tables:
                table_md = cls._render_table(tbl)
                if table_md:
                    lines.append(table_md)
                    lines.append("")

        # Fallback to raw text
        if not lines and content.raw_text:
            return content.raw_text.strip() + "\n"

        return "\n".join(lines).strip() + "\n"

    @classmethod
    def _render_table(cls, tbl: UniversalTable) -> str:
        """Render a UniversalTable into GitHub Flavored Markdown table format."""
        if not tbl.rows and not tbl.headers:
            return ""

        lines: list[str] = []
        name = tbl.title or tbl.sheet_name
        if name:
            lines.append(f"### Table: {name}\n")

        # Normalize headers and rows
        col_count = len(tbl.headers) if tbl.headers else 0
        if tbl.rows:
            col_count = max(col_count, max(len(r) for r in tbl.rows))

        if col_count == 0:
            return ""

        headers = list(tbl.headers) if tbl.headers else [f"Col {i+1}" for i in range(col_count)]
        while len(headers) < col_count:
            headers.append(f"Col {len(headers)+1}")

        # Header row
        header_cells = [cls._escape_cell(str(h)) for h in headers]
        lines.append("| " + " | ".join(header_cells) + " |")

        # Separator row
        lines.append("| " + " | ".join(["---"] * col_count) + " |")

        # Data rows
        for row in tbl.rows:
            row_cells: list[str] = []
            for i in range(col_count):
                val = row[i] if i < len(row) else ""
                row_cells.append(cls._escape_cell(str(val) if val is not None else ""))
            lines.append("| " + " | ".join(row_cells) + " |")

        return "\n".join(lines)

    @staticmethod
    def _escape_cell(cell: str) -> str:
        clean = cell.replace("\n", " ").replace("\r", " ").replace("|", "\\|").strip()
        return clean

    @staticmethod
    def _escape_yaml(val: str) -> str:
        return re.sub(r'["\\]', r"\\\g<0>", val)
