"""Plain Text Document Extraction Adapter supporting multiple encodings."""

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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


class PlainTextExtractor(BaseDocumentExtractor):
    """Robust extractor for plain text files with automatic encoding fallback."""

    engine_name = "plain_text_extractor"
    version = "1.0.0"
    supported_formats = ["txt"]

    # Encodings to probe in prioritized sequence
    CANDIDATE_ENCODINGS = [
        "utf-8-sig",  # UTF-8 with optional BOM
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "utf-32",
        "cp1252",  # Windows-1252
        "iso-8859-1",  # Latin-1
    ]

    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract text blocks and encoding metadata from a text file."""
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
            raise CorruptedDocumentError(f"Failed to read file: {exc}") from exc

        # 1. Decode with Encoding Discovery
        decoded_text = ""
        detected_encoding = None
        warnings: list[str] = []

        # Check BOM signatures first
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            detected_encoding = "utf-8-sig"
            decoded_text = raw_bytes.decode("utf-8-sig")
        elif raw_bytes.startswith(b"\xff\xfe\x00\x00"):
            detected_encoding = "utf-32-le"
            decoded_text = raw_bytes.decode("utf-32-le")
        elif raw_bytes.startswith(b"\x00\x00\xfe\xff"):
            detected_encoding = "utf-32-be"
            decoded_text = raw_bytes.decode("utf-32-be")
        elif raw_bytes.startswith(b"\xff\xfe"):
            detected_encoding = "utf-16-le"
            decoded_text = raw_bytes.decode("utf-16-le")
        elif raw_bytes.startswith(b"\xfe\xff"):
            detected_encoding = "utf-16-be"
            decoded_text = raw_bytes.decode("utf-16-be")
        else:
            # Check UTF-8 first
            try:
                decoded_text = raw_bytes.decode("utf-8")
                detected_encoding = "utf-8"
            except UnicodeDecodeError:
                # If null bytes are present, test UTF-16/32
                if b"\x00" in raw_bytes[:256]:
                    for enc in ["utf-16", "utf-16-le", "utf-16-be", "utf-32"]:
                        try:
                            decoded_text = raw_bytes.decode(enc)
                            detected_encoding = enc
                            break
                        except (UnicodeDecodeError, LookupError):
                            continue

                # Otherwise probe 8-bit European / Windows encodings
                if detected_encoding is None:
                    for enc in ["cp1252", "iso-8859-1"]:
                        try:
                            decoded_text = raw_bytes.decode(enc)
                            detected_encoding = enc
                            break
                        except (UnicodeDecodeError, LookupError):
                            continue

        if detected_encoding is None:
            # Fallback with replacement
            detected_encoding = "utf-8"
            decoded_text = raw_bytes.decode("utf-8", errors="replace")
            warnings.append(
                "Document could not be decoded cleanly with standard encodings; "
                "decoded using UTF-8 with character replacement."
            )

        # Normalize line endings
        normalized_text = decoded_text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Split into Structural Blocks (by blank lines)
        raw_paragraphs = normalized_text.split("\n\n")
        blocks: list[CanonicalBlock] = []

        for idx, para in enumerate(raw_paragraphs):
            text = para.strip()
            if not text:
                continue

            # Classify block
            b_type = BlockType.PARAGRAPH
            if text.startswith(("- ", "* ", "1. ", "2. ")):
                b_type = BlockType.LIST_ITEM
            elif len(text) < 60 and not text.endswith((".", ":", ";")) and idx == 0:
                b_type = BlockType.HEADING

            block = CanonicalBlock(
                block_id=self._generate_block_id(1, len(blocks)),
                block_type=b_type,
                text=text,
                reading_order=len(blocks),
                page_number=1,
                confidence=1.0,
                extraction_engine=self.engine_name,
                provenance="native",
                metadata={"raw_length": len(text), "lines": text.count("\n") + 1},
            )
            blocks.append(block)

        # If file was entirely whitespace or empty
        if not blocks and normalized_text.strip():
            blocks.append(
                CanonicalBlock(
                    block_id=self._generate_block_id(1, 0),
                    block_type=BlockType.PARAGRAPH,
                    text=normalized_text.strip(),
                    reading_order=0,
                    page_number=1,
                    confidence=1.0,
                    extraction_engine=self.engine_name,
                    provenance="native",
                )
            )

        page = CanonicalPage(
            page_number=1,
            is_scanned=False,
            ocr_applied=False,
            blocks=blocks,
            metadata={"paragraph_count": len(blocks)},
        )

        metadata = {
            "encoding": detected_encoding,
            "byte_size": len(raw_bytes),
            "char_count": len(normalized_text),
            "word_count": len(normalized_text.split()),
            "line_count": normalized_text.count("\n") + 1,
        }

        status = (
            ExtractionStatus.COMPLETED_WITH_WARNINGS if warnings else ExtractionStatus.COMPLETED
        )

        return CanonicalDocument(
            document_id=doc_id,
            original_filename=original_filename,
            detected_format="txt",
            extraction_status=status,
            metadata=metadata,
            page_count=1,
            extraction_engine=self.engine_name,
            extraction_version=self.version,
            created_at=datetime.now(UTC).isoformat(),
            pages=[page],
            blocks=blocks,
            warnings=warnings,
            errors=[],
        )
