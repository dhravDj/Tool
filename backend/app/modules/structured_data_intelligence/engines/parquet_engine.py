"""Apache Parquet columnar inspection and bounded data profiling engine using PyArrow."""

import io
import uuid
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from app.modules.structured_data_intelligence.engines.base import BaseStructuredEngine
from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    ColumnProfile,
    ColumnStatistics,
    DataProfile,
    StructuredDataDocument,
    StructuredModelInfo,
    ValidationResult,
)


class ParquetEngine(BaseStructuredEngine):
    """Engine for Apache Parquet metadata extraction, schema inspection, and bounded column profiling."""

    @property
    def format(self) -> str:
        return "parquet"

    @property
    def supported_extensions(self) -> list[str]:
        return ["parquet", "pq"]

    def analyze(
        self,
        file_path_or_bytes: Path | str | bytes,
        file_id: str,
        filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> StructuredDataDocument:
        validation = ValidationResult(is_valid=True, syntax_valid=True)
        warnings: list[str] = []

        try:
            if isinstance(file_path_or_bytes, bytes):
                source_input: Any = io.BytesIO(file_path_or_bytes)
            elif isinstance(file_path_or_bytes, (str, Path)):
                source_input = str(file_path_or_bytes)
            else:
                source_input = file_path_or_bytes

            pf = pq.ParquetFile(source_input)
        except Exception as e:
            validation.is_valid = False
            validation.syntax_valid = False
            validation.schema_errors.append(f"Parquet Read Error: {e}")
            return StructuredDataDocument(
                document_id=f"struct_{uuid.uuid4().hex[:8]}",
                source_file_id=file_id,
                format="parquet",
                root_type="table",
                validation_results=validation,
                warnings=[f"Failed to open Parquet dataset: {e}"],
                status="error",
                raw_preview="[Binary Parquet Data - Malformed or Corrupted]",
            )

        metadata = pf.metadata
        num_rows = metadata.num_rows
        num_row_groups = metadata.num_row_groups
        schema = pf.schema_arrow

        # Column stats aggregation across row groups
        col_profiles: list[ColumnProfile] = []
        candidate_keys: list[str] = []
        schema_dict: dict[str, str] = {}

        # Sample up to 50 rows using bounded batch iterator
        sample_records: list[dict[str, Any]] = []
        try:
            if num_rows > 0:
                first_batch = next(pf.iter_batches(batch_size=50))
                sample_records = first_batch.to_pylist()
        except Exception as sample_err:
            warnings.append(f"Could not read sample batch: {sample_err}")

        for i, field in enumerate(schema):
            col_name = field.name
            arrow_type = str(field.type)
            schema_dict[col_name] = arrow_type

            # Aggregate metadata statistics
            total_nulls = 0
            min_val = None
            max_val = None

            for rg_idx in range(num_row_groups):
                rg = metadata.row_group(rg_idx)
                col_chunk = rg.column(i)
                if col_chunk.is_stats_set and col_chunk.statistics:
                    st = col_chunk.statistics
                    total_nulls += st.null_count or 0
                    if min_val is None or (st.min is not None and st.min < min_val):
                        min_val = st.min
                    if max_val is None or (st.max is not None and st.max > max_val):
                        max_val = st.max

            # Check uniqueness in sample
            sample_col_vals = [r.get(col_name) for r in sample_records]
            is_unique = (
                len({str(v) for v in sample_col_vals if v is not None}) == len(sample_col_vals)
                and total_nulls == 0
                and len(sample_col_vals) > 0
            )
            if is_unique and col_name.lower() in ("id", "uuid", "key", f"{col_name}_id"):
                candidate_keys.append(col_name)

            stats = ColumnStatistics(
                min_value=str(min_val) if min_val is not None else None,
                max_value=str(max_val) if max_val is not None else None,
                null_count=total_nulls,
                distinct_count=len({str(v) for v in sample_col_vals}),
                sample_values=[v for v in sample_col_vals[:5] if v is not None],
            )

            col_profiles.append(
                ColumnProfile(
                    name=col_name,
                    data_type=arrow_type,
                    physical_type=field.type.__class__.__name__,
                    null_percentage=round((total_nulls / max(1, num_rows)) * 100, 2),
                    is_unique=is_unique,
                    is_candidate_key=is_unique,
                    statistics=stats,
                )
            )

        data_profile = DataProfile(
            total_rows=num_rows,
            total_columns=len(schema),
            candidate_keys=candidate_keys,
            missing_cells_ratio=round(sum(c.statistics.null_count for c in col_profiles) / max(1, num_rows * len(schema)), 4),
            column_profiles=col_profiles,
        )

        return StructuredDataDocument(
            document_id=f"struct_{uuid.uuid4().hex[:8]}",
            source_file_id=file_id,
            format="parquet",
            root_type="table",
            schema_definition={"columns": schema_dict, "num_columns": len(schema)},
            hierarchy={"row_groups": num_row_groups, "columns": [c.name for c in col_profiles]},
            records=sample_records,
            data_profile=data_profile,
            validation_results=validation,
            metadata={
                "row_count": num_rows,
                "row_group_count": num_row_groups,
                "column_count": len(schema),
                "created_by": metadata.created_by or "unknown",
            },
            model_information=StructuredModelInfo(
                engine_name="documind-parquet-v1",
                format_parser="pyarrow.parquet.ParquetFile",
                is_bounded_memory=True,
                features_used=["metadata_projection", "zero_dataframe_streaming", "bounded_batch_profiling"],
            ),
            warnings=warnings,
            status="completed",
            raw_preview=f"[Apache Parquet Columnar Dataset: {num_rows} rows, {len(schema)} columns, {num_row_groups} row groups]",
        )
