"""Diagram and connector extraction logic for presentation slides."""

from typing import Any

from app.modules.presentation_intelligence.schemas.presentation_document import (
    DiagramEdge,
    DiagramNode,
    ElementDimensions,
    ElementPosition,
    SlideDiagram,
)


class PresentationDiagramExtractor:
    """Extracts and reconstructs diagram structures (nodes, edges, connectors, groups)."""

    @classmethod
    def extract_slide_diagram(
        cls,
        slide_id: str,
        slide_number: int,
        shapes: list[Any],
        diagram_counter: int = 1,
    ) -> SlideDiagram | None:
        """Extract node-edge diagram structure from geometric shapes and connectors on a slide."""
        nodes: list[DiagramNode] = []
        edges: list[DiagramEdge] = []
        groups: list[dict[str, Any]] = []

        shape_map: dict[str, str] = {}  # shape_id -> node_id

        for idx, shape in enumerate(shapes):
            shape_id = str(getattr(shape, "shape_id", f"s_{idx}"))
            shape_type_name = str(getattr(shape, "shape_type", "UNKNOWN"))

            # Check for Group
            if "GROUP" in shape_type_name:
                group_children = []
                try:
                    for child in shape.shapes:
                        child_text = ""
                        if getattr(child, "has_text_frame", False) and child.text_frame:
                            child_text = child.text_frame.text.strip()
                        group_children.append({
                            "shape_id": getattr(child, "shape_id", ""),
                            "name": getattr(child, "name", ""),
                            "text": child_text,
                        })
                except Exception:
                    pass
                groups.append({
                    "group_id": shape_id,
                    "name": getattr(shape, "name", "Group"),
                    "children": group_children,
                })
                continue

            # Check if Connector / Line
            if "CONNECTOR" in shape_type_name or "LINE" in shape_type_name:
                edge_id = f"edge_{shape_id}"
                source_id = "unknown"
                target_id = "unknown"

                # Check connection sites if available
                if hasattr(shape, "begin_connected_shape") and shape.begin_connected_shape:
                    source_id = str(getattr(shape.begin_connected_shape, "shape_id", "source"))
                if hasattr(shape, "end_connected_shape") and shape.end_connected_shape:
                    target_id = str(getattr(shape.end_connected_shape, "shape_id", "target"))

                edge_text = None
                if getattr(shape, "has_text_frame", False) and shape.text_frame:
                    edge_text = shape.text_frame.text.strip() or None

                edges.append(
                    DiagramEdge(
                        edge_id=edge_id,
                        source_id=source_id,
                        target_id=target_id,
                        label=edge_text,
                        arrow_type="directed" if "ARROW" in shape_type_name else "connector",
                    )
                )
                continue

            # Shapes with text or geometric boxes
            has_text = getattr(shape, "has_text_frame", False) and shape.text_frame
            text_content = shape.text_frame.text.strip() if has_text else ""

            if text_content or ("AUTO_SHAPE" in shape_type_name and not getattr(shape, "has_table", False)):
                node_id = f"node_{shape_id}"
                shape_map[shape_id] = node_id

                left = float(getattr(shape, "left", 0)) / 914400.0
                top = float(getattr(shape, "top", 0)) / 914400.0
                width = float(getattr(shape, "width", 0)) / 914400.0
                height = float(getattr(shape, "height", 0)) / 914400.0

                nodes.append(
                    DiagramNode(
                        node_id=node_id,
                        label=text_content or getattr(shape, "name", "Box"),
                        shape_type=getattr(shape, "name", "rectangle"),
                        position=ElementPosition(left=round(left, 2), top=round(top, 2)),
                        dimensions=ElementDimensions(width=round(width, 2), height=round(height, 2)),
                    )
                )

        # Update edge source/target IDs to point to mapped node_ids if available
        for edge in edges:
            if edge.source_id in shape_map:
                edge.source_id = shape_map[edge.source_id]
            if edge.target_id in shape_map:
                edge.target_id = shape_map[edge.target_id]

        if not nodes and not edges and not groups:
            return None

        # Only return diagram if there's at least an edge or a group
        if len(edges) > 0 or len(groups) > 0:
            return SlideDiagram(
                diagram_id=f"{slide_id}_diag_{diagram_counter}",
                slide_id=slide_id,
                slide_number=slide_number,
                nodes=nodes,
                edges=edges,
                groups=groups,
            )

        return None
