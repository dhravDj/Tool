"""JSON intelligence engine with duplicate key detection, schema inference, and data profiling."""

import json
import uuid
from pathlib import Path
from typing import Any

from app.modules.structured_data_intelligence.engines.base import BaseStructuredEngine
from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    ColumnProfile,
    ColumnStatistics,
    DataProfile,
    StructuredDataDocument,
    StructuredModelInfo,
    ValidationResult,
)


class JSONEngine(BaseStructuredEngine):
    """Engine for JSON structural validation, duplicate key discovery, schema inference, and profiling."""

    @property
    def format(self) -> str:
        return "json"

    @property
    def supported_extensions(self) -> list[str]:
        return ["json"]

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

        duplicate_keys: list[str] = []

        def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            res: dict[str, Any] = {}
            for k, v in pairs:
                if k in res:
                    duplicate_keys.append(k)
                res[k] = v
            return res

        validation = ValidationResult(is_valid=True, syntax_valid=True)
        parsed_data: Any = None
        warnings: list[str] = []

        try:
            parsed_data = json.loads(raw_text, object_pairs_hook=pairs_hook)
        except Exception as e:
            validation.is_valid = False
            validation.syntax_valid = False
            validation.schema_errors.append(f"JSON Decode Error: {e}")
            return StructuredDataDocument(
                document_id=f"struct_{uuid.uuid4().hex[:8]}",
                source_file_id=file_id,
                format="json",
                root_type="unknown",
                validation_results=validation,
                warnings=[f"Failed to parse JSON: {e}"],
                status="error",
                raw_preview=raw_text[:2000],
            )

        if duplicate_keys:
            validation.duplicate_keys = sorted(set(duplicate_keys))
            warnings.append(f"Found {len(validation.duplicate_keys)} duplicate key(s) in JSON mapping: {validation.duplicate_keys}")

        # Compute max depth and root type
        def get_depth(val: Any, curr: int = 1) -> int:
            if isinstance(val, dict):
                return max([get_depth(v, curr + 1) for v in val.values()] or [curr])
            elif isinstance(val, list):
                return max([get_depth(v, curr + 1) for v in val] or [curr])
            return curr

        max_depth = get_depth(parsed_data)
        root_type = "array" if isinstance(parsed_data, list) else ("object" if isinstance(parsed_data, dict) else "scalar")

        # Schema Inference
        def infer_schema(val: Any) -> dict[str, Any]:
            if isinstance(val, dict):
                props = {k: infer_schema(v) for k, v in val.items()}
                return {"type": "object", "properties": props, "required": list(val.keys())}
            elif isinstance(val, list):
                if not val:
                    return {"type": "array", "items": {}}
                sample_item = infer_schema(val[0])
                return {"type": "array", "items": sample_item}
            elif isinstance(val, bool):
                return {"type": "boolean"}
            elif isinstance(val, int):
                return {"type": "integer"}
            elif isinstance(val, float):
                return {"type": "number"}
            elif isinstance(val, str):
                return {"type": "string"}
            elif val is None:
                return {"type": "null"}
            return {"type": "any"}

        schema_def = infer_schema(parsed_data)

        # Tabular records extraction if array of dicts
        records_sample: list[dict[str, Any]] = []
        col_profiles: list[ColumnProfile] = []
        candidate_keys: list[str] = []
        total_rows = 0

        if isinstance(parsed_data, list) and parsed_data and all(isinstance(x, dict) for x in parsed_data[:10]):
            total_rows = len(parsed_data)
            records_sample = parsed_data[:50]
            # Gather all columns across sample
            all_cols: set[str] = set()
            for r in records_sample:
                all_cols.update(r.keys())

            for col in sorted(all_cols):
                vals = [r.get(col) for r in records_sample]
                null_c = sum(1 for v in vals if v is None)
                distinct_vals = {str(v) for v in vals if v is not None}
                is_unique = (null_c == 0) and (len(distinct_vals) == len(vals)) and len(vals) > 0
                if is_unique and col.lower() in ("id", "uuid", "key", f"{filename.split('.')[0]}_id"):
                    candidate_keys.append(col)

                stats = ColumnStatistics(
                    null_count=null_c,
                    distinct_count=len(distinct_vals),
                    sample_values=[v for v in vals[:5] if v is not None],
                )
                col_profiles.append(
                    ColumnProfile(
                        name=col,
                        data_type=type(vals[0]).__name__ if vals and vals[0] is not None else "string",
                        null_percentage=round((null_c / max(1, len(vals))) * 100, 2),
                        is_unique=is_unique,
                        is_candidate_key=is_unique,
                        statistics=stats,
                    )
                )
        elif isinstance(parsed_data, dict):
            total_rows = 1
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
            total_rows=total_rows or (1 if isinstance(parsed_data, dict) else len(parsed_data) if isinstance(parsed_data, list) else 0),
            total_columns=len(col_profiles) or (len(parsed_data) if isinstance(parsed_data, dict) else 0),
            candidate_keys=candidate_keys,
            column_profiles=col_profiles,
        )

        return StructuredDataDocument(
            document_id=f"struct_{uuid.uuid4().hex[:8]}",
            source_file_id=file_id,
            format="json",
            root_type=root_type,
            schema_definition=schema_def,
            hierarchy=parsed_data if isinstance(parsed_data, (dict, list)) else {"value": parsed_data},
            records=records_sample,
            data_profile=data_profile,
            validation_results=validation,
            metadata={"character_length": len(raw_text), "max_depth": max_depth},
            model_information=StructuredModelInfo(
                engine_name="documind-json-v1",
                format_parser="json.loads+pairs_hook",
                is_bounded_memory=True,
                features_used=["duplicate_key_detection", "schema_inference", "data_profiling"],
            ),
            warnings=warnings,
            status="completed",
            raw_preview=raw_text[:2000],
        )
