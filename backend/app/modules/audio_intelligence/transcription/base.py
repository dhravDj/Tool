"""Base interface for speech-to-text transcription adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.modules.audio_intelligence.schemas.audio_document import (
    AudioModelInfo,
    AudioSegment,
    AudioWord,
)


@dataclass
class TranscriptionResult:
    """Standardized output produced by any audio transcription adapter."""

    text: str
    language: str | None
    language_confidence: float | None
    segments: list[AudioSegment]
    words: list[AudioWord] = field(default_factory=list)
    confidence: float = 1.0
    warnings: list[str] = field(default_factory=list)
    model_info: AudioModelInfo = field(default_factory=AudioModelInfo)


class BaseAudioTranscriptionAdapter(ABC):
    """Abstract base class for all DocuMind AI speech recognition engines."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the transcription engine backend."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the speech model."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True if the engine dependencies and weights are installed and ready."""

    @abstractmethod
    async def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        task: str = "transcribe",
        prompt: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe speech in the given audio file into structured segments."""
