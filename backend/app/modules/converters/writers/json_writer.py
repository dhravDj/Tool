"""JSON writer for universal content extraction."""

import json

from app.modules.converters.schemas import UniversalContent


class JsonWriter:
    """Serializes UniversalContent into structured JSON format."""

    @classmethod
    def write(cls, content: UniversalContent, indent: int = 2) -> str:
        data = {
            "version": "2.0.0",
            "document": {
                "source_filename": content.source_filename,
                "source_format": content.source_format,
                "title": content.title,
                "author": content.author,
                "page_count": content.page_count,
                "word_count": content.word_count,
                "metadata": content.metadata,
                "warnings": content.warnings,
            },
            "content": {
                "sections": [s.model_dump() for s in content.sections],
                "paragraphs": content.paragraphs,
                "tables": [t.model_dump() for t in content.tables],
                "code_blocks": [c.model_dump() for c in content.code_blocks],
                "transcript_segments": [ts.model_dump() for ts in content.transcript_segments],
                "raw_text_length": len(content.raw_text),
            },
        }
        return json.dumps(data, indent=indent, ensure_ascii=False)
