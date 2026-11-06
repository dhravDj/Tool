"""Formula inspection, classification, dependency mapping, and CSV injection sanitization.

Strict Security Posture:
1. Never executes formulas or VBA macros.
2. Distinguishes formula definition, cached evaluation result, and external references.
3. Sanitizes dangerous formula triggers in exported CSV files.
"""

import re
from typing import Any


class FormulaInspector:
    """Parses and analyzes spreadsheet formulas without execution."""

    SUPPORTED_FUNCTIONS = {
        # Arithmetic / Aggregation
        "SUM", "AVERAGE", "COUNT", "COUNTA", "MIN", "MAX", "ROUND", "ABS", "PRODUCT",
        # Logical
        "IF", "SUMIF", "COUNTIF", "IFERROR", "AND", "OR", "NOT",
        # Lookup & Reference
        "VLOOKUP", "HLOOKUP", "XLOOKUP", "INDEX", "MATCH", "LOOKUP", "CHOOSE", "OFFSET",
        # Text
        "CONCAT", "CONCATENATE", "TEXT", "LEFT", "RIGHT", "MID", "TRIM", "LEN", "UPPER", "LOWER",
        # Date & Time
        "DATE", "TIME", "NOW", "TODAY", "YEAR", "MONTH", "DAY", "DATEDIF",
    }

    # Matches cross-sheet cell references e.g. Sheet1!A1, 'Quarter 1'!$B$12, Sheet2!A1:B10
    CROSS_SHEET_REGEX = re.compile(
        r"(?:'([^']+)'|([A-Za-z0-9_]+))!(\$?[A-Za-z]{1,3}\$?[0-9]+(?::\$?[A-Za-z]{1,3}\$?[0-9]+)?)"
    )

    # Matches local cell references e.g. A1, $B$12, C1:C20
    LOCAL_CELL_REGEX = re.compile(
        r"(?<![A-Za-z0-9_!])(\$?[A-Za-z]{1,3}\$?[0-9]+(?::\$?[A-Za-z]{1,3}\$?[0-9]+)?)(?![A-Za-z0-9_])"
    )

    # Matches external workbook references e.g. [Budget.xlsx]Sheet1!A1
    EXTERNAL_REF_REGEX = re.compile(r"\[([^\]]+)\]")

    @classmethod
    def inspect(cls, formula_str: str, cached_val: Any = None) -> dict[str, Any]:
        """Analyze a formula string and return its classification and referenced cells."""
        raw = formula_str.strip()
        if not raw.startswith("="):
            raw = f"={raw}"

        # Extract function names in formula
        tokens = re.findall(r"\b([A-Za-z][A-Za-z0-9_\.]*)\s*\(", raw)
        functions = [f.upper() for f in tokens]

        # Check for external workbook references
        is_external = bool(cls.EXTERNAL_REF_REGEX.search(raw))

        # Check cross-sheet references
        cross_sheet_refs: list[dict[str, str]] = []
        for match in cls.CROSS_SHEET_REGEX.finditer(raw):
            quoted_sheet, unquoted_sheet, cell_range = match.groups()
            sheet = quoted_sheet or unquoted_sheet
            cross_sheet_refs.append({"sheet": sheet, "range": cell_range})

        # Local references
        # Strip string literals before searching for cell references
        clean_for_refs = re.sub(r'"[^"]*"', '""', raw)
        clean_for_refs = cls.CROSS_SHEET_REGEX.sub("", clean_for_refs)
        local_refs = cls.LOCAL_CELL_REGEX.findall(clean_for_refs)
        unique_local_refs = sorted(set(local_refs))

        # Category classification
        category = "general"
        if any(f in ("VLOOKUP", "HLOOKUP", "XLOOKUP", "INDEX", "MATCH") for f in functions):
            category = "lookup"
        elif any(f in ("IF", "SUMIF", "COUNTIF", "IFERROR") for f in functions):
            category = "conditional"
        elif any(f in ("SUM", "AVERAGE", "COUNT", "COUNTA", "MIN", "MAX") for f in functions):
            category = "math_aggregation"
        elif any(f in ("CONCAT", "CONCATENATE", "TEXT") for f in functions):
            category = "text"
        elif any(f in ("DATE", "TIME", "NOW", "TODAY") for f in functions):
            category = "datetime"
        elif any(op in raw for op in ("+", "-", "*", "/", "^")):
            category = "arithmetic"

        return {
            "formula_text": raw,
            "cached_value": cached_val,
            "has_cached_value": cached_val is not None,
            "functions": functions,
            "category": category,
            "is_external_reference": is_external,
            "cross_sheet_references": cross_sheet_refs,
            "local_references": unique_local_refs,
            "has_unsupported_functions": any(f not in cls.SUPPORTED_FUNCTIONS for f in functions),
        }

    @classmethod
    def sanitize_for_csv_export(cls, val: Any) -> str:
        """Sanitize values for CSV export to prevent formula injection attacks (CSV Injection / DDE).

        Prefixes values starting with '=', '+', '-', '@', '\t', or '\r' with a single quote.
        """
        if val is None:
            return ""

        s = str(val)
        if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{s}"
        return s
