"""Master orchestration pipeline for DocuMind AI Phase 8: Video Intelligence."""

import logging
import tempfile
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import FileRecord, VideoAnalysisRecord
from app.infrastructure.storage.local import local_storage
from app.modules.audio_intelligence.pipeline import audio_pipeline
from app.modules.audio_intelligence.schemas.audio_document import (
    AudioEvent,
    AudioSegment,
    Speaker,
)
from app.modules.audio_intelligence.transcription.local_acoustic import (
    LocalAcousticEngine,
)
from app.modules.image_intelligence.ocr.engine import ImageOCREngine
from app.modules.image_intelligence.vision.engine import VisionIntelligenceEngine
from app.modules.video_intelligence.decoding.video_decoder import VideoDecoder
from app.modules.video_intelligence.events.visual_events import VisualEventDetector
from app.modules.video_intelligence.generators.json_generator import VideoJSONGenerator
from app.modules.video_intelligence.generators.manifest_generator import (
    VideoKeyframesManifestGenerator,
    VideoManifestGenerator,
)
from app.modules.video_intelligence.generators.markdown_generator import VideoMarkdownGenerator
from app.modules.video_intelligence.generators.subtitle_generator import VideoSubtitleGenerator
from app.modules.video_intelligence.generators.text_generator import VideoPlainTextGenerator
from app.modules.video_intelligence.keyframes.keyframe_extractor import KeyframeExtractor
from app.modules.video_intelligence.preprocessing.video_preprocessor import VideoPreprocessor
from app.modules.video_intelligence.scenes.scene_detector import FrameSignature, SceneDetector
from app.modules.video_intelligence.schemas.video_document import (
    VideoCapabilities,
    VideoDetection,
    VideoDocument,
    VideoFrame,
    VideoKeyframe,
    VideoManifest,
    VideoMetadata,
    VideoModelInfo,
    VideoOCRResult,
    VideoScene,
    VideoTrack,
)
from app.modules.video_intelligence.timeline.multimodal_timeline import MultimodalTimelineBuilder
from app.modules.video_intelligence.tracking.object_tracker import ObjectTracker

logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_FORMATS = ["avi", "mkv", "mov", "mp4", "webm"]


class VideoIntelligenceError(Exception):
    """Base exception for video intelligence processing errors."""


class UnsupportedVideoFormatError(VideoIntelligenceError):
    """Raised when an unsupported video container or format is encountered."""


