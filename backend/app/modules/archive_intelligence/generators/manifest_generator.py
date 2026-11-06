"""Archive entry manifest generator."""

import csv
import io
import json

from app.modules.archive_intelligence.schemas.archive_document import ArchiveDocument


class ArchiveManifestGenerator:
    """Generates machine-readable manifest of all entries in the archive."""

    def generate(self, doc: ArchiveDocument, format_type: str = "json") -> str:
        """Generate manifest as JSON or CSV formatted string."""
        if format_type.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "entry_id",
                    "original_path",
                    "normalized_path",
                    "filename",
                    "extension",
                    "entry_type",
                    "uncompressed_size",
                    "compressed_size",
                    "checksum",
                    "encrypted",
                    "is_nested_archive",
                    "status",
                ]
            )
            for e in doc.entries:
                writer.writerow(
                    [
                        e.entry_id,
                        e.original_path,
                        e.normalized_path,
                        e.filename,
                        e.extension,
                        e.entry_type,
                        e.uncompressed_size,
                        e.compressed_size,
                        e.checksum or "",
                        e.encrypted,
                        e.is_nested_archive,
                        e.processing_status,
                    ]
                )
            return output.getvalue()

        # Default JSON format
        entries_data = [
            {
                "entry_id": e.entry_id,
                "original_path": e.original_path,
                "normalized_path": e.normalized_path,
                "filename": e.filename,
                "extension": e.extension,
                "entry_type": e.entry_type,
                "uncompressed_size": e.uncompressed_size,
                "compressed_size": e.compressed_size,
                "checksum": e.checksum,
                "encrypted": e.encrypted,
                "is_nested_archive": e.is_nested_archive,
                "detection_result": e.detection_result,
                "status": e.processing_status,
            }
            for e in doc.entries
        ]
        return json.dumps(
            {
                "archive_id": doc.archive_id,
                "total_entries": len(doc.entries),
                "manifest": entries_data,
            },
            indent=2,
        )
