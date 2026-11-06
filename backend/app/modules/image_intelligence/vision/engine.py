"""Modular Vision Understanding Engine supporting deterministic heuristic CV and extensible neural backends.

Explicitly clarifies and documents non-neural heuristic classification:
- Default Engine: 'documind-heuristic-cv-v1'
- Engine Type: 'heuristic' (NON-NEURAL)
- Methodology: Deterministic computer vision heuristics (spatial luminance distribution,
  Otsu thresholding, color histogram quantization, gradient variance, token topology).
"""

import logging
from typing import Any

from PIL import Image

from app.modules.image_intelligence.schemas.image_document import (
    ImageAskResponse,
    ImageRegion,
)
from app.modules.image_intelligence.vision.adapters import (
    HeuristicVisionAdapter,
    VisionAdapterInterface,
)

logger = logging.getLogger(__name__)


class VisionIntelligenceEngine:
    """Coordinates scene understanding, captioning, object detection, and grounded Visual Question Answering.

    Decoupled via VisionAdapterInterface to ensure transparent classification between
    deterministic heuristic computer vision algorithms and optional neural model backends.
    """

    def __init__(
        self,
        model_name: str = "documind-heuristic-cv-v1",
        adapter: VisionAdapterInterface | None = None,
    ) -> None:
        self.adapter: VisionAdapterInterface = adapter or HeuristicVisionAdapter()
        self.model_name = model_name or self.adapter.engine_name

    @property
    def engine_name(self) -> str:
        return self.adapter.engine_name

    @property
    def engine_type(self) -> str:
        return self.adapter.engine_type

    @property
    def hardware_acceleration(self) -> str:
        return self.adapter.hardware_acceleration

    def analyze_scene(
        self,
        img: Image.Image,
        ocr_text: str = "",
        metadata_dict: dict[str, Any] | None = None,
    ) -> tuple[str, str, list[str], list[str], list[ImageRegion]]:
        """Analyze image and generate caption, scene type, objects, dominant colors, and object regions."""
        return self.adapter.analyze_scene(img, ocr_text, metadata_dict)

    def answer_question(
        self,
        img: Image.Image,
        question: str,
        caption: str = "",
        ocr_text: str = "",
        regions: list[ImageRegion] | None = None,
        diagram_info: dict[str, Any] | None = None,
        chart_info: dict[str, Any] | None = None,
    ) -> ImageAskResponse:
        """Answer queries grounded in extracted visual entities, OCR words, and document layout."""
        return self.adapter.answer_question(
            img=img,
            question=question,
            caption=caption,
            ocr_text=ocr_text,
            regions=regions,
            diagram_info=diagram_info,
            chart_info=chart_info,
        )

    # Backward-compatible convenience methods delegating to adapter
    def _extract_dominant_colors(self, img: Image.Image, num_colors: int = 5) -> list[str]:
        if isinstance(self.adapter, HeuristicVisionAdapter):
            return self.adapter._extract_dominant_colors(img, num_colors)
        return ["#FFFFFF", "#000000"]

    def _detect_visual_elements(
        self,
        img: Image.Image,
        ocr_text: str,
        dominant_colors: list[str],
    ) -> tuple[str, list[str], list[ImageRegion]]:
        if isinstance(self.adapter, HeuristicVisionAdapter):
            return self.adapter._detect_visual_elements(img, ocr_text, dominant_colors)
        return "general", ["visual_graphic"], []

    def _generate_caption(
        self,
        scene_type: str,
        objects: list[str],
        ocr_text: str,
        width: int,
        height: int,
        colors: list[str],
    ) -> str:
        if isinstance(self.adapter, HeuristicVisionAdapter):
            return self.adapter._generate_caption(
                scene_type, objects, ocr_text, width, height, colors
            )
        return f"Image depicting {', '.join(objects)}."
