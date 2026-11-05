"""Non-destructive image preprocessing pipeline for OCR and Vision analysis."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)


@dataclass
class PreprocessedBundle:
    """Preprocessed working image representations and metadata."""

    working_image: Image.Image
    ocr_image: Image.Image
    deskew_angle: float = 0.0
    scaling_factor: float = 1.0
    tiles: list[dict[str, Any]] = field(default_factory=list)
    applied_steps: list[str] = field(default_factory=list)


class ImagePreprocessor:
    """Applies non-destructive computer vision and morphological preprocessing."""

    def __init__(
        self,
        max_dimension: int = 4096,
        tile_size: int = 1536,
        tile_overlap_ratio: float = 0.1,
    ) -> None:
        self.max_dimension = max_dimension
        self.tile_size = tile_size
        self.tile_overlap_ratio = tile_overlap_ratio

    def process(
        self,
        source: Path | Image.Image,
        enable_deskew: bool = True,
        enable_binarization: bool = True,
        enable_contrast_enhancement: bool = True,
        enable_tiling: bool = True,
    ) -> PreprocessedBundle:
        """Execute full preprocessing pipeline without mutating source."""
        applied_steps: list[str] = []

        # 1. Load image safely
        if isinstance(source, Path):
            with Image.open(source) as raw:
                img = raw.copy()
        else:
            img = source.copy()

        # 2. Correct EXIF Orientation
        try:
            transposed = ImageOps.exif_transpose(img)
            if transposed is not None:
                img = transposed
                applied_steps.append("exif_orientation_correction")
        except Exception:
            pass

        # 3. Ensure RGB base for vision processing
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
            applied_steps.append("color_normalization_to_rgb")

        # 4. Dimensional Bounds Resizing
        orig_w, orig_h = img.size
        scaling_factor = 1.0
        if max(orig_w, orig_h) > self.max_dimension:
            scale = self.max_dimension / float(max(orig_w, orig_h))
            new_w = max(1, int(orig_w * scale))
            new_h = max(1, int(orig_h * scale))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            scaling_factor = scale
            applied_steps.append(f"rescale_to_max_{self.max_dimension}px")

        # 5. Deskewing
        deskew_angle = 0.0
        if enable_deskew:
            deskew_angle = self._estimate_skew_angle(img)
            if abs(deskew_angle) >= 0.5:
                # Rotate with BICUBIC and expand to avoid clipping
                img = img.rotate(-deskew_angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="white")
                applied_steps.append(f"deskew_corrected_{deskew_angle:.2f}_deg")

        working_image = img.copy()

        # 6. OCR-Optimized Derivation
        ocr_img = self._create_ocr_representation(
            working_image,
            enable_contrast=enable_contrast_enhancement,
            enable_binarization=enable_binarization,
            applied_steps=applied_steps,
        )

        # 7. Intelligent Tiling for Large Images
        tiles: list[dict[str, Any]] = []
        cur_w, cur_h = working_image.size
        if enable_tiling and (cur_w > self.tile_size or cur_h > self.tile_size):
            tiles = self._generate_tiles(working_image, self.tile_size, self.tile_overlap_ratio)
            applied_steps.append(f"generated_{len(tiles)}_overlapping_tiles")

        return PreprocessedBundle(
            working_image=working_image,
            ocr_image=ocr_img,
            deskew_angle=deskew_angle,
            scaling_factor=scaling_factor,
            tiles=tiles,
            applied_steps=applied_steps,
        )

    def _estimate_skew_angle(self, img: Image.Image) -> float:
        """Estimate skew angle using horizontal projection profile variance."""
        try:
            # Downscale for rapid projection analysis
            small = img.convert("L").resize((300, 300), Image.Resampling.BILINEAR)
            arr = np.asarray(small, dtype=np.uint8)

            # Simple edge derivative
            edges = np.abs(np.diff(arr, axis=0))
            threshold = np.mean(edges) + np.std(edges)
            bin_edges = (edges > threshold).astype(np.float32)

            best_score = -1.0
            best_angle = 0.0

            # Test angles between -15 and +15 degrees
            for angle in np.linspace(-15.0, 15.0, 31):
                rotated = Image.fromarray((bin_edges * 255).astype(np.uint8)).rotate(
                    angle, resample=Image.Resampling.NEAREST
                )
                rot_arr = np.asarray(rotated, dtype=np.float32)
                # Variance of row sums indicates alignment with text lines
                row_sums = np.sum(rot_arr, axis=1)
                score = float(np.var(row_sums))

                if score > best_score:
                    best_score = score
                    best_angle = float(angle)

            return round(best_angle, 2)
        except Exception as exc:
            logger.debug(f"Skew detection fallback: {exc}")
            return 0.0

    def _create_ocr_representation(
        self,
        img: Image.Image,
        enable_contrast: bool,
        enable_binarization: bool,
        applied_steps: list[str],
    ) -> Image.Image:
        """Derive high-contrast, binarized grayscale image for OCR engines."""
        # Convert to Grayscale
        gray = img.convert("L")
        applied_steps.append("grayscale_conversion")

        # Contrast enhancement (Auto-contrast + slight sharpness boost)
        if enable_contrast:
            gray = ImageOps.autocontrast(gray, cutoff=1)
            enhancer = ImageEnhance.Contrast(gray)
            gray = enhancer.enhance(1.5)
            gray = gray.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))
            applied_steps.append("autocontrast_and_unsharp_mask")

        # Adaptive / Otsu-like Binarization
        if enable_binarization:
            arr = np.asarray(gray, dtype=np.uint8)
            # Otsu threshold calculation
            hist, _ = np.histogram(arr, bins=256, range=(0, 256))
            total = arr.size
            current_max = 0.0
            threshold = 128
            sum_total = np.dot(np.arange(256), hist)
            sum_bg = 0.0
            weight_bg = 0

            for t in range(256):
                weight_bg += hist[t]
                if weight_bg == 0:
                    continue
                weight_fg = total - weight_bg
                if weight_fg == 0:
                    break
                sum_bg += t * hist[t]
                mean_bg = sum_bg / weight_bg
                mean_fg = (sum_total - sum_bg) / weight_fg
                variance = weight_bg * weight_fg * ((mean_bg - mean_fg) ** 2)
                if variance > current_max:
                    current_max = variance
                    threshold = t

            # Apply threshold
            bin_arr = np.where(arr > threshold, 255, 0).astype(np.uint8)
            bin_img = Image.fromarray(bin_arr, mode="L")
            applied_steps.append(f"otsu_binarization_threshold_{threshold}")
            return bin_img

        return gray

    def _generate_tiles(
        self,
        img: Image.Image,
        tile_size: int,
        overlap_ratio: float,
    ) -> list[dict[str, Any]]:
        """Slice large image into overlapping rectangular sub-windows."""
        width, height = img.size
        stride = max(1, int(tile_size * (1.0 - overlap_ratio)))
        tiles: list[dict[str, Any]] = []

        tile_idx = 0
        y0 = 0
        while y0 < height:
            y1 = min(height, y0 + tile_size)
            x0 = 0
            while x0 < width:
                x1 = min(width, x0 + tile_size)
                tile_box = [x0, y0, x1, y1]
                tile_crop = img.crop((x0, y0, x1, y1))
                tiles.append({
                    "tile_index": tile_idx,
                    "pixel_box": tile_box,
                    "normalized_box": [
                        round(y0 / height, 4),
                        round(x0 / width, 4),
                        round(y1 / height, 4),
                        round(x1 / width, 4),
                    ],
                    "image": tile_crop,
                })
                tile_idx += 1
                if x1 >= width:
                    break
                x0 += stride
            if y1 >= height:
                break
            y0 += stride

        return tiles
