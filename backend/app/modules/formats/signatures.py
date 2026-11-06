"""Binary magic byte signatures for reliable file format identification."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MagicSignature:
    """Represents a byte pattern located at a specific file offset."""

    signature_bytes: bytes
    offset: int = 0
    mask: bytes | None = None
    name: str = ""
    description: str = ""

    def matches(self, buffer: bytes) -> bool:
        """Check if this signature matches within the given byte buffer."""
        sig_len = len(self.signature_bytes)
        if len(buffer) < self.offset + sig_len:
            return False

        chunk = buffer[self.offset : self.offset + sig_len]
        if self.mask is not None and len(self.mask) == sig_len:
            masked_chunk = bytes(b & m for b, m in zip(chunk, self.mask, strict=True))
            return masked_chunk == self.signature_bytes

        return chunk == self.signature_bytes


# ==============================================================================
# Comprehensive Known Signatures Registry
# ==============================================================================

PDF_SIGNATURE = MagicSignature(
    signature_bytes=b"%PDF-",
    offset=0,
    name="PDF",
    description="Adobe Portable Document Format header",
)

# Images
PNG_SIGNATURE = MagicSignature(
    signature_bytes=b"\x89PNG\r\n\x1a\n",
    offset=0,
    name="PNG",
    description="Portable Network Graphics header",
)

JPEG_SIGNATURE = MagicSignature(
    signature_bytes=b"\xff\xd8\xff",
    offset=0,
    name="JPEG",
    description="Joint Photographic Experts Group SOI marker",
)

GIF87_SIGNATURE = MagicSignature(
    signature_bytes=b"GIF87a",
    offset=0,
    name="GIF87a",
    description="Graphics Interchange Format 1987a",
)

GIF89_SIGNATURE = MagicSignature(
    signature_bytes=b"GIF89a",
    offset=0,
    name="GIF89a",
    description="Graphics Interchange Format 1989a",
)

WEBP_RIFF = MagicSignature(
    signature_bytes=b"RIFF",
    offset=0,
    name="RIFF",
    description="Resource Interchange File Format container",
)

WEBP_TAG = MagicSignature(
    signature_bytes=b"WEBP",
    offset=8,
    name="WEBP",
    description="Google WebP image container tag",
)

BMP_SIGNATURE = MagicSignature(
    signature_bytes=b"BM",
    offset=0,
    name="BMP",
    description="Windows Bitmap file identifier",
)

TIFF_LE_SIGNATURE = MagicSignature(
    signature_bytes=b"II*\x00",
    offset=0,
    name="TIFF_LE",
    description="TIFF Little-Endian (Intel format)",
)

TIFF_BE_SIGNATURE = MagicSignature(
    signature_bytes=b"MM\x00*",
    offset=0,
    name="TIFF_BE",
    description="TIFF Big-Endian (Motorola format)",
)

# Audio
MP3_ID3_SIGNATURE = MagicSignature(
    signature_bytes=b"ID3",
    offset=0,
    name="MP3_ID3",
    description="MPEG Audio with ID3v2 container header",
)

MP3_SYNC_SIGNATURE = MagicSignature(
    signature_bytes=b"\xff\xe2",
    offset=0,
    mask=b"\xff\xe6",
    name="MP3_SYNC",
    description="MPEG Audio Layer III frame sync header (Layer 01)",
)

AAC_ADTS_SIGNATURE = MagicSignature(
    signature_bytes=b"\xff\xf0",
    offset=0,
    mask=b"\xff\xf6",
    name="AAC_ADTS",
    description="Advanced Audio Coding ADTS frame header (Layer 00)",
)

WAV_TAG = MagicSignature(
    signature_bytes=b"WAVE",
    offset=8,
    name="WAV",
    description="WAVE audio chunk tag inside RIFF container",
)

FLAC_SIGNATURE = MagicSignature(
    signature_bytes=b"fLaC",
    offset=0,
    name="FLAC",
    description="Free Lossless Audio Codec header",
)

OGG_SIGNATURE = MagicSignature(
    signature_bytes=b"OggS",
    offset=0,
    name="OGG",
    description="Xiph.Org Ogg bitstream container header",
)

# Video
MP4_FTYP_SIGNATURE = MagicSignature(
    signature_bytes=b"ftyp",
    offset=4,
    name="ISO_BMFF",
    description="ISO Base Media File Format (MP4/MOV/M4A/HEIC)",
)

QT_MOOV_SIGNATURE = MagicSignature(
    signature_bytes=b"moov",
    offset=4,
    name="QT_MOOV",
    description="Apple QuickTime Movie moov atom header",
)

QT_WIDE_SIGNATURE = MagicSignature(
    signature_bytes=b"wide",
    offset=4,
    name="QT_WIDE",
    description="Apple QuickTime Movie wide atom header",
)

EBML_SIGNATURE = MagicSignature(
    signature_bytes=b"\x1aE\xdf\xa3",
    offset=0,
    name="EBML",
    description="Extensible Binary Meta Language (Matroska / WebM)",
)

AVI_TAG = MagicSignature(
    signature_bytes=b"AVI ",
    offset=8,
    name="AVI",
    description="Audio Video Interleave tag inside RIFF container",
)

# Archives & Containers
ZIP_STANDARD_SIGNATURE = MagicSignature(
    signature_bytes=b"PK\x03\x04",
    offset=0,
    name="ZIP_LOCAL",
    description="Standard ZIP local file header",
)
ZIP_LOCAL_SIGNATURE = ZIP_STANDARD_SIGNATURE

ZIP_EMPTY_SIGNATURE = MagicSignature(
    signature_bytes=b"PK\x05\x06",
    offset=0,
    name="ZIP_EMPTY",
    description="Empty ZIP archive end of central directory header",
)

ZIP_SPANNED_SIGNATURE = MagicSignature(
    signature_bytes=b"PK\x07\x08",
    offset=0,
    name="ZIP_SPANNED",
    description="Spanned or split ZIP archive signature",
)

SEVEN_ZIP_SIGNATURE = MagicSignature(
    signature_bytes=b"7z\xbc\xaf'\x1c",
    offset=0,
    name="7Z",
    description="7-Zip archive header",
)

GZIP_SIGNATURE = MagicSignature(
    signature_bytes=b"\x1f\x8b",
    offset=0,
    name="GZIP",
    description="GZIP compressed file header",
)

BZIP2_SIGNATURE = MagicSignature(
    signature_bytes=b"BZh",
    offset=0,
    name="BZIP2",
    description="BZIP2 compressed stream header",
)

XZ_SIGNATURE = MagicSignature(
    signature_bytes=b"\xfd7zXZ\x00",
    offset=0,
    name="XZ",
    description="XZ compression format header",
)

RAR_V4_SIGNATURE = MagicSignature(
    signature_bytes=b"Rar!\x1a\x07\x00",
    offset=0,
    name="RAR4",
    description="RAR archive v1.5 - v4.x header",
)

RAR_V5_SIGNATURE = MagicSignature(
    signature_bytes=b"Rar!\x1a\x07\x01\x00",
    offset=0,
    name="RAR5",
    description="RAR archive v5.0+ header",
)

TAR_USTAR_SIGNATURE = MagicSignature(
    signature_bytes=b"ustar",
    offset=257,
    name="TAR_USTAR",
    description="POSIX tar archive ustar indicator",
)

# Microsoft Compound Document Format (OLE2 - DOC, XLS, PPT, MSG)
OLE2_SIGNATURE = MagicSignature(
    signature_bytes=b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    offset=0,
    name="OLE2",
    description="Microsoft Compound File Binary Format (OLE2)",
)

RTF_SIGNATURE = MagicSignature(
    signature_bytes=b"{\\rtf",
    offset=0,
    name="RTF",
    description="Rich Text Format document header",
)

# Executables & Binaries
ELF_SIGNATURE = MagicSignature(
    signature_bytes=b"\x7fELF",
    offset=0,
    name="ELF",
    description="Executable and Linkable Format (Linux binary)",
)

PE_MZ_SIGNATURE = MagicSignature(
    signature_bytes=b"MZ",
    offset=0,
    name="PE_MZ",
    description="DOS / Windows Portable Executable (EXE/DLL)",
)

MACHO_32_BE = MagicSignature(
    signature_bytes=b"\xfe\xed\xfa\xce",
    offset=0,
    name="MACHO_32_BE",
    description="Apple Mach-O 32-bit big-endian binary",
)

MACHO_64_BE = MagicSignature(
    signature_bytes=b"\xfe\xed\xfa\xcf",
    offset=0,
    name="MACHO_64_BE",
    description="Apple Mach-O 64-bit big-endian binary",
)

MACHO_32_LE = MagicSignature(
    signature_bytes=b"\xce\xfa\xed\xfe",
    offset=0,
    name="MACHO_32_LE",
    description="Apple Mach-O 32-bit little-endian binary",
)

MACHO_64_LE = MagicSignature(
    signature_bytes=b"\xcf\xfa\xed\xfe",
    offset=0,
    name="MACHO_64_LE",
    description="Apple Mach-O 64-bit little-endian binary",
)

# Structured Data
PARQUET_SIGNATURE = MagicSignature(
    signature_bytes=b"PAR1",
    offset=0,
    name="PARQUET_MAGIC",
    description="Apache Parquet columnar storage format",
)

# Fonts
WOFF_SIGNATURE = MagicSignature(
    signature_bytes=b"wOFF",
    offset=0,
    name="WOFF",
    description="Web Open Font Format 1.0",
)

WOFF2_SIGNATURE = MagicSignature(
    signature_bytes=b"wOF2",
    offset=0,
    name="WOFF2",
    description="Web Open Font Format 2.0",
)

TTF_SIGNATURE = MagicSignature(
    signature_bytes=b"\x00\x01\x00\x00",
    offset=0,
    name="TTF",
    description="TrueType Font collection header",
)

OTF_SIGNATURE = MagicSignature(
    signature_bytes=b"OTTO",
    offset=0,
    name="OTF",
    description="OpenType Font header",
)
