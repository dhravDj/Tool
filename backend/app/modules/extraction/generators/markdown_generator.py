"""Markdown output generator converting CanonicalDocument to clean Markdown."""

from app.domain.enums import BlockType
from app.domain.schemas.canonical_document import CanonicalBlock, CanonicalDocument


class MarkdownGenerator:
    """Converts a CanonicalDocument into clean, readable GitHub Flavored Markdown."""

    @classmethod
    def generate(cls, document: CanonicalDocument, include_page_markers: bool = True) -> str:
        lines: list[str] = []

        # Document Header metadata comment if title or author is present
        title = document.metadata.get("title")
        author = document.metadata.get("author")
        if title:
            lines.append(f"# {title}\n")
            if author:
                lines.append(f"*Author: {author}*\n")
            lines.append("")

        current_page = 0

        for block in document.blocks:
            # Page transition marker
            if include_page_markers and block.page_number != current_page and document.page_count > 1:
                current_page = block.page_number
                lines.append(f"\n<!-- Page {current_page} -->\n")

            rendered = cls._render_block(block)
            if rendered:
                lines.append(rendered)

        return "\n".join(lines).strip() + "\n"

    @classmethod
    def _render_block(cls, block: CanonicalBlock) -> str:
        text = block.text.strip()
        b_type = block.block_type

        if b_type == BlockType.HEADING:
            level = int(block.metadata.get("heading_level", 2))
            level = max(1, min(6, level))
            return f"{'#' * level} {text}\n"

        elif b_type == BlockType.PARAGRAPH:
            return f"{text}\n"

        elif b_type == BlockType.LIST_ITEM:
            prefix = block.metadata.get("list_prefix", "- ")
            return f"{prefix}{text}"

        elif b_type == BlockType.LIST:
            return f"{text}\n"

        elif b_type == BlockType.CODE:
            lang = block.metadata.get("language", "")
            return f"```{lang}\n{text}\n```\n"

        elif b_type == BlockType.TABLE:
            # If grid is provided in metadata, format as GFM table
            grid = block.metadata.get("grid")
            if grid and isinstance(grid, list) and len(grid) > 0:
                return cls._render_table_grid(grid)
            return f"\n{text}\n"

        elif b_type == BlockType.IMAGE_REFERENCE:
            caption = text or block.metadata.get("caption", "Extracted image")
            asset_path = block.metadata.get("asset_path", "")
            return f"![{caption}]({asset_path})\n"

        elif b_type == BlockType.HEADER:
            return f"> *[Header]* {text}\n"

        elif b_type == BlockType.FOOTER:
            return f"> *[Footer]* {text}\n"

        elif b_type == BlockType.EQUATION:
            return f"$$\n{text}\n$$\n"

        elif b_type == BlockType.CAPTION:
            return f"*{text}*\n"

        else:
            # Unknown or other block types
            return f"{text}\n" if text else ""

    @staticmethod
    def _render_table_grid(grid: list[list[str]]) -> str:
        """Render 2D string matrix into Markdown table."""
        if not grid:
            return ""

        col_count = max(len(row) for row in grid)
        # Normalize row lengths
        normalized = [row + [""] * (col_count - len(row)) for row in grid]

        table_lines = []
        # Header row
        header = [cell.replace("\n", " ").strip() for cell in normalized[0]]
        table_lines.append("| " + " | ".join(header) + " |")
        table_lines.append("| " + " | ".join(["---"] * col_count) + " |")

        # Data rows
        for row in normalized[1:]:
            cells = [cell.replace("\n", " ").strip() for cell in row]
            table_lines.append("| " + " | ".join(cells) + " |")

        return "\n" + "\n".join(table_lines) + "\n"
