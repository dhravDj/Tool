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
            elif format_id == "webp":
                meta = cls._extract_webp_metadata(file_path)
                metadata.update(meta)
            elif format_id == "tiff":
                meta = cls._extract_tiff_metadata(file_path)
                metadata.update(meta)
            elif format_id == "svg":
                meta = cls._extract_svg_metadata(file_path)
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
            data = f.read(16384)
        if len(data) < 4 or data[:2] != b"\xff\xd8":
            return {}

        offset = 2
        while offset < len(data) - 8:
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            if marker in (0xC0, 0xC2):
                height, width = struct.unpack(">HH", data[offset + 5 : offset + 9])
                return {"dimensions": {"width": width, "height": height}}
            length = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
            offset += 2 + length
        return {}

    @staticmethod
    def _extract_webp_metadata(file_path: Path) -> dict[str, Any]:
        try:
            with open(file_path, "rb") as f:
                header = f.read(64)
            if len(header) < 30 or header[:4] != b"RIFF" or header[8:12] != b"WEBP":
                return {}

            subchunk = header[12:16]
            if subchunk == b"VP8 ":
                # Keyframe header starts at offset 23
                if len(header) >= 30 and header[20:23] == b"\x9d\x01\x2a":
                    w, h = struct.unpack("<HH", header[26:30])
                    return {"dimensions": {"width": w & 0x3FFF, "height": h & 0x3FFF}, "format_variant": "lossy"}
            elif subchunk == b"VP8L":
                # Lossless 1-byte 0x2f signature, 4 bytes width/height bitstream
                if len(header) >= 25 and header[20] == 0x2F:
                    b1, b2, b3, b4 = header[21:25]
                    width = 1 + (((b2 & 0x3F) << 8) | b1)
                    height = 1 + (((b4 & 0x0F) << 10) | (b3 << 2) | ((b2 & 0xC0) >> 6))
                    return {"dimensions": {"width": width, "height": height}, "format_variant": "lossless"}
            elif subchunk == b"VP8X":
                if len(header) >= 30:
                    width = 1 + struct.unpack("<I", header[24:27] + b"\x00")[0]
                    height = 1 + struct.unpack("<I", header[27:30] + b"\x00")[0]
                    flags = header[20]
                    has_animation = bool(flags & 0x02)
                    has_alpha = bool(flags & 0x10)
                    return {
                        "dimensions": {"width": width, "height": height},
                        "format_variant": "extended",
                        "has_animation": has_animation,
                        "has_alpha": has_alpha,
                    }
        except Exception:
            pass
        return {}

    @staticmethod
    def _extract_tiff_metadata(file_path: Path) -> dict[str, Any]:
        try:
            with open(file_path, "rb") as f:
                header = f.read(1024)
            if len(header) < 8:
                return {}

            is_le = header[:2] == b"II"
            endian = "<" if is_le else ">"
            magic = struct.unpack(f"{endian}H", header[2:4])[0]
            if magic != 42:
                return {}

            ifd_offset = struct.unpack(f"{endian}I", header[4:8])[0]
            if ifd_offset + 2 <= len(header):
                num_entries = struct.unpack(f"{endian}H", header[ifd_offset : ifd_offset + 2])[0]
                width = None
                height = None
                for i in range(min(num_entries, 30)):
                    entry_start = ifd_offset + 2 + (i * 12)
                    if entry_start + 12 > len(header):
                        break
                    tag, ttype, _count, val = struct.unpack(
                        f"{endian}HHI4s", header[entry_start : entry_start + 12]
                    )
                    parsed_val = (
                        struct.unpack(f"{endian}H", val[:2])[0]
                        if ttype == 3
                        else struct.unpack(f"{endian}I", val)[0]
                    )
                    if tag == 256:  # ImageWidth
                        width = parsed_val
                    elif tag == 257:  # ImageLength
                        height = parsed_val

                if width and height:
                    return {"dimensions": {"width": width, "height": height}}
        except Exception:
            pass
        return {}

    @staticmethod
    def _extract_svg_metadata(file_path: Path) -> dict[str, Any]:
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                head = f.read(4096)
            # Find svg tag
            svg_match = re.search(r"<svg\b([^>]*)>", head, re.IGNORECASE)
            if svg_match:
                attrs = svg_match.group(1)
                w_match = re.search(r'width=["\']([\d\.]+)', attrs)
                h_match = re.search(r'height=["\']([\d\.]+)', attrs)
                vb_match = re.search(r'viewBox=["\']([\d\.\s,-]+)["\']', attrs)
                meta: dict[str, Any] = {"is_vector": True}
                if w_match and h_match:
                    meta["dimensions"] = {
                        "width": int(float(w_match.group(1))),
                        "height": int(float(h_match.group(1))),
                    }
                elif vb_match:
                    parts = re.split(r"[\s,]+", vb_match.group(1).strip())
                    if len(parts) == 4:
                        meta["dimensions"] = {
                            "width": int(float(parts[2])),
                            "height": int(float(parts[3])),
                        }
                return meta
        except Exception:
            pass
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
            match = re.search(rb"%PDF-(\d+\.\d+)", head)
            if match:
                meta["pdf_version"] = match.group(1).decode("ascii")

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
