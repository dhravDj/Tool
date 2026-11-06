"""CSV writer for tabular data with formula injection protection."""

import csv
import io
import re
from typing import Any

from app.modules.converters.schemas import UniversalContent, UniversalTable

_NUMERIC_PATTERN = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


class CsvWriter:
    """Exports tabular data into clean, compliant CSV format with safe formula escaping."""

    @classmethod
    def write(cls, content: UniversalContent, table_index: int = 0) -> str:
        """Export a single table or combine all tables into CSV."""
        if not content.tables:
            # Fallback: if no structured tables exist, create single column CSV from paragraphs
            return cls._paragraphs_to_csv(content.paragraphs)

        if 0 <= table_index < len(content.tables):
            table = content.tables[table_index]
            return cls.write_table(table)

        # If table_index out of bounds or negative, export all tables separated by blank rows
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        for idx, table in enumerate(content.tables):
            if idx > 0:
                writer.writerow([])
            if table.title or table.sheet_name:
                writer.writerow([f"# Table: {table.title or table.sheet_name}"])

            if table.headers:
                writer.writerow([cls.sanitize_cell(h) for h in table.headers])
            for row in table.rows:
                writer.writerow([cls.sanitize_cell(c) for c in row])

        return output.getvalue()

    @classmethod
    def write_table(cls, table: UniversalTable) -> str:
        """Export a single UniversalTable to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        if table.headers:
            writer.writerow([cls.sanitize_cell(h) for h in table.headers])

        for row in table.rows:
            writer.writerow([cls.sanitize_cell(c) for c in row])

        return output.getvalue()

    @classmethod
    def sanitize_cell(cls, val: Any) -> Any:
        """Sanitize cell value against formula injection attacks (CSV injection / DDE).

        CRITICAL REQUIREMENT:
        Prevent spreadsheet formula injection in exported CSV files without corrupting
        legitimate negative numeric values.
        """
        if val is None:
            return ""

        # Direct numbers (int, float) are inherently safe
        if isinstance(val, (int, float)):
            return val

        raw_s = str(val)
        if not raw_s:
            return ""

        # Check if cell starts with dangerous formula execution characters: =, +, -, @, \t, \r
        if raw_s[0] in ("\t", "\r"):
            return f"'{raw_s}"

        s = raw_s.strip()
        if not s:
            return ""

        first_char = s[0]
        if first_char in ("=", "+", "-", "@"):
            # Check if it is a legitimate numeric literal (e.g. -42, -3.14, +100, -1.5e-4)
            if _NUMERIC_PATTERN.match(s):
                try:
                    float(s)
                    # It is a valid numeric value! Keep it untouched without corrupting it.
                    return s
                except (ValueError, TypeError):
                    pass

            # Not a pure numeric literal: dangerous formula injection detected!
            # Prepend single quote (') to force spreadsheet apps to treat as pure text
            return f"'{s}"

        return s

    @classmethod
    def _paragraphs_to_csv(cls, paragraphs: list[str]) -> str:
        """Fallback converter turning paragraphs into a single-column CSV."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(["Extracted Text"])
        for p in paragraphs:
            clean = p.strip()
            if clean:
                writer.writerow([cls.sanitize_cell(clean)])
        return output.getvalue()
