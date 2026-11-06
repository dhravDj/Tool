"""TOML configuration and structured document engine using tomllib."""

import tomllib
import uuid
from pathlib import Path
from typing import Any

from app.modules.structured_data_intelligence.engines.base import BaseStructuredEngine
from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    ColumnProfile,
    DataProfile,
    StructuredDataDocument,
    StructuredModelInfo,
    ValidationResult,
)


class TOMLEngine(BaseStructuredEngine):
    """Engine for TOML document parsing, table inspection, and hierarchy extraction."""

    @property
    def format(self) -> str:
        return "toml"

    @property
    def supported_extensions(self) -> list[str]:
        return ["toml"]

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
            parsed_data = tomllib.loads(raw_text)
        except Exception as e:
            validation.is_valid = False
            validation.syntax_valid = False
            validation.schema_errors.append(f"TOML Decode Error: {e}")
            return StructuredDataDocument(
                document_id=f"struct_{uuid.uuid4().hex[:8]}",
                source_file_id=file_id,
                format="toml",
                root_type="table",
                validation_results=validation,
                warnings=[f"Failed to parse TOML: {e}"],
                status="error",
                raw_preview=raw_text[:2000],
            )

        def get_depth(val: Any, curr: int = 1) -> int:
            if isinstance(val, dict):
                return max([get_depth(v, curr + 1) for v in val.values()] or [curr])
            elif isinstance(val, list):
                return max([get_depth(v, curr + 1) for v in val] or [curr])
            return curr

        max_depth = get_depth(parsed_data)

        # Count top-level tables and keys
        table_keys = [k for k, v in parsed_data.items() if isinstance(v, dict)]
        array_keys = [k for k, v in parsed_data.items() if isinstance(v, list)]
        scalar_keys = [k for k, v in parsed_data.items() if not isinstance(v, (dict, list))]

        col_profiles = [
            ColumnProfile(name=k, data_type=type(v).__name__)
            for k, v in parsed_data.items()
        ]

        data_profile = DataProfile(
            total_rows=len(parsed_data),
            total_columns=len(parsed_data),
            column_profiles=col_profiles,
        )

        return StructuredDataDocument(
            document_id=f"struct_{uuid.uuid4().hex[:8]}",
            source_file_id=file_id,
            format="toml",
            root_type="table",
            schema_definition={
                "tables": table_keys,
                "arrays": array_keys,
                "scalars": scalar_keys,
            },
            hierarchy=parsed_data,
            data_profile=data_profile,
            validation_results=validation,
            metadata={
                "table_count": len(table_keys),
                "scalar_property_count": len(scalar_keys),
                "max_depth": max_depth,
            },
            model_information=StructuredModelInfo(
                engine_name="documind-toml-v1",
                format_parser="tomllib",
                is_bounded_memory=True,
                features_used=["native_tomllib_parsing", "table_hierarchy_extraction"],
            ),
            warnings=warnings,
            status="completed",
            raw_preview=raw_text[:2000],
        )
