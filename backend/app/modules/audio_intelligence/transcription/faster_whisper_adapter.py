"""Adapter for faster-whisper (CTranslate2-based Whisper inference)."""

import logging
import uuid

from app.modules.audio_intelligence.schemas.audio_document import (
    AudioModelInfo,
    AudioSegment,
    AudioWord,
)
from app.modules.audio_intelligence.transcription.base import (
    BaseAudioTranscriptionAdapter,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


class FasterWhisperAdapter(BaseAudioTranscriptionAdapter):
    """Integrates faster-whisper CTranslate2 models for efficient local CPU/GPU inference."""

    def __init__(
        self,
        model_name: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._compute_type = compute_type
        self._model = None

    @property
    def engine_name(self) -> str:
        return "faster-whisper"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_available(self) -> bool:
        try:
            import faster_whisper  # noqa: F401

            return True
        except ImportError:
            return False

    def _load_model(self) -> None:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type=self._compute_type,
            )

    async def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        task: str = "transcribe",
        prompt: str | None = None,
    ) -> TranscriptionResult:
        if not self.is_available:
            raise RuntimeError(
                "faster-whisper is not installed. Run 'uv pip install faster-whisper' to enable."
            )

        self._load_model()
        assert self._model is not None

        segments_gen, info = self._model.transcribe(
            audio_path,
            language=language,
            task=task,
            initial_prompt=prompt,
            word_timestamps=True,
            beam_size=5,
        )

        segments: list[AudioSegment] = []
        all_words: list[AudioWord] = []
        full_text_parts: list[str] = []

        for seg in segments_gen:
            seg_words: list[AudioWord] = []
            if seg.words:
                for w in seg.words:
                    word_obj = AudioWord(
                        word_id=f"w_{uuid.uuid4().hex[:8]}",
                        text=w.word.strip(),
                        start=round(w.start, 3),
                        end=round(w.end, 3),
                        confidence=round(w.probability, 4) if hasattr(w, "probability") else None,
                    )
                    seg_words.append(word_obj)
                    all_words.append(word_obj)

            seg_obj = AudioSegment(
                segment_id=f"seg_{uuid.uuid4().hex[:8]}",
                start=round(seg.start, 3),
                end=round(seg.end, 3),
                text=seg.text.strip(),
                words=seg_words,
                confidence=round(getattr(seg, "avg_logprob", 0.0), 3),
            )
            segments.append(seg_obj)
            full_text_parts.append(seg.text.strip())

        full_text = " ".join(full_text_parts)

        return TranscriptionResult(
            text=full_text,
            language=info.language,
            language_confidence=round(info.language_probability, 3)
            if hasattr(info, "language_probability")
            else None,
            segments=segments,
            words=all_words,
            confidence=0.95,
            model_info=AudioModelInfo(
                engine_name=self.engine_name,
                model_name=self.model_name,
                device=self._device,
                quantization=self._compute_type,
                is_heuristic=False,
            ),
        )
