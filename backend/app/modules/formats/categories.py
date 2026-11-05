"""File format categories for DocuMind AI."""

from enum import StrEnum


class FormatCategory(StrEnum):
    """Broad functional categories for all file formats."""

    DOCUMENT = "document"
    PDF = "pdf"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    CODE = "code"
    STRUCTURED_DATA = "structured_data"
    EMAIL = "email"
    EBOOK = "ebook"
    FONT = "font"
    EXECUTABLE = "executable"
    DISK_IMAGE = "disk_image"
    OTHER_BINARY = "other_binary"
    UNKNOWN = "unknown"
