"""Child file manifest generator."""

import json

from app.modules.archive_intelligence.schemas.archive_document import ArchiveDocument


class ArchiveChildFileManifestGenerator:
    """Generates manifest of extracted child files with storage references and provenance."""

    def generate(self, doc: ArchiveDocument) -> str:
        child_manifest = {
            "root_archive_id": doc.archive_id,
            "nesting_depth": doc.nesting_depth,
            "total_extracted_children": len(doc.extracted_files),
            "children": [
                {
                    "entry_id": f.get("entry_id"),
                    "original_path": f.get("original_path"),
                    "normalized_path": f.get("normalized_path"),
                    "extracted_path": f.get("extracted_path"),
                    "file_size": f.get("file_size"),
                    "sha256": f.get("sha256"),
                    "is_nested_archive": f.get("is_nested_archive", False),
                    "created_file_id": f.get("created_file_id"),
                    "downstream_analysis_id": f.get("downstream_analysis_id"),
                    "downstream_engine": f.get("downstream_engine"),
                }
                for f in doc.extracted_files
            ],
        }
        return json.dumps(child_manifest, indent=2)
