"""Audio speech-to-text adapters and transcription router."""

from app.modules.audio_intelligence.transcription.base import (
    BaseAudioTranscriptionAdapter,
    TranscriptionResult,
)
from app.modules.audio_intelligence.transcription.cloud_adapter import (
    CloudConsentError,
    CloudTranscriptionAdapter,
)
from app.modules.audio_intelligence.transcription.faster_whisper_adapter import (
    FasterWhisperAdapter,
)
from app.modules.audio_intelligence.transcription.local_acoustic import (
    LocalAcousticEngine,
)
from app.modules.audio_intelligence.transcription.router import (
    AudioTranscriptionRouter,
)
from app.modules.audio_intelligence.transcription.whisper_cpp_adapter import (
    WhisperCppAdapter,
)

__all__ = [
    "AudioTranscriptionRouter",
    "BaseAudioTranscriptionAdapter",
    "CloudConsentError",
    "CloudTranscriptionAdapter",
    "FasterWhisperAdapter",
    "LocalAcousticEngine",
    "TranscriptionResult",
    "WhisperCppAdapter",
]
