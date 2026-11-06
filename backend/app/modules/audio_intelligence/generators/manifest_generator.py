"""Audio execution manifest generator."""

from datetime import UTC, datetime

from app.modules.audio_intelligence.schemas.audio_document import (
    AudioDocument,
    AudioManifest,
)


class AudioManifestGenerator:
    """Produces comprehensive execution manifest detailing analysis provenance."""

    @staticmethod
    def generate(
        doc: AudioDocument,
        source_filename: str,
        artifacts: dict[str, str],
        errors: list[str] | None = None,
    ) -> AudioManifest:
        """Create structured AudioManifest entity."""
        word_count = sum(len(s.text.split()) for s in doc.segments)

        return AudioManifest(
            document_id=doc.document_id,
            file_id=doc.source_file_id,
            source_filename=source_filename,
            source_format=doc.format,
            status=doc.processing_status,
            engine_name=doc.model_information.engine_name,
            model_name=doc.model_information.model_name,
            processing_time_seconds=doc.processing_metadata.get(
                "processing_duration_seconds", 0.0
            ),
            duration_seconds=doc.duration,
            detected_language=doc.language,
            segment_count=len(doc.segments),
            word_count=word_count,
            speaker_count=len(doc.speakers),
            event_count=len(doc.events),
            artifacts=artifacts,
            warnings=doc.warnings,
            errors=errors or [],
            created_at=datetime.now(UTC),
        )
