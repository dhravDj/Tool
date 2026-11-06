"""Structured data adapter converting StructuredDataDocument to UniversalContent."""

import json

from app.modules.converters.schemas import (
    UniversalCodeBlock,
    UniversalContent,
    UniversalSection,
    UniversalTable,
)
from app.modules.structured_data_intelligence.schemas.structured_data_document import (
    StructuredDataDocument,
)


class StructuredDataAdapter:
    """Adapts StructuredDataDocument into standard UniversalContent preserving tabular rows and tree structures."""

    @classmethod
    def adapt(cls, doc: StructuredDataDocument, original_filename: str = "") -> UniversalContent:
        filename = original_filename or f"structured_data.{doc.format}"
        tables: list[UniversalTable] = []
        code_blocks: list[UniversalCodeBlock] = []
        sections: list[UniversalSection] = []

        # 1. Tabular records (from Parquet or array of JSON/TOML records)
        if doc.records:
            headers: list[str] = []
            for r in doc.records:
                for k in r.keys():
                    if k not in headers:
                        headers.append(k)

            rows: list[list[str]] = []
            for r in doc.records:
                rows.append([str(r.get(h, "")) if r.get(h) is not None else "" for h in headers])

            tables.append(
                UniversalTable(
                    title=f"Structured Records ({doc.format.upper()})",
                    headers=headers,
                    rows=rows,
                    row_count=len(rows),
                    col_count=len(headers),
                )
            )

        # 2. Hierarchy view as JSON / formatted block
        if doc.hierarchy:
            try:
                formatted_repr = json.dumps(doc.hierarchy, indent=2, ensure_ascii=False)
            except Exception:
                formatted_repr = str(doc.hierarchy)

            code_blocks.append(
                UniversalCodeBlock(
                    language="json",
                    code=formatted_repr,
                    caption=f"Hierarchy Tree ({doc.format.upper()})",
                    line_count=len(formatted_repr.splitlines()),
                )
            )
            sections.append(
                UniversalSection(
                    title=f"Structured Content ({doc.format.upper()})",
                    level=2,
                    content=f"```json\n{formatted_repr}\n```",
                )
            )

        meta = {
            "format": doc.format,
            "root_type": doc.root_type,
            "total_rows": doc.data_profile.total_rows,
            "total_columns": doc.data_profile.total_columns,
            "duplicate_keys": doc.validation_results.duplicate_keys,
            "candidate_keys": doc.data_profile.candidate_keys,
        }

        raw_text = doc.raw_preview or (code_blocks[0].code if code_blocks else "")

        return UniversalContent(
            source_filename=filename,
            source_format=doc.format,
            title=f"Structured Data: {filename}",
            author="",
            page_count=1,
            word_count=len(raw_text.split()),
            paragraphs=[],
            sections=sections,
            tables=tables,
            code_blocks=code_blocks,
            metadata=meta,
            warnings=doc.warnings + doc.validation_results.security_warnings,
            raw_text=raw_text,
        )
