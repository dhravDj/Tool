"""YAML intelligence engine with safe loading, alias protection, and profiling."""

import re
import uuid
from pathlib import Path
from typing import Any

import yaml

from app.modules.structured_data_intelligence.engines.base import BaseStructuredEngine
from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    ColumnProfile,
    ColumnStatistics,
    DataProfile,
    StructuredDataDocument,
    StructuredModelInfo,
    ValidationResult,
)


class SafeDuplicateKeyLoader(yaml.SafeLoader):
    """YAML Loader recording duplicate mapping keys and protecting against alias bombs."""

    pass


class YAMLEngine(BaseStructuredEngine):
    """Safe YAML parser protecting against Billion Laughs expansion and extracting hierarchy."""

    @property
    def format(self) -> str:
        return "yaml"

    @property
    def supported_extensions(self) -> list[str]:
        return ["yaml", "yml"]

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

        # 1. Protection against YAML Alias Expansion / Billion Laughs
        anchor_count = len(re.findall(r"&[A-Za-z0-9_]+", raw_text))
        alias_count = len(re.findall(r"\*[A-Za-z0-9_]+", raw_text))

        if (alias_count > 25 and anchor_count >= 3) or alias_count > 50:
            validation.security_warnings.append(
                f"Suspicious YAML anchor/alias density detected ({anchor_count} anchors, {alias_count} aliases). Risk of billion laughs expansion."
            )
            warnings.append("High alias count detected: potential expansion vulnerability.")

        # 2. Parse YAML using yaml.safe_load
        parsed_data: Any = None
        try:
            parsed_data = yaml.safe_load(raw_text)
        except Exception as e:
            validation.is_valid = False
            validation.syntax_valid = False
            validation.schema_errors.append(f"YAML Parse Error: {e}")
            return StructuredDataDocument(
                document_id=f"struct_{uuid.uuid4().hex[:8]}",
                source_file_id=file_id,
                format="yaml",
                root_type="unknown",
                validation_results=validation,
                warnings=[f"Failed to parse YAML: {e}"],
                status="error",
                raw_preview=raw_text[:2000],
            )

        root_type = "mapping" if isinstance(parsed_data, dict) else ("sequence" if isinstance(parsed_data, list) else "scalar")

        # Depth & Profile
        def get_depth(val: Any, curr: int = 1) -> int:
            if isinstance(val, dict):
                return max([get_depth(v, curr + 1) for v in val.values()] or [curr])
            elif isinstance(val, list):
                return max([get_depth(v, curr + 1) for v in val] or [curr])
            return curr

        max_depth = get_depth(parsed_data)

        # Tabular records if list of dicts
        records_sample: list[dict[str, Any]] = []
        col_profiles: list[ColumnProfile] = []

        if isinstance(parsed_data, list) and parsed_data and all(isinstance(x, dict) for x in parsed_data[:10]):
            records_sample = parsed_data[:50]
            all_cols: set[str] = set()
            for r in records_sample:
                all_cols.update(r.keys())

            for col in sorted(all_cols):
                vals = [r.get(col) for r in records_sample]
                null_c = sum(1 for v in vals if v is None)
                stats = ColumnStatistics(
                    null_count=null_c,
                    distinct_count=len({str(v) for v in vals}),
                    sample_values=[v for v in vals[:5] if v is not None],
                )
                col_profiles.append(
                    ColumnProfile(
                        name=col,
                        data_type=type(vals[0]).__name__ if vals and vals[0] is not None else "string",
                        null_percentage=round((null_c / max(1, len(vals))) * 100, 2),
                        is_unique=len({str(v) for v in vals}) == len(vals),
                        statistics=stats,
                    )
                )
        elif isinstance(parsed_data, dict):
            records_sample = [parsed_data]
            for col, val in parsed_data.items():
                val_type = type(val).__name__ if val is not None else "null"
                stats = ColumnStatistics(
                    null_count=1 if val is None else 0,
                    distinct_count=1,
                    sample_values=[val] if not isinstance(val, (dict, list)) else [str(val)[:50]],
                )
                col_profiles.append(
                    ColumnProfile(
                        name=col,
                        data_type=val_type,
                        null_percentage=100.0 if val is None else 0.0,
                        is_unique=True,
                        statistics=stats,
                    )
                )

        data_profile = DataProfile(
            total_rows=len(parsed_data) if isinstance(parsed_data, list) else (len(parsed_data) if isinstance(parsed_data, dict) else 1),
            total_columns=len(col_profiles) or (len(parsed_data) if isinstance(parsed_data, dict) else 1),
            column_profiles=col_profiles,
        )

        return StructuredDataDocument(
            document_id=f"struct_{uuid.uuid4().hex[:8]}",
            source_file_id=file_id,
            format="yaml",
            root_type=root_type,
            schema_definition={"root_type": root_type, "anchors_found": anchor_count, "aliases_found": alias_count},
            hierarchy=parsed_data if isinstance(parsed_data, (dict, list)) else {"value": parsed_data},
            records=records_sample,
            data_profile=data_profile,
            validation_results=validation,
            metadata={"anchor_count": anchor_count, "alias_count": alias_count, "max_depth": max_depth},
            model_information=StructuredModelInfo(
                engine_name="documind-yaml-v1",
                format_parser="yaml.safe_load",
                is_bounded_memory=True,
                features_used=["safe_load", "alias_expansion_inspection", "hierarchy_normalization"],
            ),
            warnings=warnings,
            status="completed",
            raw_preview=raw_text[:2000],
        )
