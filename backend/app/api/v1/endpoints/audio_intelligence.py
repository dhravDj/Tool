"""Audio Intelligence API endpoints."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import AudioAnalysisRecord, FileRecord
from app.infrastructure.storage.local import local_storage
from app.modules.audio_intelligence.pipeline import audio_pipeline
from app.modules.audio_intelligence.schemas.audio_document import (
    AudioCapabilities,
    AudioDocument,
    AudioEvent,
    AudioManifest,
    AudioSegment,
    Speaker,
)

router = APIRouter(tags=["Audio Intelligence"])


@router.get(
    "/audio-intelligence/capabilities",
    response_model=APIResponse[AudioCapabilities],
    summary="Get audio intelligence capabilities",
)
async def get_audio_capabilities() -> APIResponse[AudioCapabilities]:
    """Retrieve platform audio capabilities, supported formats, limits, and active speech engines."""
    caps = audio_pipeline.get_capabilities()
    return APIResponse.ok(data=caps, message="Audio intelligence capabilities retrieved.")


@router.get(
    "/audio-intelligence/models",
    response_model=APIResponse[dict[str, Any]],
    summary="Get available speech and acoustic models",
)
async def get_audio_models() -> APIResponse[dict[str, Any]]:
    """Retrieve speech recognition engines, installed backends, and memory guidelines."""
    caps = audio_pipeline.router.get_capabilities()
    models_info = {
        "installed_engines": caps["installed_engines"],
        "active_engine": caps["active_engine"],
        "supported_models": [
            {
                "name": "documind-acoustic-v1",
                "engine": "documind-acoustic",
                "device": "cpu",
                "vram_mb": 0,
                "ram_mb": 50,
                "description": "Deterministic local acoustic baseline with VAD alignment and zero weight download.",
                "is_installed": True,
            },
            {
                "name": "base",
                "engine": "faster-whisper",
                "device": "cpu / cuda",
                "vram_mb": 500,
                "ram_mb": 800,
                "description": "Standard multilingual Whisper base model (74M parameters). Ideal for 4GB VRAM.",
                "is_installed": "faster-whisper" in caps["installed_engines"],
            },
            {
                "name": "small",
                "engine": "faster-whisper",
                "device": "cpu / cuda",
                "vram_mb": 1500,
                "ram_mb": 2000,
                "description": "Enhanced multilingual Whisper small model (244M parameters) with higher Hindi accuracy.",
                "is_installed": "faster-whisper" in caps["installed_engines"],
            },
            {
                "name": "whisper-base",
                "engine": "whisper-cpp",
                "device": "cpu",
                "vram_mb": 0,
                "ram_mb": 400,
                "description": "Lightweight C/C++ compiled Whisper execution.",
                "is_installed": "whisper-cpp" in caps["installed_engines"],
            },
        ],
        "hardware_recommendations": {
            "recommended_gpu_model": "base or small on RTX 3050 (4GB VRAM)",
            "batch_size": 1,
            "max_concurrent_gpu": 1,
        },
    }
    return APIResponse.ok(data=models_info, message="Audio models and backends listed.")


@router.post(
    "/files/{file_id}/analyze-audio",
    response_model=APIResponse[AudioManifest],
    summary="Analyze an audio file",
    description="Probes stream metadata, performs speech transcription, diarization, and sound event classification.",
)
async def analyze_audio_file(
    file_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[AudioManifest]:
    """Trigger audio intelligence pipeline for an ingested audio recording."""
    stmt = select(FileRecord).where(FileRecord.id == file_id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found.",
        )

    options = payload or {}

    try:
        _doc, manifest = await audio_pipeline.process_and_persist(
            file_id=file_id,
            session=db,
            preferred_engine=options.get("engine"),
            language=options.get("language"),
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio analysis failed: {exc}",
        ) from exc

    return APIResponse.ok(
        data=manifest,
        message=f"Audio analysis completed with status: {manifest.status}",
    )


@router.get(
    "/files/{file_id}/audio-analysis",
    response_model=APIResponse[dict[str, Any]],
    summary="Get audio analysis overview record",
)
async def get_audio_analysis(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve historical audio analysis summary from PostgreSQL."""
    stmt = (
        select(AudioAnalysisRecord)
        .where(AudioAnalysisRecord.file_id == file_id)
        .order_by(desc(AudioAnalysisRecord.created_at))
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audio analysis found for file ID '{file_id}'.",
        )

    data = {
        "analysis_id": str(record.id),
        "file_id": str(record.file_id),
        "status": record.status,
        "format": record.format,
        "duration_seconds": record.duration_seconds,
        "sample_rate": record.sample_rate,
        "channels": record.channels,
        "codec": record.codec,
        "detected_language": record.detected_language,
        "language_confidence": record.language_confidence,
        "full_transcript_preview": record.full_transcript[:200]
        if record.full_transcript
        else "",
        "speaker_count": record.speaker_count,
        "segment_count": record.segment_count,
        "event_count": record.event_count,
        "has_diarization": record.has_diarization,
        "has_word_timestamps": record.has_word_timestamps,
        "has_events": record.has_events,
        "model_name": record.model_name,
        "engine_name": record.engine_name,
        "confidence": record.confidence,
        "processing_duration": record.processing_duration,
        "artifacts": record.artifacts,
        "warnings": record.warnings,
        "created_at": record.created_at.isoformat(),
    }
    return APIResponse.ok(data=data, message="Audio analysis record retrieved.")


