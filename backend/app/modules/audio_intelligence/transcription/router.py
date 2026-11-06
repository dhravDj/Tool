"""Transcription engine router dispatching across local acoustic, faster-whisper, and whisper.cpp."""

import logging
from typing import Any

from app.core.hardware import HardwareGovernor
from app.modules.audio_intelligence.transcription.base import (
    BaseAudioTranscriptionAdapter,
    TranscriptionResult,
)
from app.modules.audio_intelligence.transcription.cloud_adapter import (
    CloudTranscriptionAdapter,
)
from app.modules.audio_intelligence.transcription.faster_whisper_adapter import (
    FasterWhisperAdapter,
)
from app.modules.audio_intelligence.transcription.local_acoustic import (
    LocalAcousticEngine,
)
from app.modules.audio_intelligence.transcription.whisper_cpp_adapter import (
    WhisperCppAdapter,
)

logger = logging.getLogger(__name__)


class AudioTranscriptionRouter:
    """Manages available speech-to-text engines and routes transcription requests."""

    def __init__(self, hardware_governor: HardwareGovernor | None = None) -> None:
        self.governor = hardware_governor or HardwareGovernor()
        self._engines: dict[str, BaseAudioTranscriptionAdapter] = {
            "documind-acoustic": LocalAcousticEngine(),
            "faster-whisper": FasterWhisperAdapter(),
            "whisper-cpp": WhisperCppAdapter(),
            "cloud": CloudTranscriptionAdapter(),
        }

    def get_capabilities(self) -> dict[str, Any]:
        """Return status and availability of all registered speech engines."""
        installed = [name for name, eng in self._engines.items() if eng.is_available]
        active = self.get_default_engine_name()
        return {
            "installed_engines": installed,
            "active_engine": active,
            "default_model": self._engines[active].model_name,
            "all_engines": {
                name: {
                    "engine_name": eng.engine_name,
                    "model_name": eng.model_name,
                    "is_available": eng.is_available,
                }
                for name, eng in self._engines.items()
            },
        }

    def get_default_engine_name(self) -> str:
        """Select highest-performing available local speech engine."""
        if self._engines["faster-whisper"].is_available:
            return "faster-whisper"
        if self._engines["whisper-cpp"].is_available:
            return "whisper-cpp"
        return "documind-acoustic"

    async def transcribe(
        self,
        audio_path: str,
        engine_name: str | None = None,
        language: str | None = None,
        task: str = "transcribe",
        prompt: str | None = None,
        user_consent: bool = False,
    ) -> TranscriptionResult:
        """Execute transcription under hardware governance slots."""
        target_engine_name = engine_name or self.get_default_engine_name()
        adapter = self._engines.get(target_engine_name)

        if not adapter or not adapter.is_available:
            logger.warning(
                f"Requested engine '{target_engine_name}' unavailable. Falling back to default."
            )
            target_engine_name = self.get_default_engine_name()
            adapter = self._engines[target_engine_name]

        # Acquire CPU or GPU hardware slot
        if getattr(adapter, "_device", "cpu") == "cuda":
            async with self.governor.gpu_bound_slot():
                return await adapter.transcribe(audio_path, language=language, task=task, prompt=prompt)
        else:
            async with self.governor.cpu_bound_slot():
                if isinstance(adapter, CloudTranscriptionAdapter):
                    return await adapter.transcribe(
                        audio_path,
                        language=language,
                        task=task,
                        prompt=prompt,
                        user_consent=user_consent,
                    )
                return await adapter.transcribe(
                    audio_path, language=language, task=task, prompt=prompt
                )
