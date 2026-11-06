"""Video Intelligence API endpoints."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_session
from app.domain.schemas.api_response import APIResponse
from app.infrastructure.database.models import FileRecord, VideoAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.video_intelligence.pipeline import video_pipeline
from app.modules.video_intelligence.schemas.video_document import (
    TimelineEvent,
    VideoCapabilities,
    VideoDetection,
    VideoDocument,
    VideoKeyframe,
    VideoManifest,
    VideoScene,
    VideoTrack,
)

router = APIRouter(tags=["Video Intelligence"])


@router.get(
    "/video-intelligence/capabilities",
    response_model=APIResponse[VideoCapabilities],
    summary="Get video intelligence capabilities",
)
async def get_video_capabilities() -> APIResponse[VideoCapabilities]:
    """Retrieve platform video capabilities, supported formats, limits, and installed vision engines."""
    caps = video_pipeline.get_capabilities()
    return APIResponse.ok(data=caps, message="Video intelligence capabilities retrieved.")


@router.post(
    "/files/{file_id}/analyze-video",
    response_model=APIResponse[VideoManifest],
    summary="Analyze a video file",
    description="Probes stream parameters, detects scene cuts, extracts keyframes, runs OCR/tracking, and synchronizes audio transcript.",
)
async def analyze_video_file(
    file_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[VideoManifest]:
    """Trigger video intelligence pipeline for an ingested video recording."""
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
        _doc, manifest = await video_pipeline.process_and_persist(
            file_id=file_id,
            session=db,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video analysis failed: {exc}",
        ) from exc

    return APIResponse.ok(
        data=manifest,
        message=f"Video analysis completed with status: {manifest.status}",
    )


@router.get(
    "/files/{file_id}/video-analysis",
    response_model=APIResponse[dict[str, Any]],
    summary="Get video analysis overview record",
)
async def get_video_analysis(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve historical video analysis summary from PostgreSQL."""
    stmt = (
        select(VideoAnalysisRecord)
        .where(VideoAnalysisRecord.file_id == file_id)
        .order_by(desc(VideoAnalysisRecord.created_at))
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No video analysis found for file ID '{file_id}'.",
        )

    data = {
        "analysis_id": str(record.id),
        "file_id": str(record.file_id),
        "status": record.status,
        "format": record.format,
        "duration_seconds": record.duration_seconds,
        "width": record.width,
        "height": record.height,
        "fps": record.fps,
        "video_codec": record.video_codec,
        "audio_codec": record.audio_codec,
        "scene_count": record.scene_count,
        "keyframe_count": record.keyframe_count,
        "detection_count": record.detection_count,
        "track_count": record.track_count,
        "has_audio": record.has_audio,
        "has_transcript": record.has_transcript,
        "full_transcript_preview": record.full_transcript[:200] if record.full_transcript else "",
        "model_name": record.model_name,
        "engine_name": record.engine_name,
        "confidence": record.confidence,
        "processing_duration": record.processing_duration,
        "artifacts": record.artifacts,
        "warnings": record.warnings,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
    return APIResponse.ok(data=data, message="Video analysis record retrieved.")


async def _fetch_video_document(file_id: uuid.UUID, db: AsyncSession) -> VideoDocument:
    """Retrieve full canonical VideoDocument structure from artifact storage."""
    stmt = (
        select(VideoAnalysisRecord)
        .where(VideoAnalysisRecord.file_id == file_id)
        .order_by(desc(VideoAnalysisRecord.created_at))
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record or not record.artifacts.get("json"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analyzed video JSON artifact found for file ID '{file_id}'.",
        )

    json_rel_path = record.artifacts["json"]
    try:
        raw_bytes = await local_storage.read_file(json_rel_path)
        data = json.loads(raw_bytes.decode("utf-8"))
        return VideoDocument.model_validate(data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load canonical video document: {exc}",
        ) from exc


@router.get(
    "/files/{file_id}/video-analysis/result",
    response_model=APIResponse[VideoDocument],
    summary="Get canonical VideoDocument JSON",
)
async def get_video_document_result(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[VideoDocument]:
    """Retrieve the full parsed canonical VideoDocument representation."""
    doc = await _fetch_video_document(file_id, db)
    return APIResponse.ok(data=doc, message="Video document retrieved.")


@router.get(
    "/files/{file_id}/video-analysis/summary",
    response_model=APIResponse[dict[str, Any]],
    summary="Get executive summary of video analysis",
)
async def get_video_summary(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve executive summary including scene counts, tracks, transcript preview, and visual events."""
    doc = await _fetch_video_document(file_id=file_id, db=db)

    summary_data = {
        "document_id": doc.document_id,
        "filename": doc.metadata.filename,
        "format": doc.format,
        "duration_seconds": doc.duration,
        "resolution": f"{doc.video_streams[0].width}x{doc.video_streams[0].height}" if doc.video_streams else "0x0",
        "fps": doc.video_streams[0].fps if doc.video_streams else 0.0,
        "scene_count": len(doc.scenes),
        "keyframe_count": len(doc.keyframes),
        "tracked_objects_count": len(doc.tracks),
        "visual_events_count": len(doc.visual_events),
        "has_audio": bool(doc.audio_streams),
        "transcript_word_count": len(doc.transcript.split()) if doc.transcript else 0,
        "scenes_preview": [
            {
                "scene_id": s.scene_id,
                "start": s.start,
                "end": s.end,
                "duration": s.duration,
                "transition_type": s.transition_type,
                "visual_summary": s.visual_summary,
            }
            for s in doc.scenes[:10]
        ],
    }
    return APIResponse.ok(data=summary_data, message="Video summary retrieved.")


@router.get(
    "/files/{file_id}/video-analysis/scenes",
    response_model=APIResponse[list[VideoScene]],
    summary="Get all detected video scenes",
)
async def get_video_scenes(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[VideoScene]]:
    """Retrieve all visual scenes identified by boundary detection."""
    doc = await _fetch_video_document(file_id=file_id, db=db)
    return APIResponse.ok(data=doc.scenes, message=f"Retrieved {len(doc.scenes)} scenes.")


@router.get(
    "/files/{file_id}/video-analysis/scenes/{scene_id}",
    response_model=APIResponse[VideoScene],
    summary="Get specific scene details",
)
async def get_video_scene_by_id(
    file_id: uuid.UUID,
    scene_id: str,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[VideoScene]:
    """Retrieve detailed data for a single scene."""
    doc = await _fetch_video_document(file_id=file_id, db=db)
    for sc in doc.scenes:
        if sc.scene_id == scene_id:
            return APIResponse.ok(data=sc, message=f"Scene {scene_id} found.")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Scene '{scene_id}' not found in video analysis.",
    )


@router.get(
    "/files/{file_id}/video-analysis/keyframes",
    response_model=APIResponse[list[VideoKeyframe]],
    summary="Get all representative keyframes",
)
async def get_video_keyframes(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[VideoKeyframe]]:
    """Retrieve keyframe catalog with timestamps and asset storage paths."""
    doc = await _fetch_video_document(file_id=file_id, db=db)
    return APIResponse.ok(data=doc.keyframes, message=f"Retrieved {len(doc.keyframes)} keyframes.")


@router.get(
    "/files/{file_id}/video-analysis/timeline",
    response_model=APIResponse[list[TimelineEvent]],
    summary="Get unified multimodal timeline",
)
async def get_video_timeline(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[TimelineEvent]]:
    """Retrieve chronological multimodal timeline connecting scenes, speech, OCR, and tracks."""
    doc = await _fetch_video_document(file_id=file_id, db=db)
    return APIResponse.ok(data=doc.timeline, message=f"Retrieved {len(doc.timeline)} timeline events.")


@router.get(
    "/files/{file_id}/video-analysis/transcript",
    response_model=APIResponse[dict[str, Any]],
    summary="Get synchronized video transcript and speaker segments",
)
async def get_video_transcript(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve full text transcript and synchronized speaker utterances."""
    doc = await _fetch_video_document(file_id=file_id, db=db)
    data = {
        "file_id": str(file_id),
        "transcript": doc.transcript,
        "speakers": [s.model_dump() for s in doc.speakers],
        "segments": [seg.model_dump() for seg in doc.transcript_segments],
        "word_count": len(doc.transcript.split()) if doc.transcript else 0,
    }
    return APIResponse.ok(data=data, message="Video transcript retrieved.")


@router.get(
    "/files/{file_id}/video-analysis/detections",
    response_model=APIResponse[list[VideoDetection]],
    summary="Get frame-level object detections",
)
async def get_video_detections(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[VideoDetection]]:
    """Retrieve all frame-level bounding box detections."""
    doc = await _fetch_video_document(file_id=file_id, db=db)
    return APIResponse.ok(data=doc.detections, message=f"Retrieved {len(doc.detections)} detections.")


@router.get(
    "/files/{file_id}/video-analysis/tracks",
    response_model=APIResponse[list[VideoTrack]],
    summary="Get tracked object trajectories",
)
async def get_video_tracks(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[list[VideoTrack]]:
    """Retrieve continuous object trajectories tracked across frames."""
    doc = await _fetch_video_document(file_id=file_id, db=db)
    return APIResponse.ok(data=doc.tracks, message=f"Retrieved {len(doc.tracks)} tracks.")


@router.get(
    "/files/{file_id}/video-analysis/assets",
    response_model=APIResponse[dict[str, Any]],
    summary="Get video analysis storage asset catalog",
)
async def get_video_assets(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
) -> APIResponse[dict[str, Any]]:
    """Retrieve storage references for keyframe images, thumbnails, and generated exports."""
    stmt = (
        select(VideoAnalysisRecord)
        .where(VideoAnalysisRecord.file_id == file_id)
        .order_by(desc(VideoAnalysisRecord.created_at))
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No video analysis found for file ID '{file_id}'.",
        )

    return APIResponse.ok(
        data={"file_id": str(file_id), "artifacts": record.artifacts},
        message="Asset references retrieved.",
    )


@router.get(
    "/files/{file_id}/video-analysis/export/{format}",
    summary="Download video analysis export in specified format",
)
async def export_video_analysis(
    file_id: uuid.UUID,
    format: str,
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Download analysis artifacts in JSON, Markdown, Plain Text, SubRip (SRT), WebVTT, or Manifest."""
    fmt = format.lower().strip()
    valid_formats = {"json", "markdown", "md", "txt", "text", "srt", "vtt", "manifest", "keyframes_manifest"}
    if fmt not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid export format '{format}'. Supported: {sorted(valid_formats)}",
        )

    stmt = (
        select(VideoAnalysisRecord)
        .where(VideoAnalysisRecord.file_id == file_id)
        .order_by(desc(VideoAnalysisRecord.created_at))
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No video analysis found for file ID '{file_id}'.",
        )

    key_map = {
        "json": "json",
        "markdown": "markdown",
        "md": "markdown",
        "txt": "txt",
        "text": "txt",
        "srt": "srt",
        "vtt": "vtt",
        "manifest": "manifest",
        "keyframes_manifest": "keyframes_manifest",
    }
    artifact_key = key_map[fmt]
    rel_path = record.artifacts.get(artifact_key)

    if not rel_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export artifact for format '{format}' not found.",
        )

    content_bytes = await local_storage.read_file(rel_path)

    media_types = {
        "json": "application/json",
        "markdown": "text/markdown; charset=utf-8",
        "txt": "text/plain; charset=utf-8",
        "srt": "text/plain; charset=utf-8",
        "vtt": "text/vtt; charset=utf-8",
        "manifest": "application/json",
        "keyframes_manifest": "application/json",
    }
    extensions = {
        "json": "json",
        "markdown": "md",
        "txt": "txt",
        "srt": "srt",
        "vtt": "vtt",
        "manifest": "json",
        "keyframes_manifest": "json",
    }

    media_type = media_types.get(artifact_key, "application/octet-stream")
    ext = extensions.get(artifact_key, fmt)

    return Response(
        content=content_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="video_analysis_{file_id}.{ext}"'
        },
    )
