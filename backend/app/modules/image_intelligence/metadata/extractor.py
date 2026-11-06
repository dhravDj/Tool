"""Robust and secure image metadata extraction with privacy-preserving EXIF sanitization."""

import logging
import re
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET
from PIL import ExifTags, Image

from app.modules.image_intelligence.schemas.image_document import ImageMetadata

logger = logging.getLogger(__name__)

# Enforce strict decompression bomb threshold (89 MP)
Image.MAX_IMAGE_PIXELS = 89_478_485

# Sensitive EXIF tag IDs to sanitize for privacy
SENSITIVE_EXIF_TAG_NAMES = {
    "GPSInfo",
    "BodySerialNumber",
    "CameraSerialNumber",
    "LensSerialNumber",
    "OwnerName",
    "Artist",
}


class ImageMetadataExtractor:
    """Extracts technical attributes, dimensions, color profiles, and sanitized EXIF from images."""

    @classmethod
    def extract(cls, file_path: Path, format_id: str | None = None) -> ImageMetadata:
        """Extract metadata from image file, routing SVGs to safe XML parser and raster formats to Pillow."""
        file_size = file_path.stat().st_size
        ext = (format_id or file_path.suffix.lstrip(".")).lower()
        if ext in ("jpeg", "jpg"):
            ext = "jpeg"

        if ext == "svg":
            return cls._extract_svg(file_path, file_size)

        return cls._extract_raster(file_path, ext, file_size)

    @classmethod
    def _extract_svg(cls, file_path: Path, file_size: int) -> ImageMetadata:
        """Parse vector SVG using defusedxml without executing external entities or scripts."""
        try:
            tree = ET.parse(str(file_path))
            root = tree.getroot()

            width = 800
            height = 600

            w_attr = root.attrib.get("width")
            h_attr = root.attrib.get("height")
            vb_attr = root.attrib.get("viewBox")

            if w_attr and h_attr:
                w_clean = re.sub(r"[^\d.]", "", w_attr)
                h_clean = re.sub(r"[^\d.]", "", h_attr)
                if w_clean and h_clean:
                    width = int(float(w_clean))
                    height = int(float(h_clean))
            elif vb_attr:
                parts = re.split(r"[\s,]+", vb_attr.strip())
                if len(parts) == 4:
                    width = int(float(parts[2]))
                    height = int(float(parts[3]))

            aspect_ratio = round(width / max(1, height), 3)

            return ImageMetadata(
                format="svg",
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
                color_mode="Vector/RGBA",
                channels=4,
                bit_depth=24,
                file_size=file_size,
                dpi=(72.0, 72.0),
                has_transparency=True,
                is_animated=False,
                frame_count=1,
                exif_scrubbed={"is_vector": True, "element_count": len(list(root.iter()))},
                gps_redacted=True,
            )
        except Exception as exc:
            logger.warning(f"Error parsing SVG metadata: {exc}")
            return ImageMetadata(
                format="svg",
                width=800,
                height=600,
                aspect_ratio=1.333,
                color_mode="Vector",
                channels=3,
                bit_depth=24,
                file_size=file_size,
                has_transparency=True,
                gps_redacted=True,
            )

    @classmethod
    def _extract_raster(cls, file_path: Path, format_name: str, file_size: int) -> ImageMetadata:
        """Parse raster formats (PNG, JPEG, WEBP, TIFF, BMP) with Pillow."""
        with Image.open(file_path) as img:
            width, height = img.size
            aspect_ratio = round(width / max(1, height), 3)
            color_mode = img.mode
            channels = len(img.getbands())

            # Determine bit depth
            bit_depth = 8 * channels
            if color_mode in ("1",):
                bit_depth = 1
            elif color_mode in ("L", "P"):
                bit_depth = 8
            elif color_mode in ("RGB", "YCbCr"):
                bit_depth = 24
            elif color_mode in ("RGBA", "CMYK"):
                bit_depth = 32
            elif color_mode in ("I", "F"):
                bit_depth = 32

            # DPI / Resolution
            dpi: tuple[float, float] | None = None
            raw_dpi = img.info.get("dpi")
            if raw_dpi and isinstance(raw_dpi, (tuple, list)) and len(raw_dpi) >= 2:
                dpi = (round(float(raw_dpi[0]), 1), round(float(raw_dpi[1]), 1))

            # Transparency check
            has_transparency = (
                color_mode in ("RGBA", "LA", "PA")
                or "transparency" in img.info
                or ("A" in color_mode)
            )

            # Animation
            is_animated = bool(getattr(img, "is_animated", False))
            frame_count = int(getattr(img, "n_frames", 1))
            duration_ms = img.info.get("duration")

            # EXIF extraction and sanitization
            exif_scrubbed: dict[str, Any] = {}
            gps_redacted = False

            try:
                exif_data = img.getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        if tag_name in SENSITIVE_EXIF_TAG_NAMES:
                            gps_redacted = True
                            continue  # Strip sensitive GPS, serials, and identity tags

                        # Safe tags to retain (camera model, orientation, datetime, software)
                        if isinstance(value, (str, int, float, bool)):
                            exif_scrubbed[tag_name] = value
                        elif isinstance(value, bytes):
                            try:
                                exif_scrubbed[tag_name] = value.decode(
                                    "utf-8", errors="ignore"
                                ).strip()
                            except Exception:
                                pass
            except Exception as e:
                logger.debug(f"EXIF parsing bypassed or failed: {e}")

            return ImageMetadata(
                format=format_name,
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
                color_mode=color_mode,
                channels=channels,
                bit_depth=bit_depth,
                file_size=file_size,
                dpi=dpi,
                has_transparency=has_transparency,
                is_animated=is_animated,
                frame_count=frame_count,
                duration_ms=duration_ms,
                exif_scrubbed=exif_scrubbed,
                gps_redacted=gps_redacted or True,
            )
