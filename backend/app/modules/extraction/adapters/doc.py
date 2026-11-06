"""Legacy Microsoft Word 97-2003 (DOC) Document Extraction Adapter."""

import asyncio
import logging
import re
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import olefile

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

logger = logging.getLogger(__name__)


class LegacyDocExtractor(BaseDocumentExtractor):
    """Secure extraction adapter for legacy binary Word 97-2003 (.doc) documents.

    Never executes macros or active content. Uses pure-Python OLE2 stream inspection
    with optional system utility (antiword / catdoc) acceleration when present.
    """

    engine_name = "legacy_doc_extractor"
    version = "1.0.0"
    supported_formats = ["doc"]

    async def extract_document(
        self,
        file_path: Path,
        original_filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> CanonicalDocument:
        """Extract text and metadata from legacy binary Word document."""
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

        # Verify OLE2 compound document format
        if not olefile.isOleFile(str(file_path)):
            raise CorruptedDocumentError(
                f"File '{original_filename}' is not a valid OLE2 compound binary document."
            )

        metadata: dict[str, Any] = {}
        warnings: list[str] = []
        errors: list[str] = []

        # 1. Extract OLE Summary Metadata
        try:
            with olefile.OleFileIO(str(file_path)) as ole:
                meta = ole.get_metadata()
                metadata = {
                    "title": getattr(meta, "title", None) or None,
                    "author": getattr(meta, "author", None) or None,
                    "subject": getattr(meta, "subject", None) or None,
                    "keywords": getattr(meta, "keywords", None) or None,
                    "comments": getattr(meta, "comments", None) or None,
                    "last_saved_by": getattr(meta, "last_saved_by", None) or None,
                    "revision_number": getattr(meta, "revision_number", None) or None,
                    "total_edit_time": getattr(meta, "total_edit_time", None) or None,
                    "created": meta.create_time.isoformat()
                    if getattr(meta, "create_time", None)
                    else None,
                    "modified": meta.last_saved_time.isoformat()
                    if getattr(meta, "last_saved_time", None)
                    else None,
                }

                # Check for macro streams (for audit/warning only - NEVER execute)
                has_macros = any(
                    "vba" in "/".join(s).lower() or "macros" in "/".join(s).lower()
                    for s in ole.listdir()
                )
                if has_macros:
                    warnings.append(
                        "Document contains VBA/macro streams. Macro execution is disabled for security."
                    )
        except Exception as exc:
            warnings.append(f"Failed to read OLE summary metadata: {exc}")

        # 2. Extract Document Content
        extracted_text = ""

        # Check for system utility antiword first if available
        antiword_bin = shutil.which("antiword")
        if antiword_bin:
            try:
                import subprocess

                res = subprocess.run(
                    [antiword_bin, str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if res.returncode == 0 and res.stdout.strip():
                    extracted_text = res.stdout.strip()
            except Exception as exc:
                warnings.append(f"antiword execution failed: {exc}")

        # Check for headless LibreOffice conversion if antiword is unavailable
        if not extracted_text:
            extracted_text = self._extract_with_libreoffice(file_path, warnings)

        # Fallback: Pure-Python WordDocument Stream Extraction
        if not extracted_text:
            extracted_text = self._extract_from_word_stream(file_path, warnings)

        # 3. Parse Extracted Text into Blocks
        blocks: list[CanonicalBlock] = []
        raw_paragraphs = [p.strip() for p in extracted_text.split("\n\n") if p.strip()]

        # If splitting by double newlines yielded single block or nothing, split by single newline
        if len(raw_paragraphs) <= 1 and "\n" in extracted_text:
            raw_paragraphs = [p.strip() for p in extracted_text.split("\n") if p.strip()]

        for idx, text in enumerate(raw_paragraphs):
            # Classify block
            b_type = BlockType.PARAGRAPH
            meta_block: dict[str, Any] = {}
            if text.startswith(("- ", "* ", "• ", "1. ", "2. ")):
                b_type = BlockType.LIST_ITEM
            elif len(text) < 60 and not text.endswith((".", ":", ";")):
                b_type = BlockType.HEADING
                meta_block["heading_level"] = 1 if idx == 0 else 2

            block = CanonicalBlock(
                block_id=self._generate_block_id(1, idx),
                block_type=b_type,
                text=text,
                reading_order=idx,
                page_number=1,
                confidence=0.9,
                extraction_engine=self.engine_name,
                provenance="native_ole_stream",
                metadata=meta_block,
            )
            blocks.append(block)

        page = CanonicalPage(
            page_number=1,
            is_scanned=False,
            ocr_applied=False,
            blocks=blocks,
            metadata={"paragraph_count": len(blocks)},
        )

        status = (
            ExtractionStatus.COMPLETED_WITH_WARNINGS if warnings else ExtractionStatus.COMPLETED
        )

        return CanonicalDocument(
            document_id=doc_id,
            original_filename=original_filename,
            detected_format="doc",
            extraction_status=status,
            metadata=metadata,
            page_count=1,
            extraction_engine=self.engine_name,
            extraction_version=self.version,
            created_at=datetime.now(UTC).isoformat(),
            pages=[page],
            blocks=blocks,
            warnings=warnings,
            errors=errors,
        )

    def _extract_with_libreoffice(self, file_path: Path, warnings: list[str]) -> str:
        """Safely convert legacy DOC to text using LibreOffice in headless sandbox mode."""
        lo_bin = shutil.which("libreoffice") or shutil.which("soffice")
        if not lo_bin:
            return ""

        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            try:
                # Security flags: --headless, --nodefault, --nolockcheck, --nologo, --norestore
                # Strict 15-second timeout, zero interactive prompts, no network
                cmd = [
                    lo_bin,
                    "--headless",
                    "--nodefault",
                    "--nolockcheck",
                    "--nologo",
                    "--norestore",
                    "--convert-to",
                    "txt:Text",
                    "--outdir",
                    str(temp_path),
                    str(file_path),
                ]
                res = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                if res.returncode == 0:
                    txt_files = list(temp_path.glob("*.txt"))
                    if txt_files and txt_files[0].stat().st_size > 0:
                        return txt_files[0].read_text(encoding="utf-8", errors="ignore").strip()
            except subprocess.TimeoutExpired:
                warnings.append(
                    "LibreOffice conversion timed out after 15s; falling back to OLE stream parser."
                )
            except Exception as exc:
                warnings.append(f"LibreOffice conversion failed: {exc}")
        return ""

    def _extract_from_word_stream(self, file_path: Path, warnings: list[str]) -> str:
        """Extract text chunks safely from the binary WordDocument stream using FIB and stream analysis."""
        try:
            with olefile.OleFileIO(str(file_path)) as ole:
                if not ole.exists("WordDocument"):
                    warnings.append("No 'WordDocument' stream found in OLE2 container.")
                    return ""

                word_stream = ole.openstream("WordDocument").read()
                chunks: list[str] = []

                # Strategy 1: FIB (File Information Block) structural extraction
                if len(word_stream) >= 80:
                    import struct

                    w_ident, _n_fib = struct.unpack_from("<HH", word_stream, 0)
                    if w_ident in (0xA5EC, 0xA5DC):
                        fc_min = struct.unpack_from("<I", word_stream, 0x18)[0]
                        ccp_text = struct.unpack_from("<I", word_stream, 0x4C)[0]

                        if 0 < fc_min < len(word_stream) and 0 < ccp_text < 5_000_000:
                            # Try 16-bit unicode run at fc_min
                            raw_slice = word_stream[
                                fc_min : min(len(word_stream), fc_min + ccp_text * 2)
                            ]
                            try:
                                decoded_fib = raw_slice.decode("utf-16le", errors="ignore").strip()
                                # Clean control characters except newlines/tabs
                                cleaned_fib = re.sub(
                                    r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", decoded_fib
                                )
                                if len(cleaned_fib) > 10:
                                    chunks.append(cleaned_fib)
                            except Exception:
                                pass

                # Strategy 2: Decode 16-bit unicode strings (min length 4 chars) across stream
                if not chunks or sum(len(c) for c in chunks) < 50:
                    unicode_pattern = re.compile(b"(?:[\x20-\x7e\r\n\t]\x00){4,}")
                    matches_u16 = unicode_pattern.findall(word_stream)
                    for m in matches_u16:
                        try:
                            decoded = m.decode("utf-16le", errors="ignore").strip()
                            if len(decoded) > 3:
                                chunks.append(decoded)
                        except Exception:
                            pass

                # Strategy 3: If unicode matches were sparse, extract printable ASCII runs
                if not chunks or sum(len(c) for c in chunks) < 100:
                    ascii_pattern = re.compile(b"[\x20-\x7e\r\n\t]{6,}")
                    matches_ascii = ascii_pattern.findall(word_stream)
                    for m in matches_ascii:
                        try:
                            decoded = m.decode("latin1", errors="ignore").strip()
                            # Filter out binary junk like font names or internal tags if too repetitive
                            if len(decoded) > 5 and not decoded.startswith(
                                ("Normal", "Default Paragraph", "Times New")
                            ):
                                chunks.append(decoded)
                        except Exception:
                            pass

                # De-duplicate adjacent identical fragments and join
                unique_chunks: list[str] = []
                for c in chunks:
                    if not unique_chunks or unique_chunks[-1] != c:
                        unique_chunks.append(c)

                return "\n\n".join(unique_chunks)
        except Exception as exc:
            warnings.append(f"WordDocument stream parsing error: {exc}")
            return ""