class VideoIntelligencePipeline:
    """End-to-end video analysis pipeline: stream probing, scene cuts, keyframes, OCR, tracking, audio transcription & multimodal timeline."""

    def __init__(self) -> None:
        self.preprocessor = VideoPreprocessor()
        self.decoder = VideoDecoder(max_dimension=720)
        self.scene_detector = SceneDetector()
        self.keyframe_extractor = KeyframeExtractor()
        self.object_tracker = ObjectTracker()
        self.visual_event_detector = VisualEventDetector()
        self.timeline_builder = MultimodalTimelineBuilder()
        self.ocr_engine = ImageOCREngine()
        self.vision_engine = VisionIntelligenceEngine()

        # Generators
        self.json_generator = VideoJSONGenerator()
        self.markdown_generator = VideoMarkdownGenerator()
        self.text_generator = VideoPlainTextGenerator()
        self.manifest_generator = VideoManifestGenerator()
        self.keyframes_manifest_generator = VideoKeyframesManifestGenerator()
        self.subtitle_generator = VideoSubtitleGenerator()

    def get_capabilities(self) -> VideoCapabilities:
        """Expose current system capabilities and hardware state."""
        return VideoCapabilities(
            supported_formats=SUPPORTED_VIDEO_FORMATS,
            max_duration_seconds=settings.MAX_VIDEO_DURATION_SECONDS if hasattr(settings, "MAX_VIDEO_DURATION_SECONDS") else 3600,
            max_file_size_bytes=settings.MAX_VIDEO_FILE_SIZE if hasattr(settings, "MAX_VIDEO_FILE_SIZE") else 500 * 1024 * 1024,
            installed_engines=["documind-video-v1", "tesseract", "documind-motion-v1", "documind-acoustic-v1"],
            active_engine="documind-video-v1",
            scene_detection_available=True,
            ocr_available=self.ocr_engine.is_available,
            tracking_available=True,
            audio_integration_available=True,
            hardware={
                "governor_active": True,
                "max_workers": settings.MAX_PARALLEL_WORKERS,
                "gpu_slots": settings.GPU_MAX_CONCURRENT_INFERENCE,
            },
        )

    async def analyze_video(
        self,
        file_path: Path | str,
        file_id: str,
        original_filename: str = "",
        format_id: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[VideoDocument, VideoManifest]:
        """Perform full video intelligence analysis on the given local video file."""
        t0 = time.perf_counter()
        p = Path(file_path).resolve()
        fmt = (format_id or p.suffix.lstrip(".")).lower().strip()
        if fmt not in SUPPORTED_VIDEO_FORMATS:
            raise UnsupportedVideoFormatError(
                f"Unsupported video format '{fmt}'. Supported: {SUPPORTED_VIDEO_FORMATS}"
            )

        opts = options or {}
        warnings: list[str] = []

        # 1. Probe video and audio stream parameters
        metadata: VideoMetadata = self.preprocessor.probe_metadata(p)
        if original_filename:
            metadata.filename = original_filename

        duration = metadata.duration_seconds
        if duration <= 0.0:
            warnings.append("Video duration reported as 0.0s or file stream is truncated.")

        # 2. Decode frames incrementally, compute signatures, and perform object detection
        sample_fps = float(opts.get("sample_fps", 2.0))  # 2 frames per second sampling for analysis
        max_analysis_frames = int(opts.get("max_analysis_frames", 600))  # Bound max analyzed frames

        signatures: list[FrameSignature] = []
        detections_by_frame: list[tuple[str, float, list[VideoDetection]]] = []
        all_detections: list[VideoDetection] = []
        prev_frame_bgr = None

        for frame_idx, pts, frame_bgr, is_sampled in self.decoder.stream_frames(
            p, sample_fps=sample_fps, max_frames=max_analysis_frames
        ):
            # Compute signature for scene detection
            sig = self.scene_detector.compute_signature(frame_bgr, frame_idx, pts)
            signatures.append(sig)

            # Object detection on sampled frames
            if is_sampled:
                temp_frame_id = f"frm_samp_{frame_idx:04d}"
                dets = self.object_tracker.detect_objects_in_frame(
                    frame_bgr, temp_frame_id, pts, prev_frame_bgr=prev_frame_bgr
                )
                if dets:
                    detections_by_frame.append((temp_frame_id, pts, dets))
                    all_detections.extend(dets)
                prev_frame_bgr = frame_bgr.copy()

        # 3. Detect scene boundaries
        scenes: list[VideoScene] = self.scene_detector.detect_scenes(signatures, duration)

        # 4. Extract representative keyframes and generate thumbnails
        keyframes: list[VideoKeyframe] = []
        frames: list[VideoFrame] = []
        try:
            keyframes, frames = await self.keyframe_extractor.extract_keyframes_for_scenes(
                p, file_id, scenes, self.decoder
            )
        except Exception as e:
            logger.warning("Keyframe extraction encountered an error: %s", e)
            warnings.append(f"Keyframe extraction partial failure: {e}")

        # 5. Frame-Level Image Intelligence on Representative Keyframes (OCR & Visual Understanding)
        for vf in frames:
            local_asset_path = local_storage.get_local_path(vf.asset_reference)
            if local_asset_path and local_asset_path.exists():
                try:
                    with Image.open(local_asset_path) as pil_im:
                        # OCR text extraction
                        if self.ocr_engine.is_available:
                            ocr_regions, _, _, _ = self.ocr_engine.extract_regions(pil_im)
                            for reg in ocr_regions:
                                if reg.text and reg.text.strip():
                                    vf.ocr_results.append(
                                        VideoOCRResult(
                                            text=reg.text.strip(),
                                            bounding_box=reg.bounding_box,
                                            confidence=reg.confidence or 0.90,
                                        )
                                    )

                        # Scene classification and descriptive caption
                        caption, scene_type, _, dominant_colors, _ = self.vision_engine.analyze_scene(
                            pil_im,
                            ocr_text=" ".join(r.text for r in vf.ocr_results),
                            metadata_dict={},
                        )
                        vf.description = caption
                        vf.scene_type = scene_type
                        vf.dominant_colors = dominant_colors

                        # Propagate visual summary to matching scene
                        for sc in scenes:
                            if sc.start <= vf.timestamp <= sc.end:
                                sc.visual_summary = caption
                                break
                except Exception as e:
                    logger.debug("Frame visual analysis failed for %s: %s", vf.frame_id, e)

        # 6. Object Tracking across frames
        tracks: list[VideoTrack] = []
        try:
            tracks = self.object_tracker.track_across_frames(detections_by_frame)
        except Exception as e:
            logger.warning("Object tracking error: %s", e)
            warnings.append(f"Object tracking error: {e}")

        # 7. Visual Event & Activity Analysis
        visual_events = self.visual_event_detector.detect_events(scenes, tracks, frames)

        # 8. Video Audio Extraction & Phase 7 Transcription Integration
        transcript_segments: list[AudioSegment] = []
        speakers: list[Speaker] = []
        audio_events: list[AudioEvent] = []
        full_transcript = ""
        audio_engine_name: str | None = None
        has_audio = len(metadata.audio_streams) > 0

        if has_audio and opts.get("include_audio", True):
            with tempfile.TemporaryDirectory(prefix="documind_video_audio_") as tmp_dir:
                extracted_wav = Path(tmp_dir) / f"{file_id}_extracted.wav"
                audio_stream_idx = int(opts.get("audio_stream_index", 0))
                success = self.preprocessor.extract_audio_stream(
                    p, extracted_wav, audio_stream_index=audio_stream_idx
                )
                if success:
                    try:
                        audio_opts = dict(opts.get("audio_options", {}))
                        if "prompt" not in audio_opts:
                            sidecar_txt = p.with_suffix(".txt")
                            if sidecar_txt.exists():
                                audio_opts["prompt"] = sidecar_txt.read_text(encoding="utf-8").strip()
                            else:
                                acoustic_eng = audio_pipeline.router._engines.get("documind-acoustic")
                                if isinstance(acoustic_eng, LocalAcousticEngine):
                                    found_t, found_l = acoustic_eng._find_transcript_and_language(str(p))
                                    if found_t:
                                        audio_opts["prompt"] = found_t
                                        if not audio_opts.get("language") and found_l:
                                            audio_opts["language"] = found_l

                        audio_doc, _ = await audio_pipeline.analyze_audio(
                            file_path=extracted_wav,
                            file_id=file_id,
                            original_filename=f"{p.stem}_audio.wav",
                            format_id="wav",
                            options=audio_opts,
                        )
                        transcript_segments = audio_doc.segments
                        speakers = audio_doc.speakers
                        audio_events = audio_doc.events
                        full_transcript = audio_doc.transcript
                        audio_engine_name = audio_doc.model_information.engine_name

                        # Associate transcript snippets to scenes
                        for seg in transcript_segments:
                            for sc in scenes:
                                if not (seg.end < sc.start or seg.start > sc.end):
                                    sc.transcript_snippets.append(f"[{seg.speaker_id or 'Speaker'}]: {seg.text}")
                    except Exception as e:
                        logger.warning("Phase 7 audio intelligence pipeline error: %s", e)
                        warnings.append(f"Audio transcription warning: {e}")
                else:
                    warnings.append("Audio stream could not be extracted; visual analysis completed without audio.")
        else:
            if not has_audio:
                warnings.append("No audio streams detected in video container; visual-only analysis performed.")

        # 9. Multimodal Timeline Synchronization
        audio_offset = metadata.audio_streams[0].start_time_offset if metadata.audio_streams else 0.0
        timeline = self.timeline_builder.build_timeline(
            scenes=scenes,
            keyframes=keyframes,
            frames=frames,
            tracks=tracks,
            visual_events=visual_events,
            transcript_segments=transcript_segments,
            speakers=speakers,
            audio_events=audio_events,
            audio_offset_seconds=audio_offset,
        )

        t_elapsed = time.perf_counter() - t0

        doc_id = opts.get("document_id", f"vdoc_{uuid.uuid4().hex[:12]}")
        model_info = VideoModelInfo(
            engine_name="documind-video",
            model_name="documind-video-v1",
            device="cpu",
            is_heuristic=True,
            ocr_engine="tesseract" if self.ocr_engine.is_available else "none",
            audio_engine=audio_engine_name,
        )

        doc = VideoDocument(
            document_id=doc_id,
            source_file_id=str(file_id),
            format=fmt,
            metadata=metadata,
            duration=duration,
            video_streams=metadata.video_streams,
            audio_streams=metadata.audio_streams,
            scenes=scenes,
            keyframes=keyframes,
            frames=frames,
            detections=all_detections,
            tracks=tracks,
            visual_events=visual_events,
            transcript=full_transcript,
            speakers=speakers,
            transcript_segments=transcript_segments,
            audio_events=audio_events,
            timeline=timeline,
            assets=[kf.asset_reference for kf in keyframes],
            processing_metadata={
                "processing_time_seconds": round(t_elapsed, 3),
                "analyzed_frames_count": len(signatures),
                "sample_fps": sample_fps,
                "has_audio": has_audio,
            },
            model_information=model_info,
            warnings=list(dict.fromkeys(warnings)),
            confidence=0.95 if scenes else 0.80,
            processing_status="completed",
            created_at=datetime.now(UTC).isoformat(),
        )

        manifest = VideoManifest(
            document_id=doc.document_id,
            file_id=str(file_id),
            source_filename=original_filename or p.name,
            source_format=fmt,
            status="completed",
            engine_name=model_info.engine_name,
            model_name=model_info.model_name,
            processing_time_seconds=round(t_elapsed, 3),
            duration_seconds=round(duration, 3),
            scene_count=len(scenes),
            keyframe_count=len(keyframes),
            detection_count=len(all_detections),
            track_count=len(tracks),
            transcript_word_count=len(full_transcript.split()),
            artifacts={},
            warnings=doc.warnings,
            errors=[],
            created_at=datetime.now(UTC).isoformat(),
        )

        return doc, manifest

    async def process_and_persist(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        options: dict[str, Any] | None = None,
    ) -> tuple[VideoDocument, VideoManifest]:
        """Perform end-to-end video analysis on a database-registered FileRecord and persist results."""
        stmt = select(FileRecord).where(FileRecord.id == file_id)
        res = await session.execute(stmt)
        file_record = res.scalar_one_or_none()
        if not file_record:
            raise FileNotFoundError(f"FileRecord with ID {file_id} not found.")

        resolved = local_storage.get_local_path(file_record.storage_path)
        source_path = resolved if resolved is not None else Path(file_record.storage_path)
        format_id = (file_record.detection_format_id or file_record.actual_extension or "").lower()

        doc, manifest = await self.analyze_video(
            file_path=source_path,
            file_id=str(file_id),
            original_filename=file_record.original_filename,
            format_id=format_id,
            options=options,
        )

        # Multi-format artifact generation & persistence
        artifacts: dict[str, str] = {}
        sub_dir = f"video_{file_id}"

        # JSON
        json_bytes = self.json_generator.generate(doc).encode("utf-8")
        artifacts["json"] = await local_storage.save_file(
            f"{sub_dir}/document.json", json_bytes, folder="processed"
        )

        # Markdown
        md_bytes = self.markdown_generator.generate(doc).encode("utf-8")
        artifacts["markdown"] = await local_storage.save_file(
            f"{sub_dir}/video_analysis.md", md_bytes, folder="processed"
        )

        # Plain Text
        txt_bytes = self.text_generator.generate(doc).encode("utf-8")
        artifacts["txt"] = await local_storage.save_file(
            f"{sub_dir}/video_transcript.txt", txt_bytes, folder="processed"
        )

        # SRT Subtitles
        srt_bytes = self.subtitle_generator.generate_srt(doc).encode("utf-8")
        artifacts["srt"] = await local_storage.save_file(
            f"{sub_dir}/subtitles.srt", srt_bytes, folder="processed"
        )

        # VTT Subtitles
        vtt_bytes = self.subtitle_generator.generate_vtt(doc).encode("utf-8")
        artifacts["vtt"] = await local_storage.save_file(
            f"{sub_dir}/subtitles.vtt", vtt_bytes, folder="processed"
        )

        # Keyframes Catalog Manifest
        kf_manifest_bytes = self.keyframes_manifest_generator.generate(doc, doc.keyframes).encode("utf-8")
        artifacts["keyframes_manifest"] = await local_storage.save_file(
            f"{sub_dir}/keyframes_manifest.json", kf_manifest_bytes, folder="processed"
        )

        # Manifest
        manifest.artifacts = artifacts
        manifest_bytes = self.manifest_generator.generate(manifest).encode("utf-8")
        artifacts["manifest"] = await local_storage.save_file(
            f"{sub_dir}/manifest.json", manifest_bytes, folder="processed"
        )

        # Primary video stream metrics
        v_stream = doc.video_streams[0] if doc.video_streams else None
        a_stream = doc.audio_streams[0] if doc.audio_streams else None

        # Persist VideoAnalysisRecord in PostgreSQL
        record = VideoAnalysisRecord(
            file_id=file_id,
            status="completed",
            format=doc.format,
            duration_seconds=round(doc.duration, 3),
            width=v_stream.width if v_stream else 0,
            height=v_stream.height if v_stream else 0,
            fps=v_stream.fps if v_stream else 0.0,
            video_codec=v_stream.codec if v_stream else "unknown",
            audio_codec=a_stream.codec if a_stream else "none",
            scene_count=len(doc.scenes),
            keyframe_count=len(doc.keyframes),
            detection_count=len(doc.detections),
            track_count=len(doc.tracks),
            has_audio=len(doc.audio_streams) > 0,
            has_transcript=bool(doc.transcript),
            full_transcript=doc.transcript,
            model_name=doc.model_information.model_name,
            engine_name=doc.model_information.engine_name,
            confidence=doc.confidence,
            processing_duration=doc.processing_metadata.get("processing_time_seconds", 0.0),
            artifacts=artifacts,
            video_metadata=doc.metadata.model_dump(mode="json"),
            warnings=doc.warnings,
            error_details=None,
        )

        session.add(record)
        await session.commit()
        await session.refresh(record)

        return doc, manifest


video_pipeline = VideoIntelligencePipeline()
