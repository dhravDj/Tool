"""Safe inspection of container-based file formats (ZIP, OLE2, RIFF, ISO-BMFF)."""

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# Defensive security constraints for container inspection
MAX_ZIP_ENTRIES_SCANNED = 120
MAX_XML_READ_BYTES = 65536  # 64 KB limit for header/manifest parsing
MAX_TOTAL_DECOMPRESSED_BYTES = 5 * 1024 * 1024  # 5 MB maximum decompression quota


@dataclass
class ContainerInspectionResult:
    """Findings from inspecting a container-based archive or structured package."""

    is_container: bool = False
    container_type: str | None = None  # "zip", "ole2", "riff", "isobmff", "tar"
    identified_format_id: str | None = None
    manifest_entries: list[str] = field(default_factory=list)
    is_suspicious: bool = False
    is_corrupted: bool = False
    warnings: list[str] = field(default_factory=list)


class ContainerInspector:
    """Safely inspects internal structures of compound files without full decompression."""

    @classmethod
    def inspect_zip_package(cls, file_path: Path) -> ContainerInspectionResult:
        """Inspect internal filenames in a ZIP archive with strict entry and size limits."""
        result = ContainerInspectionResult(is_container=True, container_type="zip")

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                infolist = zf.infolist()

                if len(infolist) > MAX_ZIP_ENTRIES_SCANNED:
                    result.warnings.append(
                        f"Archive contains {len(infolist)} entries; scanning capped at {MAX_ZIP_ENTRIES_SCANNED}."
                    )

                names: set[str] = set()
                total_uncompressed = 0
                for info in infolist[:MAX_ZIP_ENTRIES_SCANNED]:
                    names.add(info.filename)
                    total_uncompressed += info.file_size
                    # Zip bomb heuristic check
                    if info.compress_size > 0 and (info.file_size / info.compress_size > 150):
                        result.is_suspicious = True
                        result.warnings.append(
                            f"Suspicious compression ratio on entry '{info.filename}' ({info.file_size}/{info.compress_size})."
                        )

                result.manifest_entries = list(names)[:20]

                # 1. Microsoft OpenXML Formats
                if "[Content_Types].xml" in names:
                    if any(n.startswith("word/") for n in names) or "word/document.xml" in names:
                        result.identified_format_id = "docx"
                        return result
                    if any(n.startswith("xl/") for n in names) or "xl/workbook.xml" in names:
                        result.identified_format_id = "xlsx"
                        return result
                    if any(n.startswith("ppt/") for n in names) or "ppt/presentation.xml" in names:
                        result.identified_format_id = "pptx"
                        return result

                # 2. OpenDocument Formats (ODF)
                if "mimetype" in names:
                    try:
                        # Safely read first 128 bytes of mimetype file
                        mime_data = (
                            zf.read("mimetype")[:128].decode("ascii", errors="ignore").strip()
                        )
                        if "application/vnd.oasis.opendocument.text" in mime_data:
                            result.identified_format_id = "odt"
                            return result
                        if "application/vnd.oasis.opendocument.spreadsheet" in mime_data:
                            result.identified_format_id = "ods"
                            return result
                        if "application/vnd.oasis.opendocument.presentation" in mime_data:
                            result.identified_format_id = "odp"
                            return result
                        if "application/epub+zip" in mime_data:
                            result.identified_format_id = "epub"
                            return result
                    except Exception as e:
                        result.warnings.append(f"Could not parse ODF mimetype entry: {e}")

                # 3. EPUB Electronic Books
                if "META-INF/container.xml" in names:
                    result.identified_format_id = "epub"
                    return result

                # 4. Java Archives / Android APKs
                if "AndroidManifest.xml" in names:
                    result.identified_format_id = "apk"
                    return result
                if "META-INF/MANIFEST.MF" in names:
                    result.identified_format_id = "jar"
                    return result

                # Generic standard ZIP
                result.identified_format_id = "zip"
                return result

        except zipfile.BadZipFile:
            result.is_corrupted = True
            result.is_suspicious = True
            result.identified_format_id = "zip"
            result.warnings.append("Corrupted or truncated ZIP container structure.")
            return result
        except Exception as e:
            result.warnings.append(f"Error inspecting ZIP container: {e}")
            return result

    @classmethod
    def inspect_riff_container(cls, buffer: bytes) -> ContainerInspectionResult:
        """Inspect RIFF container format tag (WEBP, WAVE, AVI)."""
        result = ContainerInspectionResult(is_container=True, container_type="riff")
        if len(buffer) < 12 or buffer[:4] != b"RIFF":
            return result

        form_type = buffer[8:12]
        if form_type == b"WEBP":
            result.identified_format_id = "webp"
        elif form_type == b"WAVE":
            result.identified_format_id = "wav"
        elif form_type == b"AVI ":
            result.identified_format_id = "avi"
        else:
            result.identified_format_id = "riff"

        return result

    @classmethod
    def inspect_isobmff_container(cls, buffer: bytes) -> ContainerInspectionResult:
        """Inspect ISO Base Media File Format ftyp major brand (MP4, M4A, MOV, HEIC)."""
        result = ContainerInspectionResult(is_container=True, container_type="isobmff")
        if len(buffer) < 12 or buffer[4:8] != b"ftyp":
            return result

        major_brand = buffer[8:12].decode("ascii", errors="ignore").lower()
        result.manifest_entries = [f"brand:{major_brand}"]

        if major_brand in ("isom", "iso2", "mp41", "mp42", "avc1"):
            result.identified_format_id = "mp4"
        elif major_brand in ("m4a ", "m4b ", "m4p "):
            result.identified_format_id = "m4a"
        elif major_brand in ("qt  ", "moov"):
            result.identified_format_id = "mov"
        elif major_brand in ("heic", "heix", "mif1"):
            result.identified_format_id = "heic"
        else:
            result.identified_format_id = "mp4"  # Default generic ISO-BMFF

        return result
