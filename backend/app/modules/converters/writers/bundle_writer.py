"""Mode C Complete Extraction Bundle Writer generating self-contained ZIP packages."""

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from app.modules.converters.schemas import UniversalContent
from app.modules.converters.writers.csv_writer import CsvWriter
from app.modules.converters.writers.html_writer import HtmlWriter
from app.modules.converters.writers.json_writer import JsonWriter
from app.modules.converters.writers.markdown_writer import MarkdownWriter
from app.modules.converters.writers.srt_vtt_writer import SubtitleWriter
from app.modules.converters.writers.txt_writer import TxtWriter


class BundleWriter:
    """Packages all extracted representations into an organized ZIP archive (Mode C)."""

    @classmethod
    def write_zip(cls, content: UniversalContent, output_path: Path) -> int:
        """Create a complete ZIP package containing all output formats and table CSVs."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        base_name = Path(content.source_filename).stem or "extracted_document"

        manifest_data = {
            "platform": "DocuMind Universal File Converter",
            "version": "2.0.0",
            "source_filename": content.source_filename,
            "source_format": content.source_format,
            "title": content.title,
            "author": content.author,
            "page_count": content.page_count,
            "word_count": content.word_count,
            "tables_extracted": len(content.tables),
            "code_blocks_extracted": len(content.code_blocks),
            "transcript_segments_extracted": len(content.transcript_segments),
            "warnings": content.warnings,
            "generated_at": datetime.now(UTC).isoformat(),
            "manifest_files": [
                f"{base_name}.txt",
                f"{base_name}.md",
                f"{base_name}.json",
                f"{base_name}.html",
                "metadata.json",
                "manifest.json",
            ],
        }

        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 1. Plain Text (.txt)
            txt_str = TxtWriter.write(content)
            zf.writestr(f"{base_name}.txt", txt_str.encode("utf-8"))

            # 2. Markdown (.md)
            md_str = MarkdownWriter.write(content)
            zf.writestr(f"{base_name}.md", md_str.encode("utf-8"))

            # 3. Structured JSON (.json)
            json_str = JsonWriter.write(content)
            zf.writestr(f"{base_name}.json", json_str.encode("utf-8"))

            # 4. Clean HTML (.html)
            html_str = HtmlWriter.write(content)
            zf.writestr(f"{base_name}.html", html_str.encode("utf-8"))

            # 5. Metadata (.json)
            metadata_str = json.dumps(content.metadata, indent=2, ensure_ascii=False)
            zf.writestr("metadata.json", metadata_str.encode("utf-8"))

            # 6. Extracted Tables (individual CSVs)
            if content.tables:
                for idx, tbl in enumerate(content.tables, start=1):
                    tbl_name = tbl.title or tbl.sheet_name or f"table_{idx}"
                    # Sanitize filename
                    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in tbl_name)
                    csv_str = CsvWriter.write_table(tbl)
                    table_path = f"tables/{safe_name}_{idx}.csv"
                    zf.writestr(table_path, csv_str.encode("utf-8"))
                    manifest_data["manifest_files"].append(table_path)

            # 7. Subtitles (if transcript segments exist)
            if content.transcript_segments:
                srt_str = SubtitleWriter.write_srt(content)
                vtt_str = SubtitleWriter.write_vtt(content)
                zf.writestr("subtitles/transcript.srt", srt_str.encode("utf-8"))
                zf.writestr("subtitles/transcript.vtt", vtt_str.encode("utf-8"))
                manifest_data["manifest_files"].append("subtitles/transcript.srt")
                manifest_data["manifest_files"].append("subtitles/transcript.vtt")

            # 8. Manifest (.json)
            zf.writestr("manifest.json", json.dumps(manifest_data, indent=2).encode("utf-8"))

        return output_path.stat().st_size