@router.get(
    "/files/{file_id}/audio-analysis/result",
    response_model=APIResponse[AudioDocument],
    summary="Get canonical AudioDocument result",
)
async def get_audio_document_result(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[AudioDocument]:
    """Retrieve full canonical AudioDocument structure from artifact storage."""
    stmt = (
        select(AudioAnalysisRecord)
        .where(AudioAnalysisRecord.file_id == file_id)
        .order_by(desc(AudioAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record or not record.artifacts.get("json"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analyzed audio JSON artifact found for file ID '{file_id}'.",
        )

    json_rel_path = record.artifacts["json"]
    try:
        content_bytes = await local_storage.read_file(json_rel_path)
        data = json.loads(content_bytes.decode("utf-8"))
        doc = AudioDocument.model_validate(data)
        return APIResponse.ok(data=doc, message="AudioDocument retrieved successfully.")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load AudioDocument: {exc}",
        ) from exc


@router.get(
    "/files/{file_id}/audio-analysis/transcript",
    response_model=APIResponse[dict[str, Any]],
    summary="Get full audio transcript",
)
async def get_audio_transcript(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve complete speech transcript with detected language."""
    stmt = (
        select(AudioAnalysisRecord)
        .where(AudioAnalysisRecord.file_id == file_id)
        .order_by(desc(AudioAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audio analysis found for file ID '{file_id}'.",
        )

    return APIResponse.ok(
        data={
            "file_id": str(file_id),
            "transcript": record.full_transcript,
            "detected_language": record.detected_language,
            "language_confidence": record.language_confidence,
            "word_count": len(record.full_transcript.split()) if record.full_transcript else 0,
        },
        message="Transcript retrieved successfully.",
    )


@router.get(
    "/files/{file_id}/audio-analysis/segments",
    response_model=APIResponse[list[AudioSegment]],
    summary="Get speech segments with timestamps",
)
async def get_audio_segments(
    file_id: uuid.UUID,
    q: str | None = Query(None, description="Optional search filter string within segment text"),
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[AudioSegment]]:
    """Retrieve timestamped speech segments with optional in-transcript text search."""
    stmt = (
        select(AudioAnalysisRecord)
        .where(AudioAnalysisRecord.file_id == file_id)
        .order_by(desc(AudioAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record or not record.artifacts.get("json"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audio segments found for file ID '{file_id}'.",
        )

    content_bytes = await local_storage.read_file(record.artifacts["json"])
    doc = AudioDocument.model_validate_json(content_bytes)

    segments = doc.segments
    if q and q.strip():
        search_term = q.strip().lower()
        segments = [s for s in segments if search_term in s.text.lower()]

    return APIResponse.ok(
        data=segments,
        message=f"Retrieved {len(segments)} segment(s).",
    )


@router.get(
    "/files/{file_id}/audio-analysis/speakers",
    response_model=APIResponse[list[Speaker]],
    summary="Get speaker diarization profiles",
)
async def get_audio_speakers(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[Speaker]]:
    """Retrieve anonymous speaker profiles and attributed speech turns."""
    stmt = (
        select(AudioAnalysisRecord)
        .where(AudioAnalysisRecord.file_id == file_id)
        .order_by(desc(AudioAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record or not record.artifacts.get("json"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No speaker analysis found for file ID '{file_id}'.",
        )

    content_bytes = await local_storage.read_file(record.artifacts["json"])
    doc = AudioDocument.model_validate_json(content_bytes)

    return APIResponse.ok(
        data=doc.speakers,
        message=f"Retrieved {len(doc.speakers)} speaker profile(s).",
    )


@router.get(
    "/files/{file_id}/audio-analysis/events",
    response_model=APIResponse[list[AudioEvent]],
    summary="Get classified sound events",
)
async def get_audio_events(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[AudioEvent]]:
    """Retrieve acoustic and environmental sound events (Music, Silence, Applause, Noise)."""
    stmt = (
        select(AudioAnalysisRecord)
        .where(AudioAnalysisRecord.file_id == file_id)
        .order_by(desc(AudioAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record or not record.artifacts.get("json"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sound events found for file ID '{file_id}'.",
        )

    content_bytes = await local_storage.read_file(record.artifacts["json"])
    doc = AudioDocument.model_validate_json(content_bytes)

    return APIResponse.ok(
        data=doc.events,
        message=f"Retrieved {len(doc.events)} event(s).",
    )


@router.get(
    "/files/{file_id}/audio-analysis/summary",
    response_model=APIResponse[dict[str, Any]],
    summary="Get executive summary of audio recording",
)
async def get_audio_summary(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve executive summary and key metrics of analyzed recording."""
    stmt = (
        select(AudioAnalysisRecord)
        .where(AudioAnalysisRecord.file_id == file_id)
        .order_by(desc(AudioAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis record found for file ID '{file_id}'.",
        )

    summary_data = {
        "file_id": str(file_id),
        "duration_seconds": record.duration_seconds,
        "format": record.format,
        "codec": record.codec,
        "detected_language": record.detected_language,
        "speaker_count": record.speaker_count,
        "segment_count": record.segment_count,
        "event_count": record.event_count,
        "model_name": record.model_name,
        "engine_name": record.engine_name,
        "confidence": record.confidence,
    }
    return APIResponse.ok(data=summary_data, message="Audio summary retrieved.")


@router.get(
    "/files/{file_id}/audio-analysis/export/{format}",
    summary="Export audio analysis in requested format",
)
async def export_audio_analysis(
    file_id: uuid.UUID,
    format: str,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Download audio analysis in JSON, Markdown, TXT, SRT, or VTT format."""
    fmt = format.lower().strip()
    valid_formats = {"json", "md", "markdown", "txt", "srt", "vtt"}
    if fmt not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid export format '{format}'. Valid options: {sorted(valid_formats)}",
        )

    stmt = (
        select(AudioAnalysisRecord)
        .where(AudioAnalysisRecord.file_id == file_id)
        .order_by(desc(AudioAnalysisRecord.created_at))
    )
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audio analysis found for file ID '{file_id}'.",
        )

    key = "markdown" if fmt in ("md", "markdown") else fmt
    rel_path = record.artifacts.get(key)
    if not rel_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export artifact for format '{format}' not found.",
        )

    content_bytes = await local_storage.read_file(rel_path)

    media_types = {
        "json": "application/json",
        "md": "text/markdown; charset=utf-8",
        "markdown": "text/markdown; charset=utf-8",
        "txt": "text/plain; charset=utf-8",
        "srt": "text/plain; charset=utf-8",
        "vtt": "text/vtt; charset=utf-8",
    }
    return Response(
        content=content_bytes,
        media_type=media_types.get(fmt, "text/plain"),
        headers={
            "Content-Disposition": f'attachment; filename="audio_analysis_{file_id}.{fmt}"'
        },
    )
