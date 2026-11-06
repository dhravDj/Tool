"""Secure XML intelligence engine with XXE defense and hierarchy extraction."""

import uuid
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException

from app.modules.structured_data_intelligence.engines.base import BaseStructuredEngine
from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    ColumnProfile,
    DataProfile,
    StructuredDataDocument,
    StructuredModelInfo,
    ValidationResult,
)


class XMLEngine(BaseStructuredEngine):
    """Secure XML parser providing defensive entity resolution, hierarchy traversal, and tag profiling."""

    @property
    def format(self) -> str:
        return "xml"

    @property
    def supported_extensions(self) -> list[str]:
        return ["xml", "xsd", "xsl"]

    def analyze(
        self,
        file_path_or_bytes: Path | str | bytes,
        file_id: str,
        filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> StructuredDataDocument:
        if isinstance(file_path_or_bytes, bytes):
            raw_text = file_path_or_bytes.decode("utf-8", errors="replace")
        elif isinstance(file_path_or_bytes, (str, Path)):
            p = Path(file_path_or_bytes)
            raw_text = p.read_text(encoding="utf-8", errors="replace")
        else:
            raw_text = str(file_path_or_bytes)

        validation = ValidationResult(is_valid=True, syntax_valid=True)
        warnings: list[str] = []

        try:
            root = ET.fromstring(raw_text)
        except DefusedXmlException as sec_err:
            validation.is_valid = False
            validation.syntax_valid = False
            validation.security_warnings.append(f"Security Alert (DefusedXML): Blocked entity expansion or XXE payload: {sec_err}")
            warnings.append(f"Security restriction: XXE / entity resolution blocked: {sec_err}")
            return StructuredDataDocument(
                document_id=f"struct_{uuid.uuid4().hex[:8]}",
                source_file_id=file_id,
                format="xml",
                root_type="element",
                validation_results=validation,
                warnings=warnings,
                status="error",
                raw_preview=raw_text[:2000],
            )
        except Exception as e:
            validation.is_valid = False
            validation.syntax_valid = False
            validation.schema_errors.append(f"XML Parse Error: {e}")
            return StructuredDataDocument(
                document_id=f"struct_{uuid.uuid4().hex[:8]}",
                source_file_id=file_id,
                format="xml",
                root_type="unknown",
                validation_results=validation,
                warnings=[f"Malformed XML: {e}"],
                status="error",
                raw_preview=raw_text[:2000],
            )

        # Traverse hierarchy and count tags/attributes
        tag_counts: dict[str, int] = {}
        all_attributes: set[str] = set()

        def node_to_dict(elem: Any, current_depth: int = 1) -> tuple[dict[str, Any], int]:
            tag_counts[elem.tag] = tag_counts.get(elem.tag, 0) + 1
            for k in elem.attrib.keys():
                all_attributes.add(k)

            max_d = current_depth
            children_dict: list[dict[str, Any]] = []
            for child in elem:
                c_dict, c_depth = node_to_dict(child, current_depth + 1)
                children_dict.append(c_dict)
                if c_depth > max_d:
                    max_d = c_depth

            node_repr: dict[str, Any] = {
                "tag": elem.tag,
                "attributes": dict(elem.attrib),
                "text": elem.text.strip() if elem.text and elem.text.strip() else None,
            }
            if children_dict:
                node_repr["children"] = children_dict
            return node_repr, max_d

        hierarchy_tree, max_depth = node_to_dict(root)

        # Tabular records extraction if root has repeated child elements
        records: list[dict[str, Any]] = []
        if len(root) > 0 and len({c.tag for c in root}) == 1:
            for child in root[:50]:
                row = dict(child.attrib)
                for sub in child:
                    row[sub.tag] = sub.text.strip() if sub.text else None
                records.append(row)

        col_profiles = [
            ColumnProfile(name=tag, data_type="element", is_unique=False)
            for tag in sorted(tag_counts.keys())
        ]

        data_profile = DataProfile(
            total_rows=sum(tag_counts.values()),
            total_columns=len(tag_counts),
            column_profiles=col_profiles,
        )

        return StructuredDataDocument(
            document_id=f"struct_{uuid.uuid4().hex[:8]}",
            source_file_id=file_id,
            format="xml",
            root_type="element",
            schema_definition={"root": root.tag, "element_counts": tag_counts},
            hierarchy=hierarchy_tree,
            records=records,
            data_profile=data_profile,
            validation_results=validation,
            metadata={
                "root_tag": root.tag,
                "total_elements": sum(tag_counts.values()),
                "distinct_tags": len(tag_counts),
                "max_depth": max_depth,
            },
            model_information=StructuredModelInfo(
                engine_name="documind-xml-v1",
                format_parser="defusedxml.ElementTree",
                is_bounded_memory=True,
                features_used=["xxe_protection", "entity_expansion_blocking", "hierarchy_traversal"],
            ),
            warnings=warnings,
            status="completed",
            raw_preview=raw_text[:2000],
        )
