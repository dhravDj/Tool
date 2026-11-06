"""Central format registry storing definitions, categories, and signature mappings."""

from app.modules.formats.categories import FormatCategory
from app.modules.formats.format_definitions import FileFormatDefinition
from app.modules.formats.signatures import (
    AAC_ADTS_SIGNATURE,
    BMP_SIGNATURE,
    BZIP2_SIGNATURE,
    EBML_SIGNATURE,
    ELF_SIGNATURE,
    FLAC_SIGNATURE,
    GIF87_SIGNATURE,
    GIF89_SIGNATURE,
    GZIP_SIGNATURE,
    JPEG_SIGNATURE,
    MACHO_32_BE,
    MACHO_32_LE,
    MACHO_64_BE,
    MACHO_64_LE,
    MP3_ID3_SIGNATURE,
    MP3_SYNC_SIGNATURE,
    MP4_FTYP_SIGNATURE,
    OGG_SIGNATURE,
    OLE2_SIGNATURE,
    OTF_SIGNATURE,
    PDF_SIGNATURE,
    PE_MZ_SIGNATURE,
    PNG_SIGNATURE,
    RAR_V4_SIGNATURE,
    RAR_V5_SIGNATURE,
    RTF_SIGNATURE,
    SEVEN_ZIP_SIGNATURE,
    TAR_USTAR_SIGNATURE,
    TIFF_BE_SIGNATURE,
    TIFF_LE_SIGNATURE,
    TTF_SIGNATURE,
    WEBP_RIFF,
    WOFF2_SIGNATURE,
    WOFF_SIGNATURE,
    XZ_SIGNATURE,
    ZIP_EMPTY_SIGNATURE,
    ZIP_LOCAL_SIGNATURE,
    ZIP_SPANNED_SIGNATURE,
)
from app.modules.formats.support_status import SupportStatus


