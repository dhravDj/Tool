"""Adapter for whisper.cpp C/C++ lightweight CLI backend."""

import json
import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from app.modules.audio_intelligence.schemas.audio_document import (
    AudioModelInfo,
    AudioSegment,
)
from app.modules.audio_intelligence.transcription.base import (
    BaseAudioTranscriptionAdapter,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


class WhisperCppAdapter(BaseAudioTranscriptionAdapter):
    """Integrates whisper.cpp for native compiled CPU/GPU transcription."""

    def __init__(
        self,
        model_name: str = "base",
        model_path: str | None = None,
        binary_path: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._model_path = model_path
        self._binary_path = binary_path or self._find_binary()

    @property
    def engine_name(self) -> str:
        return "whisper-cpp"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_available(self) -> bool:
        return self._binary_path is not None and (
            self._model_path is not None and os.path.exists(self._model_path)
        )

    def _find_binary(self) -> str | None:
        for candidate in ("whisper-cli", "whisper-cpp", "main"):
            p = shutil.which(candidate)
            if p:
                return p
        return None

    async def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        task: str = "transcribe",
        prompt: str | None = None,
    ) -> TranscriptionResult:
        if not self.is_available:
            raise RuntimeError(
                f"whisper.cpp binary ({self._binary_path}) or model ({self._model_path}) not configured."
            )

        assert self._binary_path is not None
        assert self._model_path is not None

        cmd = [
            self._binary_path,
            "-m",
            self._model_path,
            "-f",
            audio_path,
            "-oj",  # output JSON
        ]
        if language:
            cmd.extend(["-l", language])
        if prompt:
            cmd.extend(["--prompt", prompt])

        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
        if res.returncode != 0:
            raise RuntimeError(f"whisper.cpp execution failed: {res.stderr}")

        # JSON is saved to <audio_path>.json
        json_file = Path(f"{audio_path}.json")
        segments: list[AudioSegment] = []
        full_text = ""

        if json_file.exists():
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                for s in data.get("transcription", []):
                    t_start = float(s.get("timestamps", {}).get("from", "00:00:00,000").replace(",", ".").split(":")[-1])
                    t_end = float(s.get("timestamps", {}).get("to", "00:00:00,000").replace(",", ".").split(":")[-1])
                    text = s.get("text", "").strip()
                    segments.append(
                        AudioSegment(
                            segment_id=f"seg_{uuid.uuid4().hex[:8]}",
                            start=round(t_start, 3),
                            end=round(t_end, 3),
                            text=text,
                        )
                    )
                full_text = " ".join(s.text for s in segments)
                json_file.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"whisper.cpp JSON parse failed: {e}")

        return TranscriptionResult(
            text=full_text,
            language=language or "auto",
            language_confidence=0.90,
            segments=segments,
            confidence=0.90,
            model_info=AudioModelInfo(
                engine_name=self.engine_name,
                model_name=self.model_name,
                device="cpu",
                is_heuristic=False,
            ),
        )
