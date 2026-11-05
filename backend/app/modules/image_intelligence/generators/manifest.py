"""Execution manifest generator for Image Intelligence."""

from app.modules.image_intelligence.schemas.image_document import ImageManifest


class ImageManifestGenerator:
    """Creates operational execution manifest for image processing pipelines."""

    @staticmethod
    def create_manifest(
        image_id: str,
        file_id: str,
        filename: str,
        status: str,
        processing_time_seconds: float,
        engines_used: dict[str, str],
        artifacts: dict[str, str],
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> ImageManifest:
        return ImageManifest(
            image_id=image_id,
            file_id=file_id,
            filename=filename,
            status=status,
            processing_time_seconds=round(processing_time_seconds, 3),
            engines_used=engines_used,
            artifacts=artifacts,
            warnings=warnings or [],
            errors=errors or [],
        )
