"""Step 6: Text format heuristics and structured syntax analysis."""

import json
import re
import tomllib  # Python 3.11+ standard library
from dataclasses import dataclass
from pathlib import Path

from app.modules.formats.format_definitions import FileFormatDefinition
from app.modules.formats.registry import format_registry

# Byte Order Marks (BOM)
BOM_MAP = {
    b"\xef\xbb\xbf": "utf-8-sig",
    b"\xff\xfe\x00\x00": "utf-32-le",
    b"\x00\x00\xfe\xff": "utf-32-be",
    b"\xff\xfe": "utf-16-le",
    b"\xfe\xff": "utf-16-be",
}

MAX_TEXT_INSPECT_BYTES = 32768  # 32 KB sample


@dataclass
class TextDetectionResult:
    """Outcome of text encoding and structural heuristic analysis."""

    is_text: bool
    encoding: str | None = None
    has_bom: bool = False
    detected_format: FileFormatDefinition | None = None
    confidence: float = 0.0
    structure_type: str | None = None  # "json", "xml", "csv", "yaml", "toml", "code", "plain"


class TextDetector:
    """Safely analyzes text encodings and parses structured data syntax without executing code."""

    @classmethod
    def analyze_text(
        cls,
        file_path: Path,
        extension_hint: str | None = None,
    ) -> TextDetectionResult:
        try:
            with open(file_path, "rb") as f:
                raw_sample = f.read(MAX_TEXT_INSPECT_BYTES)
        except Exception:
            return TextDetectionResult(is_text=False)

        if not raw_sample:
            return TextDetectionResult(is_text=False)

        # 1. Check for binary null bytes heuristic (unless UTF-16)
        has_bom = False
        encoding = "utf-8"

        for bom_bytes, bom_enc in BOM_MAP.items():
            if raw_sample.startswith(bom_bytes):
                has_bom = True
                encoding = bom_enc
                raw_sample = raw_sample[len(bom_bytes) :]
                break

        # Decode sample
        text_content: str | None = None
        if has_bom:
            try:
                text_content = raw_sample.decode(encoding)
            except Exception:
                pass
        else:
            # Check for binary control bytes (< 32, excluding \t, \n, \r)
            control_chars = [b for b in raw_sample if b < 32 and b not in (9, 10, 13)]
            if len(control_chars) / len(raw_sample) > 0.02:
                return TextDetectionResult(is_text=False)

            # Try UTF-8 first
            try:
                text_content = raw_sample.decode("utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                # Try Latin-1 or ASCII if null bytes are negligible
                null_ratio = raw_sample.count(b"\x00") / len(raw_sample)
                if null_ratio > 0.01:
                    return TextDetectionResult(is_text=False)
                try:
                    text_content = raw_sample.decode("latin-1")
                    encoding = "latin-1"
                except Exception:
                    return TextDetectionResult(is_text=False)

        if text_content is None:
            return TextDetectionResult(is_text=False)

        stripped = text_content.strip()
        if not stripped:
            return TextDetectionResult(
                is_text=True,
                encoding=encoding,
                has_bom=has_bom,
                detected_format=format_registry.get_by_id("txt"),
                confidence=0.5,
                structure_type="plain",
            )

        # 2. JSON Validation
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            try:
                json.loads(stripped)
                return TextDetectionResult(
                    is_text=True,
                    encoding=encoding,
                    has_bom=has_bom,
                    detected_format=format_registry.get_by_id("json"),
                    confidence=0.95,
                    structure_type="json",
                )
            except Exception:
                pass

        # 3. XML / HTML / SVG
        if (
            stripped.startswith("<?xml")
            or stripped.startswith("<!DOCTYPE")
            or stripped.startswith("<html")
        ):
            if "<svg" in stripped.lower():
                return TextDetectionResult(
                    is_text=True,
                    encoding=encoding,
                    has_bom=has_bom,
                    detected_format=format_registry.get_by_id("svg"),
                    confidence=0.92,
                    structure_type="svg",
                )
            if "<html" in stripped.lower():
                return TextDetectionResult(
                    is_text=True,
                    encoding=encoding,
                    has_bom=has_bom,
                    detected_format=format_registry.get_by_id("html"),
                    confidence=0.90,
                    structure_type="html",
                )
            return TextDetectionResult(
                is_text=True,
                encoding=encoding,
                has_bom=has_bom,
                detected_format=format_registry.get_by_id("xml"),
                confidence=0.90,
                structure_type="xml",
            )

        # 4. TOML Validation
        if extension_hint in ("toml", "ini") or ("[" in stripped and "=" in stripped):
            try:
                tomllib.loads(stripped)
                return TextDetectionResult(
                    is_text=True,
                    encoding=encoding,
                    has_bom=has_bom,
                    detected_format=format_registry.get_by_id("toml"),
                    confidence=0.88,
                    structure_type="toml",
                )
            except Exception:
                pass

        # 5. CSV / TSV Heuristics
        lines = [line.strip() for line in stripped.splitlines() if line.strip()][:20]
        if len(lines) >= 2:
            # Check for TSV
            tab_counts = [line.count("\t") for line in lines]
            if tab_counts[0] > 0 and len(set(tab_counts)) == 1:
                return TextDetectionResult(
                    is_text=True,
                    encoding=encoding,
                    has_bom=has_bom,
                    detected_format=format_registry.get_by_id("tsv"),
                    confidence=0.85,
                    structure_type="tsv",
                )

            # Check for CSV
            comma_counts = [line.count(",") for line in lines]
            if comma_counts[0] > 0 and len(set(comma_counts)) == 1:
                return TextDetectionResult(
                    is_text=True,
                    encoding=encoding,
                    has_bom=has_bom,
                    detected_format=format_registry.get_by_id("csv"),
                    confidence=0.85,
                    structure_type="csv",
                )

        # 6. SQL Syntax Check
        sql_keywords = re.findall(
            r"\b(SELECT|INSERT INTO|CREATE TABLE|UPDATE|DELETE FROM|ALTER TABLE|DROP TABLE)\b",
            stripped,
            re.IGNORECASE,
        )
        if len(sql_keywords) >= 2 or (len(sql_keywords) >= 1 and extension_hint == "sql"):
            return TextDetectionResult(
                is_text=True,
                encoding=encoding,
                has_bom=has_bom,
                detected_format=format_registry.get_by_id("sql"),
                confidence=0.80,
                structure_type="sql",
            )

        # 7. Programming Language Markers
        if extension_hint == "py" or "def " in stripped or "import " in stripped:
            if re.search(r"^\s*(def|class|import|from\s+\w+\s+import)\b", stripped, re.MULTILINE):
                return TextDetectionResult(
                    is_text=True,
                    encoding=encoding,
                    has_bom=has_bom,
                    detected_format=format_registry.get_by_id("py"),
                    confidence=0.80,
                    structure_type="python",
                )

        if extension_hint in ("js", "ts", "jsx", "tsx"):
            if re.search(r"\b(const|let|var|function|export default|import\s+.*?from)\b", stripped):
                fmt_id = "ts" if extension_hint in ("ts", "tsx") else "js"
                return TextDetectionResult(
                    is_text=True,
                    encoding=encoding,
                    has_bom=has_bom,
                    detected_format=format_registry.get_by_id(fmt_id),
                    confidence=0.80,
                    structure_type="javascript",
                )

        # 8. Markdown
        if (
            stripped.startswith("# ")
            or stripped.startswith("## ")
            or extension_hint in ("md", "markdown")
        ):
            md_format = format_registry.get_by_id("md")
            return TextDetectionResult(
                is_text=True,
                encoding=encoding,
                has_bom=has_bom,
                detected_format=md_format or format_registry.get_by_id("txt"),
                confidence=0.85 if extension_hint in ("md", "markdown") else 0.75,
                structure_type="markdown",
            )

        # Default Plain Text
        return TextDetectionResult(
            is_text=True,
            encoding=encoding,
            has_bom=has_bom,
            detected_format=format_registry.get_by_id("txt"),
            confidence=0.70,
            structure_type="plain",
        )
