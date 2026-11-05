"""Rich Text Format (RTF) Document Extraction Adapter using striprtf."""

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from striprtf.striprtf import rtf_to_text

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


class RTFExtractor(BaseDocumentExtractor):
    """Extraction adapter for Rich Text Format (.rtf) documents."""

    engine_name = "rtf_extractor"
    version = "1.0.0"
    supported_formats = ["rtf"]

    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract plain text and paragraphs from RTF."""
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
            raw_bytes = file_path.read_bytes()
        except Exception as exc:
            raise CorruptedDocumentError(f"Failed to read RTF file: {exc}") from exc

        # Decode RTF stream with fallback
        rtf_content = ""
        encoding_used = "utf-8"
        for enc in ["utf-8", "cp1252", "latin1"]:
            try:
                rtf_content = raw_bytes.decode(enc)
                encoding_used = enc
                break
            except UnicodeDecodeError:
                continue

        if not rtf_content:
            rtf_content = raw_bytes.decode("utf-8", errors="replace")

        # Strip RTF control words and extract text
        try:
            plain_text = rtf_to_text(rtf_content)
        except Exception as exc:
            raise CorruptedDocumentError(f"Failed to parse RTF structure: {exc}") from exc

        blocks: list[CanonicalBlock] = []
        raw_paragraphs = [p.strip() for p in plain_text.replace("\r\n", "\n").split("\n\n") if p.strip()]

        if not raw_paragraphs and "\n" in plain_text:
            raw_paragraphs = [p.strip() for p in plain_text.split("\n") if p.strip()]

        for idx, text in enumerate(raw_paragraphs):
            b_type = BlockType.PARAGRAPH
            meta: dict[str, Any] = {}
            if text.startswith(("- ", "* ", "• ", "1. ", "2. ")):
                b_type = BlockType.LIST_ITEM
            elif len(text) < 60 and not text.endswith((".", ":", ";")) and idx == 0:
                b_type = BlockType.HEADING
                meta["heading_level"] = 1

            block = CanonicalBlock(
                block_id=self._generate_block_id(1, idx),
                block_type=b_type,
                text=text,
                reading_order=idx,
                page_number=1,
                confidence=1.0,
                extraction_engine=self.engine_name,
                provenance="native",
                metadata=meta,
            )
            blocks.append(block)

        page = CanonicalPage(
            page_number=1,
            is_scanned=False,
            ocr_applied=False,
            blocks=blocks,
            metadata={"paragraph_count": len(blocks)},
        )

        metadata = {
            "format": "RTF",
            "encoding": encoding_used,
            "char_count": len(plain_text),
            "word_count": len(plain_text.split()),
        }

        return CanonicalDocument(
            document_id=doc_id,
            original_filename=original_filename,
            detected_format="rtf",
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
