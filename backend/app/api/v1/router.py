"""API v1 root router combining all domain endpoint modules."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_intelligence,
    archive_intelligence,
    audio_intelligence,
    batches,
    code_intelligence,
    detection,
    extraction,
    files,
    formats,
    health,
    image_intelligence,
    plugins,
    presentation_intelligence,
    spreadsheet_intelligence,
    structured_data_intelligence,
    system,
    video_intelligence,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(plugins.router)
api_router.include_router(system.router)
api_router.include_router(files.router)
api_router.include_router(batches.router)
api_router.include_router(formats.router)
api_router.include_router(detection.router)
api_router.include_router(extraction.router)
api_router.include_router(image_intelligence.router)
api_router.include_router(spreadsheet_intelligence.router)
api_router.include_router(presentation_intelligence.router)
api_router.include_router(audio_intelligence.router)
api_router.include_router(video_intelligence.router)
api_router.include_router(code_intelligence.router)
api_router.include_router(structured_data_intelligence.router)
api_router.include_router(archive_intelligence.router)
api_router.include_router(ai_intelligence.router)
