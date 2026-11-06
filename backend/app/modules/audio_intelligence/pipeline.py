"""Audio Intelligence Pipeline Orchestrator."""

import logging
import os
import tempfile
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import AudioAnalysisRecord, FileRecord
from app.infrastructure.storage.local import local_storage
from app.modules.audio_intelligence.diarization.diarizer import AudioDiarizer
from app.modules.audio_intelligence.events.event_detector import (
    SoundEventDetector,
)
from app.modules.audio_intelligence.generators.json_generator import (
    AudioJSONGenerator,
)
from app.modules.audio_intelligence.generators.manifest_generator import (
    AudioManifestGenerator,
)
from app.modules.audio_intelligence.generators.markdown_generator import (
    AudioMarkdownGenerator,
)
from app.modules.audio_intelligence.generators.srt_generator import (
    AudioSRTGenerator,
)
from app.modules.audio_intelligence.generators.text_generator import (
    AudioTextGenerator,
)
from app.modules.audio_intelligence.generators.vtt_generator import (
    AudioVTTGenerator,
)
from app.modules.audio_intelligence.preprocessing.audio_preprocessor import (
    AudioPreprocessor,
)
from app.modules.audio_intelligence.schemas.audio_document import (
    AudioCapabilities,
    AudioDocument,
    AudioManifest,
    AudioModelInfo,
    AudioSegment,
    AudioWord,
)
from app.modules.audio_intelligence.transcription.local_acoustic import (
    LocalAcousticEngine,
)
from app.modules.audio_intelligence.transcription.router import (
    AudioTranscriptionRouter,
)

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_FORMATS = ["aac", "flac", "m4a", "mp3", "ogg", "wav"]


class UnsupportedAudioFormatError(Exception):
    """Raised when an unhandled audio format is passed to audio intelligence."""


