"""Data Understanding and Tabular Profiling Engine for DocuMind AI.

Computes column data types, statistical distributions, candidate primary keys,
duplicate row counts, and data quality insights without mutating source data.
"""

import math
import re
from collections import Counter
from datetime import date, datetime
from typing import Any

from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    ColumnProfiling,
    WorksheetProfiling,
)


class DataUnderstandingProfiler:
    """Profiles extracted worksheet rows and columns with statistical metrics."""

    CURRENCY_REGEX = re.compile(r"^[\$€£¥₹]\s*[-+]?[0-9,]+(?:\.[0-9]+)?$")
    PERCENTAGE_REGEX = re.compile(r"^[-+]?[0-9]+(?:\.[0-9]+)?%$")
    DATE_REGEX = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?$")

    @classmethod
    def profile_worksheet(
        cls,
        grid_data: list[list[Any]],
        column_names: list[str] | None = None,
        max_sample_rows: int = 10_000,
    ) -> WorksheetProfiling:
        """Analyze a tabular matrix of rows and columns and return comprehensive profiling."""
        if not grid_data:
            return WorksheetProfiling()

        total_rows = len(grid_data)
        total_cols = max(len(row) for row in grid_data) if grid_data else 0

        # Subsample for statistical profiling if row count exceeds max_sample_rows
        sampled_rows = grid_data[:max_sample_rows]

        # Duplicate row check (based on string representation of row contents)
        row_hashes = set()
        duplicate_count = 0
        empty_rows_count = 0

        for row in sampled_rows:
            is_empty = all(c is None or str(c).strip() == "" for c in row)
            if is_empty:
                empty_rows_count += 1
            else:
                row_tuple = tuple(str(c).strip() if c is not None else "" for c in row)
                if row_tuple in row_hashes:
                    duplicate_count += 1
                else:
                    row_hashes.add(row_tuple)

        # Scale duplicate count if sampled
        if total_rows > max_sample_rows:
            scale_factor = total_rows / float(max_sample_rows)
            duplicate_count = int(duplicate_count * scale_factor)
            empty_rows_count = int(empty_rows_count * scale_factor)

        # Profile each column
        column_profiles: list[ColumnProfiling] = []
        candidate_primary_keys: list[str] = []
        populated_cells = 0

        for col_idx in range(total_cols):
            col_letter = cls._get_column_letter(col_idx + 1)
            col_name = column_names[col_idx] if column_names and col_idx < len(column_names) else f"Column {col_letter}"

            values = [row[col_idx] if col_idx < len(row) else None for row in grid_data]
            non_null_values = [v for v in values if v is not None and str(v).strip() != ""]
            populated_cells += len(non_null_values)

            null_count = total_rows - len(non_null_values)
            unique_count = len({str(v) for v in non_null_values})

            # Infer data type
            inferred_type = cls._infer_column_type(non_null_values)

            # Compute statistics for numeric / general values
            min_val: Any = None
            max_val: Any = None
            mean_val: float | None = None
            median_val: float | None = None
            std_dev_val: float | None = None

            if inferred_type in ("integer", "float", "number"):
                num_vals = []
                for v in non_null_values:
                    try:
                        num_vals.append(float(v))
                    except (ValueError, TypeError):
                        pass

                if num_vals:
                    num_vals.sort()
                    min_val = num_vals[0]
                    max_val = num_vals[-1]
                    mean_val = round(sum(num_vals) / len(num_vals), 4)

                    mid = len(num_vals) // 2
                    if len(num_vals) % 2 == 0:
                        median_val = round((num_vals[mid - 1] + num_vals[mid]) / 2.0, 4)
                    else:
                        median_val = round(num_vals[mid], 4)

                    if len(num_vals) > 1:
                        variance = sum((x - mean_val) ** 2 for x in num_vals) / (len(num_vals) - 1)
                        std_dev_val = round(math.sqrt(variance), 4)
            elif non_null_values:
                # String / date min and max
                str_vals = sorted(str(v) for v in non_null_values[:1000])
                if str_vals:
                    min_val = str_vals[0][:50]
                    max_val = str_vals[-1][:50]

            # Frequent values
            freq_counter = Counter(str(v)[:50] for v in non_null_values[:2000])
            top_frequent = [{"value": k, "count": count} for k, count in freq_counter.most_common(5)]

            # Candidate primary key check: 0 nulls, 100% unique, non-empty, and > 1 row
            is_pk = (null_count == 0 and unique_count == total_rows and total_rows > 1)
            if is_pk:
                candidate_primary_keys.append(col_name)

            column_profiles.append(
                ColumnProfiling(
                    column_index=col_idx + 1,
                    column_letter=col_letter,
                    column_name=col_name,
                    inferred_type=inferred_type,
                    total_count=total_rows,
                    null_count=null_count,
                    unique_count=unique_count,
                    min_value=min_val,
                    max_value=max_val,
                    mean=mean_val,
                    median=median_val,
                    std_dev=std_dev_val,
                    is_candidate_key=is_pk,
                    frequent_values=top_frequent,
                )
            )

        return WorksheetProfiling(
            total_rows=total_rows,
            total_columns=total_cols,
            populated_cells=populated_cells,
            empty_rows_count=empty_rows_count,
            duplicate_rows_count=duplicate_count,
            candidate_primary_keys=candidate_primary_keys,
            column_profiles=column_profiles,
        )

    @classmethod
    def _infer_column_type(cls, values: list[Any]) -> str:
        """Determine predominant semantic type of non-null values."""
        if not values:
            return "empty"

        sample = values[:200]
        type_counts: Counter[str] = Counter()

        for val in sample:
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                type_counts["number"] += 1
            elif isinstance(val, bool):
                type_counts["boolean"] += 1
            elif isinstance(val, (datetime, date)):
                type_counts["datetime"] += 1
            else:
                s = str(val).strip()
                if cls.CURRENCY_REGEX.match(s):
                    type_counts["currency"] += 1
                elif cls.PERCENTAGE_REGEX.match(s):
                    type_counts["percentage"] += 1
                elif cls.DATE_REGEX.match(s):
                    type_counts["datetime"] += 1
                elif s.lower() in ("true", "false", "yes", "no"):
                    type_counts["boolean"] += 1
                else:
                    try:
                        int(s)
                        type_counts["number"] += 1
                    except ValueError:
                        try:
                            float(s)
                            type_counts["number"] += 1
                        except ValueError:
                            type_counts["text"] += 1

        predominant, _ = type_counts.most_common(1)[0]
        return predominant

    @staticmethod
    def _get_column_letter(col_idx: int) -> str:
        """Convert 1-based integer to Excel column letter (1 -> 'A', 28 -> 'AB')."""
        result = []
        n = col_idx
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result.append(chr(65 + remainder))
        return "".join(reversed(result))