class FormatRegistry:
    """Central repository of all recognized file formats, categories, and signatures."""

    def __init__(self) -> None:
        self._formats_by_id: dict[str, FileFormatDefinition] = {}
        self._formats_by_ext: dict[str, list[FileFormatDefinition]] = {}
        self._formats_by_mime: dict[str, list[FileFormatDefinition]] = {}
        self._formats_by_cat: dict[FormatCategory, list[FileFormatDefinition]] = {}
        self._register_default_formats()

    def register(self, definition: FileFormatDefinition) -> None:
        """Register a format specification into index tables."""
        fid = definition.format_id.lower()
        self._formats_by_id[fid] = definition

        # Extension index
        for ext in definition.extensions:
            clean_ext = ext.lower().lstrip(".")
            self._formats_by_ext.setdefault(clean_ext, []).append(definition)

        # MIME index
        for mime in definition.mime_types:
            clean_mime = mime.lower().strip()
            self._formats_by_mime.setdefault(clean_mime, []).append(definition)

        # Category index
        self._formats_by_cat.setdefault(definition.category, []).append(definition)

    def get_by_id(self, format_id: str) -> FileFormatDefinition | None:
        return self._formats_by_id.get(format_id.lower())

    def get_by_extension(self, ext: str) -> list[FileFormatDefinition]:
        return self._formats_by_ext.get(ext.lower().lstrip("."), [])

    def get_by_mime(self, mime: str) -> list[FileFormatDefinition]:
        return self._formats_by_mime.get(mime.lower().strip(), [])

    def get_by_category(self, category: FormatCategory) -> list[FileFormatDefinition]:
        return self._formats_by_cat.get(category, [])

    def list_all(self) -> list[FileFormatDefinition]:
        """Return all registered format definitions."""
        return list(self._formats_by_id.values())

    def list_categories(self) -> list[FormatCategory]:
        """Return all format categories represented in the registry."""
        return list(self._formats_by_cat.keys())

    def list_formats(
        self,
        category: FormatCategory | None = None,
        support_status: SupportStatus | None = None,
    ) -> list[FileFormatDefinition]:
        formats = list(self._formats_by_id.values())
        if category:
            formats = [f for f in formats if f.category == category]
        if support_status:
            formats = [f for f in formats if f.support_status == support_status]
        return formats

    def find_by_signature(self, buffer: bytes) -> list[FileFormatDefinition]:
        """Scan buffer against all registered magic byte signatures."""
        matches: list[FileFormatDefinition] = []
        for fmt in self._formats_by_id.values():
            for sig in fmt.magic_signatures:
                if sig.matches(buffer):
                    matches.append(fmt)
                    break
        return matches

    def _register_default_formats(self) -> None:
        """Pre-populate comprehensive format specifications across 17 categories."""

        # ----------------------------------------------------------------------
        # 1. PDFs
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="pdf",
                canonical_name="Portable Document Format",
                display_name="PDF Document",
                category=FormatCategory.PDF,
                mime_types=["application/pdf", "application/x-pdf"],
                extensions=["pdf"],
                magic_signatures=[PDF_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="pymupdf_extractor",
                description="Adobe Portable Document Format with vector text and layout",
            )
        )

        # ----------------------------------------------------------------------
        # 2. Documents
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="docx",
                canonical_name="Office Open XML Document",
                display_name="Microsoft Word Document",
                category=FormatCategory.DOCUMENT,
                mime_types=[
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ],
                extensions=["docx"],
                is_container=True,
                container_type="zip",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="docx_extractor",
                description="Modern Microsoft Word document container",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="doc",
                canonical_name="Microsoft Word Binary Document",
                display_name="Legacy Word Document (97-2003)",
                category=FormatCategory.DOCUMENT,
                mime_types=["application/msword"],
                extensions=["doc", "dot"],
                magic_signatures=[OLE2_SIGNATURE],
                is_container=True,
                container_type="ole2",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="legacy_doc_extractor",
                description="Legacy binary Microsoft Word format",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="odt",
                canonical_name="OpenDocument Text",
                display_name="ODF Text Document",
                category=FormatCategory.DOCUMENT,
                mime_types=["application/vnd.oasis.opendocument.text"],
                extensions=["odt"],
                is_container=True,
                container_type="zip",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="odt_extractor",
                description="Open Document Format for text documents",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="rtf",
                canonical_name="Rich Text Format",
                display_name="RTF Document",
                category=FormatCategory.DOCUMENT,
                mime_types=["application/rtf", "text/rtf"],
                extensions=["rtf"],
                magic_signatures=[RTF_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="rtf_extractor",
                description="Rich Text Format specification",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="txt",
                canonical_name="Plain Text",
                display_name="Text Document",
                category=FormatCategory.DOCUMENT,
                mime_types=["text/plain"],
                extensions=["txt", "text"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="text_extractor",
                description="Unformatted plain text in UTF-8 or ASCII",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="md",
                canonical_name="Markdown",
                display_name="Markdown Document",
                category=FormatCategory.DOCUMENT,
                mime_types=["text/markdown", "text/x-markdown"],
                extensions=["md", "markdown"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="markdown_extractor",
                description="Lightweight markup language formatted text",
            )
        )

        # ----------------------------------------------------------------------
        # 3. Spreadsheets
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="xlsx",
                canonical_name="Office Open XML Spreadsheet",
                display_name="Microsoft Excel Workbook",
                category=FormatCategory.SPREADSHEET,
                mime_types=["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
                extensions=["xlsx"],
                is_container=True,
                container_type="zip",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="spreadsheet_intelligence_pipeline",
                description="Modern Microsoft Excel spreadsheet container",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="xls",
                canonical_name="Microsoft Excel Binary Spreadsheet",
                display_name="Legacy Excel Spreadsheet (97-2003)",
                category=FormatCategory.SPREADSHEET,
                mime_types=["application/vnd.ms-excel"],
                extensions=["xls"],
                magic_signatures=[OLE2_SIGNATURE],
                is_container=True,
                container_type="ole2",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="spreadsheet_intelligence_pipeline",
                description="Legacy binary Microsoft Excel format",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="ods",
                canonical_name="OpenDocument Spreadsheet",
                display_name="ODF Spreadsheet",
                category=FormatCategory.SPREADSHEET,
                mime_types=["application/vnd.oasis.opendocument.spreadsheet"],
                extensions=["ods"],
                is_container=True,
                container_type="zip",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="spreadsheet_intelligence_pipeline",
                description="Open Document Format for spreadsheets",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="csv",
                canonical_name="Comma-Separated Values",
                display_name="CSV Spreadsheet",
                category=FormatCategory.SPREADSHEET,
                mime_types=["text/csv", "application/csv"],
                extensions=["csv"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="spreadsheet_intelligence_pipeline",
                description="Delimited plain text tabular data",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="tsv",
                canonical_name="Tab-Separated Values",
                display_name="TSV Spreadsheet",
                category=FormatCategory.SPREADSHEET,
                mime_types=["text/tab-separated-values"],
                extensions=["tsv"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="spreadsheet_intelligence_pipeline",
                description="Tab-delimited text tabular data",
            )
        )

        # ----------------------------------------------------------------------
        # 4. Presentations
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="pptx",
                canonical_name="Office Open XML Presentation",
                display_name="Microsoft PowerPoint Presentation",
                category=FormatCategory.PRESENTATION,
                mime_types=[
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                ],
                extensions=["pptx"],
                is_container=True,
                container_type="zip",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Modern Microsoft PowerPoint container",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="ppt",
                canonical_name="Microsoft PowerPoint Binary Presentation",
                display_name="Legacy PowerPoint Presentation (97-2003)",
                category=FormatCategory.PRESENTATION,
                mime_types=["application/vnd.ms-powerpoint"],
                extensions=["ppt"],
                magic_signatures=[OLE2_SIGNATURE],
                is_container=True,
                container_type="ole2",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Legacy binary PowerPoint presentation",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="odp",
                canonical_name="OpenDocument Presentation",
                display_name="ODF Presentation",
                category=FormatCategory.PRESENTATION,
                mime_types=["application/vnd.oasis.opendocument.presentation"],
                extensions=["odp"],
                is_container=True,
                container_type="zip",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Open Document Format for presentations",
            )
        )

        # ----------------------------------------------------------------------
        # 5. Images
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="png",
                canonical_name="Portable Network Graphics",
                display_name="PNG Image",
                category=FormatCategory.IMAGE,
                mime_types=["image/png"],
                extensions=["png"],
                magic_signatures=[PNG_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Lossless raster image with alpha transparency",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="jpeg",
                canonical_name="Joint Photographic Experts Group",
                display_name="JPEG Image",
                category=FormatCategory.IMAGE,
                mime_types=["image/jpeg", "image/jpg"],
                extensions=["jpg", "jpeg", "jpe"],
                magic_signatures=[JPEG_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Lossy photographic image format",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="gif",
                canonical_name="Graphics Interchange Format",
                display_name="GIF Image",
                category=FormatCategory.IMAGE,
                mime_types=["image/gif"],
                extensions=["gif"],
                magic_signatures=[GIF87_SIGNATURE, GIF89_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Palette-based animated or static raster image",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="webp",
                canonical_name="WebP Image",
                display_name="Google WebP Image",
                category=FormatCategory.IMAGE,
                mime_types=["image/webp"],
                extensions=["webp"],
                magic_signatures=[WEBP_RIFF],
                is_container=True,
                container_type="riff",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Modern lossy/lossless compressed web image",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="bmp",
                canonical_name="Bitmap Image",
                display_name="Windows Bitmap Image",
                category=FormatCategory.IMAGE,
                mime_types=["image/bmp", "image/x-ms-bmp"],
                extensions=["bmp", "dib"],
                magic_signatures=[BMP_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Uncompressed raster bitmap graphic",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="tiff",
                canonical_name="Tagged Image File Format",
                display_name="TIFF Image",
                category=FormatCategory.IMAGE,
                mime_types=["image/tiff"],
                extensions=["tif", "tiff"],
                magic_signatures=[TIFF_LE_SIGNATURE, TIFF_BE_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="High-depth raster image format for scanning and print",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="svg",
                canonical_name="Scalable Vector Graphics",
                display_name="SVG Vector Graphic",
                category=FormatCategory.IMAGE,
                mime_types=["image/svg+xml"],
                extensions=["svg"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="XML-based two-dimensional vector graphic",
            )
        )

        # ----------------------------------------------------------------------
        # 6. Audio
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="mp3",
                canonical_name="MPEG Audio Layer III",
                display_name="MP3 Audio",
                category=FormatCategory.AUDIO,
                mime_types=["audio/mpeg", "audio/mp3"],
                extensions=["mp3"],
                magic_signatures=[MP3_ID3_SIGNATURE, MP3_SYNC_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Standard lossy compressed digital audio",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="wav",
                canonical_name="Waveform Audio File Format",
                display_name="WAV Audio",
                category=FormatCategory.AUDIO,
                mime_types=["audio/wav", "audio/x-wav"],
                extensions=["wav"],
                magic_signatures=[WEBP_RIFF],
                is_container=True,
                container_type="riff",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Uncompressed LPCM audio container",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="flac",
                canonical_name="Free Lossless Audio Codec",
                display_name="FLAC Audio",
                category=FormatCategory.AUDIO,
                mime_types=["audio/flac", "audio/x-flac"],
                extensions=["flac"],
                magic_signatures=[FLAC_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Lossless bit-perfect compressed audio",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="ogg",
                canonical_name="Ogg Vorbis Audio",
                display_name="OGG Audio",
                category=FormatCategory.AUDIO,
                mime_types=["audio/ogg", "application/ogg"],
                extensions=["ogg", "oga"],
                magic_signatures=[OGG_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Open source compressed audio stream",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="m4a",
                canonical_name="MPEG-4 Audio",
                display_name="M4A Audio",
                category=FormatCategory.AUDIO,
                mime_types=["audio/mp4", "audio/x-m4a"],
                extensions=["m4a"],
                magic_signatures=[MP4_FTYP_SIGNATURE],
                is_container=True,
                container_type="isobmff",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="MPEG-4 AAC compressed audio container",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="aac",
                canonical_name="Advanced Audio Coding",
                display_name="AAC Audio",
                category=FormatCategory.AUDIO,
                mime_types=["audio/aac", "audio/x-aac"],
                extensions=["aac"],
                magic_signatures=[AAC_ADTS_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Raw Advanced Audio Coding ADTS audio stream",
            )
        )

        # ----------------------------------------------------------------------
        # 7. Video
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="mp4",
                canonical_name="MPEG-4 Part 14 Video",
                display_name="MP4 Video",
                category=FormatCategory.VIDEO,
                mime_types=["video/mp4"],
                extensions=["mp4", "m4v"],
                magic_signatures=[MP4_FTYP_SIGNATURE],
                is_container=True,
                container_type="isobmff",
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="Standard ISO-BMFF digital multimedia container",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="mkv",
                canonical_name="Matroska Video",
                display_name="Matroska MKV Video",
                category=FormatCategory.VIDEO,
                mime_types=["video/x-matroska"],
                extensions=["mkv"],
                magic_signatures=[EBML_SIGNATURE],
                is_container=True,
                container_type="ebml",
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="Extensible open multimedia container",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="webm",
                canonical_name="WebM Video",
                display_name="WebM Video",
                category=FormatCategory.VIDEO,
                mime_types=["video/webm"],
                extensions=["webm"],
                magic_signatures=[EBML_SIGNATURE],
                is_container=True,
                container_type="ebml",
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="Open media file format designed for the web",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="mov",
                canonical_name="QuickTime Movie",
                display_name="QuickTime MOV Video",
                category=FormatCategory.VIDEO,
                mime_types=["video/quicktime"],
                extensions=["mov", "qt"],
                magic_signatures=[MP4_FTYP_SIGNATURE],
                is_container=True,
                container_type="isobmff",
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="Apple QuickTime multimedia container",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="avi",
                canonical_name="Audio Video Interleave",
                display_name="AVI Video",
                category=FormatCategory.VIDEO,
                mime_types=["video/x-msvideo"],
                extensions=["avi"],
                magic_signatures=[WEBP_RIFF],
                is_container=True,
                container_type="riff",
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="Microsoft RIFF video container",
            )
        )

        # ----------------------------------------------------------------------
        # 8. Archives & Compressed Packages
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="zip",
                canonical_name="ZIP Archive",
                display_name="ZIP Archive",
                category=FormatCategory.ARCHIVE,
                mime_types=["application/zip", "application/x-zip-compressed"],
                extensions=["zip"],
                magic_signatures=[ZIP_LOCAL_SIGNATURE, ZIP_EMPTY_SIGNATURE, ZIP_SPANNED_SIGNATURE],
                is_container=True,
                container_type="zip",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Ubiquitous lossless data compression archive",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="7z",
                canonical_name="7-Zip Archive",
                display_name="7-Zip Archive",
                category=FormatCategory.ARCHIVE,
                mime_types=["application/x-7z-compressed"],
                extensions=["7z"],
                magic_signatures=[SEVEN_ZIP_SIGNATURE],
                is_container=True,
                container_type="7z",
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="High-ratio LZMA compressed archive",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="tar",
                canonical_name="Tape Archive",
                display_name="TAR Archive",
                category=FormatCategory.ARCHIVE,
                mime_types=["application/x-tar"],
                extensions=["tar"],
                magic_signatures=[TAR_USTAR_SIGNATURE],
                is_container=True,
                container_type="tar",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="POSIX standard concatenated archive file",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="gz",
                canonical_name="Gzip Compressed Archive",
                display_name="GZIP Archive",
                category=FormatCategory.ARCHIVE,
                mime_types=["application/gzip", "application/x-gzip"],
                extensions=["gz", "gzip"],
                magic_signatures=[GZIP_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="GNU single-file deflate compression",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="bz2",
                canonical_name="Bzip2 Compressed Archive",
                display_name="BZIP2 Archive",
                category=FormatCategory.ARCHIVE,
                mime_types=["application/x-bzip2"],
                extensions=["bz2"],
                magic_signatures=[BZIP2_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Burrows-Wheeler block-sorting compressed file",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="xz",
                canonical_name="XZ Compressed Archive",
                display_name="XZ Archive",
                category=FormatCategory.ARCHIVE,
                mime_types=["application/x-xz"],
                extensions=["xz"],
                magic_signatures=[XZ_SIGNATURE],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="LZMA2 container archive",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="rar",
                canonical_name="Roshal Archive",
                display_name="RAR Archive",
                category=FormatCategory.ARCHIVE,
                mime_types=["application/x-rar-compressed", "application/vnd.rar"],
                extensions=["rar"],
                magic_signatures=[RAR_V4_SIGNATURE, RAR_V5_SIGNATURE],
                is_container=True,
                container_type="rar",
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="Proprietary multi-volume compressed archive",
            )
        )

        # ----------------------------------------------------------------------
        # 9. Programming Languages & Code
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="py",
                canonical_name="Python Source Code",
                display_name="Python Script",
                category=FormatCategory.CODE,
                mime_types=["text/x-python", "application/x-python-code"],
                extensions=["py", "pyw"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Python programming language source code",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="js",
                canonical_name="JavaScript Source Code",
                display_name="JavaScript File",
                category=FormatCategory.CODE,
                mime_types=["application/javascript", "text/javascript"],
                extensions=["js", "mjs", "cjs"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="ECMAScript source code",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="ts",
                canonical_name="TypeScript Source Code",
                display_name="TypeScript File",
                category=FormatCategory.CODE,
                mime_types=["application/x-typescript", "video/mp2t"],  # note .ts ambiguity
                extensions=["ts", "mts", "cts", "tsx"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Typed superset of JavaScript source",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="html",
                canonical_name="HyperText Markup Language",
                display_name="HTML Document",
                category=FormatCategory.CODE,
                mime_types=["text/html"],
                extensions=["html", "htm"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Standard markup language for web documents",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="css",
                canonical_name="Cascading Style Sheets",
                display_name="CSS Stylesheet",
                category=FormatCategory.CODE,
                mime_types=["text/css"],
                extensions=["css"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Style sheet language for document presentation",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="java",
                canonical_name="Java Source Code",
                display_name="Java Source File",
                category=FormatCategory.CODE,
                mime_types=["text/x-java-source"],
                extensions=["java"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Java language source code file",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="c",
                canonical_name="C Source Code",
                display_name="C Source File",
                category=FormatCategory.CODE,
                mime_types=["text/x-c"],
                extensions=["c", "h"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="C programming language source code",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="cpp",
                canonical_name="C++ Source Code",
                display_name="C++ Source File",
                category=FormatCategory.CODE,
                mime_types=["text/x-c++"],
                extensions=["cpp", "cc", "cxx", "hpp"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="C++ object-oriented programming language source",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="sql",
                canonical_name="Structured Query Language",
                display_name="SQL Script",
                category=FormatCategory.CODE,
                mime_types=["application/sql", "text/x-sql"],
                extensions=["sql"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Relational database queries and DDL definitions",
            )
        )

        # ----------------------------------------------------------------------
        # 10. Structured Data
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="json",
                canonical_name="JavaScript Object Notation",
                display_name="JSON Data",
                category=FormatCategory.STRUCTURED_DATA,
                mime_types=["application/json"],
                extensions=["json"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Lightweight text data interchange format",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="xml",
                canonical_name="Extensible Markup Language",
                display_name="XML Document",
                category=FormatCategory.STRUCTURED_DATA,
                mime_types=["application/xml", "text/xml"],
                extensions=["xml"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Structured hierarchical document markup",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="yaml",
                canonical_name="YAML Ain't Markup Language",
                display_name="YAML Configuration",
                category=FormatCategory.STRUCTURED_DATA,
                mime_types=["application/x-yaml", "text/yaml"],
                extensions=["yaml", "yml"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Human-friendly data serialization language",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="toml",
                canonical_name="Tom's Obvious Minimal Language",
                display_name="TOML Configuration",
                category=FormatCategory.STRUCTURED_DATA,
                mime_types=["application/toml"],
                extensions=["toml"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Minimal configuration file format with explicit semantics",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="parquet",
                canonical_name="Apache Parquet",
                display_name="Parquet Columnar Data",
                category=FormatCategory.STRUCTURED_DATA,
                mime_types=["application/vnd.apache.parquet"],
                extensions=["parquet"],
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="Columnar storage format for high-throughput big data",
            )
        )

        # ----------------------------------------------------------------------
        # 11. Emails
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="eml",
                canonical_name="Electronic Mail Format (RFC 822/2822)",
                display_name="EML Email Message",
                category=FormatCategory.EMAIL,
                mime_types=["message/rfc822"],
                extensions=["eml"],
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                description="Standard MIME compliant plain text email message",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="msg",
                canonical_name="Outlook Item Message",
                display_name="Outlook MSG Email",
                category=FormatCategory.EMAIL,
                mime_types=["application/vnd.ms-outlook"],
                extensions=["msg"],
                magic_signatures=[OLE2_SIGNATURE],
                is_container=True,
                container_type="ole2",
                support_status=SupportStatus.DETECTED_BUT_NOT_IMPLEMENTED,
                description="Microsoft Outlook binary message container",
            )
        )

        # ----------------------------------------------------------------------
        # 12. E-Books
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="epub",
                canonical_name="Electronic Publication",
                display_name="EPUB E-Book",
                category=FormatCategory.EBOOK,
                mime_types=["application/epub+zip"],
                extensions=["epub"],
                is_container=True,
                container_type="zip",
                support_status=SupportStatus.DETECTED_AND_SUPPORTED,
                extraction_plugin_id="epub_extractor",
                description="Standard XML and HTML digital e-book publication",
            )
        )

        # ----------------------------------------------------------------------
        # 13. Fonts
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="ttf",
                canonical_name="TrueType Font",
                display_name="TTF Font",
                category=FormatCategory.FONT,
                mime_types=["font/ttf", "application/x-font-ttf"],
                extensions=["ttf"],
                magic_signatures=[TTF_SIGNATURE],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Apple/Microsoft outline font standard",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="otf",
                canonical_name="OpenType Font",
                display_name="OTF Font",
                category=FormatCategory.FONT,
                mime_types=["font/otf", "application/x-font-opentype"],
                extensions=["otf"],
                magic_signatures=[OTF_SIGNATURE],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Adobe/Microsoft scalable computer fonts",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="woff",
                canonical_name="Web Open Font Format 1.0",
                display_name="WOFF Font",
                category=FormatCategory.FONT,
                mime_types=["font/woff", "application/font-woff"],
                extensions=["woff"],
                magic_signatures=[WOFF_SIGNATURE],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Compressed web font container format",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="woff2",
                canonical_name="Web Open Font Format 2.0",
                display_name="WOFF2 Font",
                category=FormatCategory.FONT,
                mime_types=["font/woff2"],
                extensions=["woff2"],
                magic_signatures=[WOFF2_SIGNATURE],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Brotli compressed web font container",
            )
        )

        # ----------------------------------------------------------------------
        # 14. Executables
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="elf",
                canonical_name="Executable and Linkable Format",
                display_name="Linux ELF Binary",
                category=FormatCategory.EXECUTABLE,
                mime_types=["application/x-executable", "application/x-sharedlib"],
                extensions=["elf", "so", "bin"],
                magic_signatures=[ELF_SIGNATURE],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Standard binary file format for Linux binaries and libraries",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="pe",
                canonical_name="Portable Executable",
                display_name="Windows PE Executable",
                category=FormatCategory.EXECUTABLE,
                mime_types=["application/x-dosexec", "application/x-msdownload"],
                extensions=["exe", "dll", "sys"],
                magic_signatures=[PE_MZ_SIGNATURE],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Windows executable, object code, and DLL file",
            )
        )
        self.register(
            FileFormatDefinition(
                format_id="macho",
                canonical_name="Mach-O Binary",
                display_name="Apple Mach-O Binary",
                category=FormatCategory.EXECUTABLE,
                mime_types=["application/x-mach-binary"],
                extensions=["dylib"],
                magic_signatures=[MACHO_32_BE, MACHO_64_BE, MACHO_32_LE, MACHO_64_LE],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Mach-O object file format for macOS and iOS",
            )
        )

        # ----------------------------------------------------------------------
        # 15. Disk Images
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="iso",
                canonical_name="ISO 9660 Disk Image",
                display_name="ISO Optical Disk Image",
                category=FormatCategory.DISK_IMAGE,
                mime_types=["application/x-iso9660-image"],
                extensions=["iso"],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Archive file containing complete optical disc image",
            )
        )

        # ----------------------------------------------------------------------
        # 16. Other Binary / Generic
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="binary",
                canonical_name="Binary Data",
                display_name="Binary File",
                category=FormatCategory.OTHER_BINARY,
                mime_types=["application/octet-stream"],
                extensions=["bin", "dat"],
                support_status=SupportStatus.DETECTED_BUT_UNSUPPORTED,
                description="Arbitrary raw unclassified binary data",
            )
        )

        # ----------------------------------------------------------------------
        # 17. Unknown Formats
        # ----------------------------------------------------------------------
        self.register(
            FileFormatDefinition(
                format_id="unknown",
                canonical_name="Unknown Format",
                display_name="Unidentified File",
                category=FormatCategory.UNKNOWN,
                mime_types=["application/octet-stream"],
                extensions=[],
                support_status=SupportStatus.UNKNOWN_FORMAT,
                description="File could not be identified by any detection signal",
            )
        )


# Global singleton instance of format registry
format_registry = FormatRegistry()
