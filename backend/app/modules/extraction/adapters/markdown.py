"""Markdown Document Extraction Adapter preserving structured markdown semantics."""

import asyncio
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.domain.enums import BlockType, ExtractionStatus
from app.domain.schemas.canonical_document import (
    CanonicalBlock,
    CanonicalDocument,
    CanonicalPage,
)
from app.modules.extraction.adapters.base import (
    BaseDocumentExtractor,
    CorruptedDocumentError,
)


class MarkdownExtractor(BaseDocumentExtractor):
    """Structured extraction adapter for Markdown documents with frontmatter parsing."""

    engine_name = "markdown_extractor"
    version = "1.0.0"
    supported_formats = ["md"]

    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract structured blocks and frontmatter metadata from Markdown."""
        return await asyncio.to_thread(
            self._extract_sync,
            file_path,
            original_filename or file_path.name,
            options or {},
        )

    def _extract_sync(
        self,
        file_path: Path,
        original_filename: str,
        options: dict[str, Any],
    ) -> CanonicalDocument:
        doc_id = options.get("document_id") or uuid.uuid4().hex

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise CorruptedDocumentError(f"Failed to read markdown file: {exc}") from exc

        metadata: dict[str, Any] = {}
        body = content

        # 1. Parse YAML Frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_raw = parts[1]
                body = parts[2]
                try:
                    parsed_yaml = yaml.safe_load(frontmatter_raw)
                    if isinstance(parsed_yaml, dict):
                        metadata.update(parsed_yaml)
                except Exception:
                    pass  # Ignore invalid frontmatter and proceed

        # 2. Parse Markdown Blocks
        blocks: list[CanonicalBlock] = []
        lines = body.replace("\r\n", "\n").split("\n")
        idx = 0
        n = len(lines)
        global_reading_order = 0

        while idx < n:
            line = lines[idx]
            stripped = line.strip()

            # Empty lines
            if not stripped:
                idx += 1
                continue

            # Code fence (```)
            if stripped.startswith("```"):
                fence_lang = stripped[3:].strip()
                code_lines = []
                idx += 1
                while idx < n and not lines[idx].strip().startswith("```"):
                    code_lines.append(lines[idx])
                    idx += 1
                if idx < n:
                    idx += 1  # Consume closing fence

                code_text = "\n".join(code_lines)
                block = CanonicalBlock(
                    block_id=self._generate_block_id(1, len(blocks)),
                    block_type=BlockType.CODE,
                    text=code_text,
                    reading_order=global_reading_order,
                    page_number=1,
                    confidence=1.0,
                    extraction_engine=self.engine_name,
                    provenance="native",
                    metadata={"language": fence_lang},
                )
                blocks.append(block)
                global_reading_order += 1
                continue

            # Headings (# H1, ## H2, etc.)
            heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                htext = heading_match.group(2).strip()
                block = CanonicalBlock(
                    block_id=self._generate_block_id(1, len(blocks)),
                    block_type=BlockType.HEADING,
                    text=htext,
                    reading_order=global_reading_order,
                    page_number=1,
                    confidence=1.0,
                    extraction_engine=self.engine_name,
                    provenance="native",
                    metadata={"heading_level": level},
                )
                blocks.append(block)
                global_reading_order += 1
                idx += 1
                continue

            # Table block (| Header 1 | Header 2 |)
            if stripped.startswith("|") and stripped.endswith("|"):
                table_lines = [stripped]
                idx += 1
                while (
                    idx < n
                    and lines[idx].strip().startswith("|")
                    and lines[idx].strip().endswith("|")
                ):
                    table_lines.append(lines[idx].strip())
                    idx += 1

                grid = []
                for tline in table_lines:
                    # Skip separator line |---|---|
                    if re.match(r"^\|(\s*:?-+:?\s*\|)+$", tline):
                        continue
                    cols = [c.strip() for c in tline.split("|")[1:-1]]
                    grid.append(cols)

                block = CanonicalBlock(
                    block_id=self._generate_block_id(1, len(blocks)),
                    block_type=BlockType.TABLE,
                    text="\n".join(table_lines),
                    reading_order=global_reading_order,
                    page_number=1,
                    confidence=1.0,
                    extraction_engine=self.engine_name,
                    provenance="native_table",
                    metadata={"table_grid": grid, "row_count": len(grid)},
                )
                blocks.append(block)
                global_reading_order += 1
                continue

            # List Item (- bullet, * bullet, 1. number)
            list_match = re.match(r"^(\*|-|\+|\d+\.)\s+(.*)$", stripped)
            if list_match:
                prefix = list_match.group(1)
                ltext = list_match.group(2).strip()
                is_num = prefix[0].isdigit()
                block = CanonicalBlock(
                    block_id=self._generate_block_id(1, len(blocks)),
                    block_type=BlockType.LIST_ITEM,
                    text=ltext,
                    reading_order=global_reading_order,
                    page_number=1,
                    confidence=1.0,
                    extraction_engine=self.engine_name,
                    provenance="native",
                    metadata={"list_type": "number" if is_num else "bullet", "marker": prefix},
                )
                blocks.append(block)
                global_reading_order += 1
                idx += 1
                continue

            # Regular Paragraph (consume contiguous lines)
            para_lines = [line]
            idx += 1
            while idx < n:
                next_line = lines[idx]
                next_s = next_line.strip()
                if (
                    not next_s
                    or next_s.startswith(("#", "```", "|", "* ", "- ", "+ "))
                    or re.match(r"^\d+\.\s+", next_s)
                ):
                    break
                para_lines.append(next_line)
                idx += 1

            p_text = "\n".join(para_lines).strip()
            if p_text:
                block = CanonicalBlock(
                    block_id=self._generate_block_id(1, len(blocks)),
                    block_type=BlockType.PARAGRAPH,
                    text=p_text,
                    reading_order=global_reading_order,
                    page_number=1,
                    confidence=1.0,
                    extraction_engine=self.engine_name,
                    provenance="native",
                )
                blocks.append(block)
                global_reading_order += 1

        page = CanonicalPage(
            page_number=1,
            is_scanned=False,
            ocr_applied=False,
            blocks=blocks,
            metadata={"block_count": len(blocks)},
        )

        metadata.update(
            {
                "char_count": len(body),
                "word_count": len(body.split()),
                "line_count": len(lines),
            }
        )

        return CanonicalDocument(
            document_id=doc_id,
            original_filename=original_filename,
            detected_format="md",
            extraction_status=ExtractionStatus.COMPLETED,
            metadata=metadata,
            page_count=1,
            extraction_engine=self.engine_name,
            extraction_version=self.version,
            created_at=datetime.now(UTC).isoformat(),
            pages=[page],
            blocks=blocks,
            warnings=[],
            errors=[],
        )
