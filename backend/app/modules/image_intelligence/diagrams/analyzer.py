"""Flowchart and technical diagram structure and topology analyzer."""

import logging
import re
from typing import Any

from PIL import Image

from app.modules.image_intelligence.schemas.image_document import (
    DiagramAnalysis,
    ImageRegion,
    RegionType,
)

logger = logging.getLogger(__name__)


class DiagramAnalyzer:
    """Identifies flowchart nodes, relational connectors, flow directions, and diagram types."""

    FLOWCHART_KEYWORDS = {
        "start",
        "end",
        "stop",
        "decision",
        "process",
        "condition",
        "yes",
        "no",
        "if",
        "else",
        "step",
    }
    ARCHITECTURE_KEYWORDS = {
        "client",
        "server",
        "database",
        "api",
        "microservice",
        "gateway",
        "backend",
        "frontend",
        "queue",
        "cache",
    }
    SEQUENCE_KEYWORDS = {
        "request",
        "response",
        "actor",
        "lifeline",
        "async",
        "sync",
        "call",
        "return",
    }

    def analyze(
        self,
        img: Image.Image,
        ocr_text: str = "",
        regions: list[ImageRegion] | None = None,
    ) -> tuple[DiagramAnalysis, list[ImageRegion]]:
        """Evaluate visual and textual features to determine diagram structure."""
        regions = regions or []
        width, height = img.size
        text_lower = ocr_text.lower()
        words = set(re.findall(r"\b[a-z]{3,}\b", text_lower))

        flowchart_score = len(words.intersection(self.FLOWCHART_KEYWORDS))
        arch_score = len(words.intersection(self.ARCHITECTURE_KEYWORDS))
        seq_score = len(words.intersection(self.SEQUENCE_KEYWORDS))

        has_arrows = "->" in ocr_text or "-->" in ocr_text or "—>" in ocr_text or "=>" in ocr_text
        max_score = max(flowchart_score, arch_score, seq_score)

        is_diagram = False
        diagram_type = "none"
        confidence = 0.0

        if max_score >= 2 or (max_score >= 1 and has_arrows):
            is_diagram = True
            if flowchart_score >= max(arch_score, seq_score):
                diagram_type = "flowchart"
                confidence = min(0.95, 0.70 + (flowchart_score * 0.06))
            elif arch_score >= seq_score:
                diagram_type = "architecture"
                confidence = min(0.95, 0.70 + (arch_score * 0.06))
            else:
                diagram_type = "sequence"
                confidence = min(0.92, 0.70 + (seq_score * 0.06))

        if not is_diagram:
            return DiagramAnalysis(is_diagram=False), []

        # Identify candidate diagram nodes from OCR text regions
        nodes: list[dict[str, Any]] = []
        diagram_regions: list[ImageRegion] = []

        # Filter regions that look like discrete node boxes or labels
        text_regions = [r for r in regions if r.region_type == RegionType.TEXT and r.text]
        for idx, r in enumerate(text_regions[:20]):
            node_id = f"node_{idx + 1}"
            label = r.text.strip() if r.text else ""
            nodes.append(
                {
                    "node_id": node_id,
                    "label": label,
                    "shape": "rectangle",
                    "bounding_box": r.bounding_box,
                    "pixel_box": r.pixel_box,
                }
            )
            diagram_regions.append(
                ImageRegion(
                    region_id=f"diagram_node_{idx + 1}",
                    region_type=RegionType.DIAGRAM,
                    bounding_box=r.bounding_box,
                    pixel_box=r.pixel_box,
                    label=f"diagram_node:{label[:24]}",
                    confidence=confidence,
                    provenance="diagram-parser",
                    attributes={"node_type": "step", "shape": "rectangle"},
                )
            )

        # Estimate flow direction from node positions
        flow_direction = "unknown"
        if len(nodes) >= 2:
            y_diff = nodes[-1]["bounding_box"][0] - nodes[0]["bounding_box"][0]
            x_diff = nodes[-1]["bounding_box"][1] - nodes[0]["bounding_box"][1]
            if abs(y_diff) > abs(x_diff):
                flow_direction = "top-to-bottom" if y_diff > 0 else "bottom-to-top"
            else:
                flow_direction = "left-to-right" if x_diff > 0 else "right-to-left"

        connectors_count = max(1, len(nodes) - 1) if nodes else 0

        analysis = DiagramAnalysis(
            is_diagram=True,
            diagram_type=diagram_type,
            nodes=nodes,
            connectors_count=connectors_count,
            flow_direction=flow_direction,
            confidence=round(confidence, 2),
        )

        return analysis, diagram_regions
