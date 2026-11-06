"""Code adapter converting CodeDocument to UniversalContent without modifying logic."""

from app.modules.code_intelligence.schemas.code_document import CodeDocument
from app.modules.converters.schemas import (
    UniversalCodeBlock,
    UniversalContent,
    UniversalSection,
    UniversalTable,
)


class CodeAdapter:
    """Adapts CodeDocument into standard UniversalContent preserving raw code and symbol hierarchy."""

    @classmethod
    def adapt(cls, doc: CodeDocument, original_filename: str = "") -> UniversalContent:
        filename = original_filename or doc.file_metadata.get("filename") or f"code.{doc.language}"
        raw_code = doc.source_code

        code_blocks: list[UniversalCodeBlock] = [
            UniversalCodeBlock(
                language=doc.language,
                code=raw_code,
                caption=f"Source Code: {filename}",
                line_count=doc.metrics.total_lines or len(raw_code.splitlines()),
            )
        ]

        sections: list[UniversalSection] = [
            UniversalSection(
                title=f"Source Code ({doc.language.upper()})",
                level=2,
                content=f"```{doc.language}\n{raw_code}\n```",
            )
        ]

        # Symbols summary table
        tables: list[UniversalTable] = []
        if doc.symbols:
            symbol_rows = [
                [
                    s.name,
                    s.symbol_type,
                    f"L{s.start_line}-L{s.end_line}",
                    s.visibility,
                    ", ".join(s.parameters) if s.parameters else "",
                    s.return_type or "",
                ]
                for s in doc.symbols
            ]
            tables.append(
                UniversalTable(
                    title="Extracted Symbols",
                    headers=["Symbol Name", "Type", "Lines", "Visibility", "Parameters", "Return Type"],
                    rows=symbol_rows,
                    row_count=len(symbol_rows),
                    col_count=6,
                )
            )

        meta = {
            "language": doc.language,
            "total_lines": doc.metrics.total_lines,
            "code_lines": doc.metrics.code_lines,
            "comment_lines": doc.metrics.comment_lines,
            "blank_lines": doc.metrics.blank_lines,
            "function_count": doc.metrics.function_count,
            "class_count": doc.metrics.class_count,
            "cyclomatic_complexity": doc.metrics.cyclomatic_complexity,
        }

        return UniversalContent(
            source_filename=filename,
            source_format=doc.language,
            title=f"Source Code: {filename}",
            author="",
            page_count=1,
            word_count=len(raw_code.split()),
            paragraphs=[],
            sections=sections,
            tables=tables,
            code_blocks=code_blocks,
            metadata=meta,
            warnings=doc.warnings,
            raw_text=raw_code,
        )