class AudioIntelligencePipeline:
    """Orchestrates probing, decoding, transcription, diarization, event detection,

    artifact generation, and database persistence.
    """

    def __init__(self) -> None:
        self.preprocessor = AudioPreprocessor()
        self.router = AudioTranscriptionRouter()
        self.diarizer = AudioDiarizer()
        self.event_detector = SoundEventDetector()

    def list_supported_formats(self) -> list[str]:
        return sorted(SUPPORTED_AUDIO_FORMATS)

    def get_capabilities(self) -> AudioCapabilities:
        router_caps = self.router.get_capabilities()
        return AudioCapabilities(
            supported_formats=self.list_supported_formats(),
            max_duration_seconds=7200.0,  # 2 hours default maximum
            max_file_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
            installed_engines=router_caps["installed_engines"],
            active_engine=router_caps["active_engine"],
            diarization_available=True,
            sound_events_available=True,
            hardware={
                "governor_active": True,
                "max_workers": settings.MAX_PARALLEL_WORKERS,
                "gpu_slots": settings.GPU_MAX_CONCURRENT_INFERENCE,
            },
        )

    async def analyze_audio(
        self,
        file_path: Path | str,
        file_id: str,
        original_filename: str = "",
        format_id: str | None = None,
        language: str | None = None,
        preferred_engine: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[AudioDocument, AudioManifest]:
        """Perform comprehensive end-to-end audio intelligence analysis on the given file."""
        t0 = time.perf_counter()
        p = Path(file_path).resolve()
        fmt = (format_id or p.suffix.lstrip(".")).lower().strip()
        if fmt not in SUPPORTED_AUDIO_FORMATS:
            raise UnsupportedAudioFormatError(
                f"Unsupported audio format '{fmt}'. Supported: {self.list_supported_formats()}"
            )

        opts = options or {}
        warnings: list[str] = []

        # 1. Probe stream metadata
        metadata = self.preprocessor.probe_metadata(p)
        duration = metadata.duration_seconds

        # Guard against zero-duration or corrupt files
        if duration <= 0.0:
            warnings.append("Audio duration is reported as 0.0s or stream is corrupted.")

        # Check if original input path has sidecar text or tags
        acoustic_eng = self.router._engines.get("documind-acoustic")
        initial_prompt = opts.get("prompt")
        if not initial_prompt and isinstance(acoustic_eng, LocalAcousticEngine):
            found_text, found_lang = acoustic_eng._find_transcript_and_language(str(p))
            if found_text:
                initial_prompt = found_text
                if not language and found_lang:
                    language = found_lang

        # Create temporary working directory for intermediate PCM slices
        with tempfile.TemporaryDirectory(prefix="documind_audio_") as tmp_dir:
            pcm_path = os.path.join(tmp_dir, "decoded_mono16k.wav")
            try:
                self.preprocessor.resample_to_pcm16_wav(
                    input_path=p,
                    output_path=pcm_path,
                    target_sample_rate=16000,
                    mono=True,
                )
                working_path = pcm_path
            except Exception as e:
                logger.warning(f"FFmpeg decoding to PCM WAV failed: {e}. Using original file.")
                working_path = str(p)
                warnings.append(f"PCM resampling fallback: {e}")

            # 2. Windowed chunking for long recordings
            chunks = self.preprocessor.generate_chunks(
                audio_file_path=working_path,
                total_duration=duration,
                temp_dir=tmp_dir,
            )

            all_segments: list[AudioSegment] = []
            all_words: list[AudioWord] = []
            detected_lang: str | None = language
            lang_confidence: float | None = None
            engine_info = AudioModelInfo()

            for chunk in chunks:
                chunk_res = await self.router.transcribe(
                    audio_path=chunk.file_path,
                    engine_name=preferred_engine,
                    language=language,
                    task="transcribe",
                    prompt=initial_prompt,
                    user_consent=opts.get("user_consent", False),
                )

                if not detected_lang and chunk_res.language:
                    detected_lang = chunk_res.language
                    lang_confidence = chunk_res.language_confidence
                engine_info = chunk_res.model_info

                # Offset chunk segments back to master audio timeline
                for seg in chunk_res.segments:
                    # Prevent duplicate text at overlap boundaries
                    if all_segments and seg.text.strip() and all_segments[-1].text.strip() == seg.text.strip():
                        continue

                    adj_start = round(chunk.start_seconds + seg.start, 3)
                    adj_end = round(min(duration, chunk.start_seconds + seg.end), 3)

                    adj_words: list[AudioWord] = []
                    for w in seg.words:
                        w_start = round(chunk.start_seconds + w.start, 3)
                        w_end = round(min(duration, chunk.start_seconds + w.end), 3)
                        w_obj = AudioWord(
                            word_id=w.word_id,
                            text=w.text,
                            start=w_start,
                            end=w_end,
                            confidence=w.confidence,
                        )
                        adj_words.append(w_obj)
                        all_words.append(w_obj)

                    adj_seg = AudioSegment(
                        segment_id=seg.segment_id,
                        start=adj_start,
                        end=adj_end,
                        text=seg.text,
                        speaker_id=seg.speaker_id,
                        words=adj_words,
                        confidence=seg.confidence,
                        source_chunk_id=chunk.chunk_id,
                    )
                    all_segments.append(adj_seg)

                if chunk_res.warnings:
                    warnings.extend(chunk_res.warnings)

            # 3. Speaker Diarization
            segments_diarized, speakers = self.diarizer.diarize_segments(
                audio_path=working_path,
                segments=all_segments,
            )

            # 4. Sound Event Detection
            events = self.event_detector.detect_events(working_path)

        # 5. Full transcript assembly
        full_transcript = " ".join(s.text.strip() for s in segments_diarized if s.text.strip())

        t_elapsed = time.perf_counter() - t0

        doc_id = opts.get("document_id", f"aud_{uuid.uuid4().hex[:12]}")
        doc = AudioDocument(
            document_id=doc_id,
            source_file_id=str(file_id),
            format=fmt,
            metadata=metadata,
            duration=duration,
            sample_rate=metadata.sample_rate,
            channels=metadata.channels,
            codec=metadata.codec,
            language=detected_lang,
            language_confidence=lang_confidence,
            transcript=full_transcript,
            segments=segments_diarized,
            speakers=speakers,
            events=events,
            processing_metadata={
                "processing_duration_seconds": round(t_elapsed, 3),
                "chunk_count": len(chunks),
                "chunks_windowed": len(chunks) > 1,
            },
            model_information=engine_info,
            warnings=list(dict.fromkeys(warnings)),
            confidence=0.95 if full_transcript else 0.80,
            processing_status="completed",
            created_at=datetime.now(UTC),
        )

        # Create dummy manifest (will be populated with actual artifact storage paths)
        manifest = AudioManifestGenerator.generate(
            doc=doc,
            source_filename=original_filename or Path(file_path).name,
            artifacts={},
        )
        return doc, manifest

    async def process_and_persist(
        self,
        file_id: uuid.UUID,
        session: AsyncSession,
        preferred_engine: str | None = None,
        language: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[AudioDocument, AudioManifest]:
        """Run complete audio intelligence on a registered FileRecord and persist analysis."""
        stmt = select(FileRecord).where(FileRecord.id == file_id)
        res = await session.execute(stmt)
        file_record = res.scalar_one_or_none()
        if not file_record:
            raise FileNotFoundError(f"FileRecord with ID {file_id} not found in database.")

        # Resolve stored file path
        resolved = local_storage.get_local_path(file_record.storage_path)
        source_path = resolved if resolved is not None else Path(file_record.storage_path)
        format_id = (file_record.detection_format_id or file_record.actual_extension or "").lower()

        doc, _ = await self.analyze_audio(
            file_path=source_path,
            file_id=str(file_id),
            original_filename=file_record.original_filename,
            format_id=format_id,
            language=language,
            preferred_engine=preferred_engine,
            options=options,
        )

        # Generate and save multi-format artifacts in local_storage
        artifacts: dict[str, str] = {}
        sub_dir = f"audio_{file_id}"

        # JSON
        json_content = AudioJSONGenerator.generate(doc).encode("utf-8")
        artifacts["json"] = await local_storage.save_file(
            f"{sub_dir}/document.json", json_content, folder="processed"
        )

        # Markdown
        md_content = AudioMarkdownGenerator.generate(
            doc, filename=file_record.original_filename
        ).encode("utf-8")
        artifacts["markdown"] = await local_storage.save_file(
            f"{sub_dir}/transcript.md", md_content, folder="processed"
        )

        # Plain Text
        txt_content = AudioTextGenerator.generate(doc).encode("utf-8")
        artifacts["txt"] = await local_storage.save_file(
            f"{sub_dir}/transcript.txt", txt_content, folder="processed"
        )

        # SRT Subtitles
        srt_content = AudioSRTGenerator.generate(doc).encode("utf-8")
        artifacts["srt"] = await local_storage.save_file(
            f"{sub_dir}/subtitles.srt", srt_content, folder="processed"
        )

        # VTT Subtitles
        vtt_content = AudioVTTGenerator.generate(doc).encode("utf-8")
        artifacts["vtt"] = await local_storage.save_file(
            f"{sub_dir}/subtitles.vtt", vtt_content, folder="processed"
        )

        # Manifest
        manifest = AudioManifestGenerator.generate(
            doc=doc,
            source_filename=file_record.original_filename,
            artifacts=artifacts,
        )
        manifest_content = manifest.model_dump_json(indent=2).encode("utf-8")
        artifacts["manifest"] = await local_storage.save_file(
            f"{sub_dir}/manifest.json", manifest_content, folder="processed"
        )

        # Persist AudioAnalysisRecord in PostgreSQL
        analysis_record = AudioAnalysisRecord(
            file_id=file_id,
            status="completed",
            format=doc.format,
            duration_seconds=round(doc.duration, 3),
            sample_rate=doc.sample_rate,
            channels=doc.channels,
            codec=doc.codec,
            detected_language=doc.language,
            language_confidence=doc.language_confidence,
            full_transcript=doc.transcript,
            speaker_count=len(doc.speakers),
            segment_count=len(doc.segments),
            event_count=len(doc.events),
            has_diarization=len(doc.speakers) > 0,
            has_word_timestamps=any(len(s.words) > 0 for s in doc.segments),
            has_events=len(doc.events) > 0,
            model_name=doc.model_information.model_name,
            engine_name=doc.model_information.engine_name,
            confidence=round(doc.confidence, 4),
            processing_duration=round(
                doc.processing_metadata.get("processing_duration_seconds", 0.0), 3
            ),
            artifacts=artifacts,
            audio_metadata=doc.metadata.model_dump(),
            warnings=doc.warnings,
            error_details=None,
        )
        session.add(analysis_record)
        await session.commit()
        await session.refresh(analysis_record)

        return doc, manifest


audio_pipeline = AudioIntelligencePipeline()

