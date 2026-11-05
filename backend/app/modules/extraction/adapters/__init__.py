"""Document extraction adapters package."""

from app.modules.extraction.adapters.base import (
    BaseDocumentExtractor,
    CorruptedDocumentError,
    ExtractionError,
    PageLimitExceededError,
    PasswordRequiredError,
    UnsupportedFormatError,
)
from app.modules.extraction.adapters.doc import LegacyDocExtractor
from app.modules.extraction.adapters.docx import DocxExtractor
from app.modules.extraction.adapters.epub import EPUBExtractor
from app.modules.extraction.adapters.markdown import MarkdownExtractor
from app.modules.extraction.adapters.odt import ODTExtractor
from app.modules.extraction.adapters.pdf import PDFExtractor
from app.modules.extraction.adapters.rtf import RTFExtractor
from app.modules.extraction.adapters.text import PlainTextExtractor

__all__ = [
    "BaseDocumentExtractor",
    "ExtractionError",
    "PasswordRequiredError",
    "CorruptedDocumentError",
    "UnsupportedFormatError",
    "PageLimitExceededError",
    "PDFExtractor",
    "DocxExtractor",
    "LegacyDocExtractor",
    "PlainTextExtractor",
    "MarkdownExtractor",
    "RTFExtractor",
    "ODTExtractor",
    "EPUBExtractor",
]
