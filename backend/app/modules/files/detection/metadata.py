"""Step 7: Lightweight and safe metadata extraction."""

import os
import re
import struct
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.security import calculate_file_sha256


class SafeMetadataExtractor:
    """Extracts lightweight metadata from file headers without executing or decompressing entire payloads."""

    @classmethod
    def extract_metadata(
        cls,
        file_path: Path,
        format_id: str,
        category: str,
        mime_type: str,
        original_filename: str | None = None,
    ) -> dict[str, Any]:
        stat_res = file_path.stat()
        file_size = stat_res.st_size

        metadata: dict[str, Any] = {
            "file_size": file_size,
            "created_at": datetime.fromtimestamp(stat_res.st_ctime, tz=UTC).isoformat(),
            "modified_at": datetime.fromtimestamp(stat_res.st_mtime, tz=UTC).isoformat(),
            "sha256": calculate_file_sha256(file_path),
            "mime_type": mime_type,
            "format_id": format_id,
            "category": category,
            "original_filename": original_filename or file_path.name,
        }

        # Format-specific metadata extraction
        try:
            if format_id == "png":
                meta = cls._extract_png_metadata(file_path)
                metadata.update(meta)
            elif format_id in ("jpeg", "jpg"):
                meta = cls._extract_jpeg_metadata(file_path)
                metadata.update(meta)
            elif format_id == "gif":
                meta = cls._extract_gif_metadata(file_path)
                metadata.update(meta)
            elif format_id == "bmp":
                meta = cls._extract_bmp_metadata(file_path)
                metadata.update(meta)
            elif format_id == "pdf":
                meta = cls._extract_pdf_metadata(file_path)
                metadata.update(meta)
            elif format_id in ("zip", "docx", "xlsx", "pptx", "odt", "ods", "odp", "epub"):
                meta = cls._extract_zip_metadata(file_path)
                metadata.update(meta)
            elif category in ("document", "code", "structured_data"):
                meta = cls._extract_text_metadata(file_path)
                metadata.update(meta)

            # Detect text encoding / BOM
            if category in ("document", "code", "structured_data"):
                try:
                    with open(file_path, "rb") as f:
                        hdr = f.read(4)
                    if hdr.startswith(b"\xef\xbb\xbf"):
                        metadata["encoding"] = "utf-8-sig"
                    elif hdr.startswith(b"\xff\xfe\x00\x00"):
                        metadata["encoding"] = "utf-32-le"
                    elif hdr.startswith(b"\x00\x00\xfe\xff"):
                        metadata["encoding"] = "utf-32-be"
                    elif hdr.startswith(b"\xff\xfe"):
                        metadata["encoding"] = "utf-16-le"
                    elif hdr.startswith(b"\xfe\xff"):
                        metadata["encoding"] = "utf-16-be"
                    elif "encoding" not in metadata:
                        metadata["encoding"] = "utf-8"
                except Exception:
                    pass
        except Exception:
            # Metadata extraction is best-effort and must never crash detection
            pass

        return metadata

    @staticmethod
    def _extract_png_metadata(file_path: Path) -> dict[str, Any]:
        with open(file_path, "rb") as f:
            header = f.read(32)
        if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", header[16:26])
            return {
                "dimensions": {"width": width, "height": height},
                "bit_depth": bit_depth,
                "color_type": color_type,
            }
        return {}

    @staticmethod
    def _extract_jpeg_metadata(file_path: Path) -> dict[str, Any]:
        with open(file_path, "rb") as f:
            # Read first 16KB to locate SOF0 / SOF2 marker
            data = f.read(16384)
        if len(data) < 4 or data[:2] != b"\xff\xd8":
            return {}

        offset = 2
        while offset < len(data) - 8:
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            # Baseline DCT (0xC0) or Progressive DCT (0xC2)
            if marker in (0xC0, 0xC2):
                height, width = struct.unpack(">HH", data[offset + 5 : offset + 9])
                return {"dimensions": {"width": width, "height": height}}
            # Advance length
            length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
            offset += 2 + length
        return {}

    @staticmethod
    def _extract_gif_metadata(file_path: Path) -> dict[str, Any]:
        with open(file_path, "rb") as f:
            header = f.read(14)
        if len(header) >= 10 and (header[:6] in (b"GIF87a", b"GIF89a")):
            width, height = struct.unpack("<HH", header[6:10])
            return {
                "dimensions": {"width": width, "height": height},
                "version": header[:6].decode("ascii"),
            }
        return {}

    @staticmethod
    def _extract_bmp_metadata(file_path: Path) -> dict[str, Any]:
        with open(file_path, "rb") as f:
            header = f.read(30)
        if len(header) >= 26 and header[:2] == b"BM":
            width, height = struct.unpack("<ii", header[18:26])
            return {"dimensions": {"width": abs(width), "height": abs(height)}}
        return {}

    @staticmethod
    def _extract_pdf_metadata(file_path: Path) -> dict[str, Any]:
        meta: dict[str, Any] = {}
        with open(file_path, "rb") as f:
            head = f.read(1024)
            # Find version string: %PDF-1.x
            match = re.search(rb"%PDF-(\d+\.\d+)", head)
            if match:
                meta["pdf_version"] = match.group(1).decode("ascii")

            # Lightweight approximate page count (scan up to 256KB from end of file)
            f.seek(0, os.SEEK_END)
            size = f.tell()
            seek_pos = max(0, size - 262144)
            f.seek(seek_pos)
            tail = f.read(262144)
            pages = len(re.findall(rb"/Type\s*/Page\b", tail))
            if pages > 0:
                meta["page_count_estimate"] = pages
        return meta

    @staticmethod
    def _extract_zip_metadata(file_path: Path) -> dict[str, Any]:
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                infolist = zf.infolist()
                total_uncompressed = sum(info.file_size for info in infolist)
                return {
                    "entry_count": len(infolist),
                    "total_uncompressed_bytes": total_uncompressed,
                    "compression_type": infolist[0].compress_type if infolist else 0,
                }
        except Exception:
            return {}

    @staticmethod
    def _extract_text_metadata(file_path: Path) -> dict[str, Any]:
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read(65536)  # Read up to 64KB for stats
                lines = content.splitlines()
                return {
                    "line_count": len(lines),
                    "character_count": len(content),
                    "word_count": len(content.split()),
                }
        except Exception:
            return {}
