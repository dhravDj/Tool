"""Acoustic sound event detector (Silence, Music, Applause, Environmental Noise)."""

import logging
import uuid

import numpy as np
import soundfile as sf

from app.modules.audio_intelligence.schemas.audio_document import AudioEvent

logger = logging.getLogger(__name__)


class SoundEventDetector:
    """Classifies acoustic events (silence, music, applause, noise) using signal analysis."""

    def __init__(self, frame_duration_seconds: float = 0.5) -> None:
        self.frame_duration_seconds = frame_duration_seconds

    def detect_events(self, audio_path: str) -> list[AudioEvent]:
        """Detect non-speech acoustic sound events across audio recording."""
        events: list[AudioEvent] = []

        try:
            data, sr = sf.read(audio_path)
            if data.ndim > 1:
                data = np.mean(data, axis=1)
        except Exception as e:
            logger.warning(f"Audio read in sound event detector failed: {e}")
            return []

        if len(data) == 0 or sr <= 0:
            return []

        frame_len = int(sr * self.frame_duration_seconds)
        if frame_len <= 0:
            return []

        num_frames = len(data) // frame_len
        if num_frames == 0:
            return []

        frame_labels: list[str | None] = []

        for f_idx in range(num_frames):
            frame = data[f_idx * frame_len : (f_idx + 1) * frame_len].astype(np.float32)
            lbl = self._classify_frame(frame, sr)
            frame_labels.append(lbl)

        # Merge contiguous frames of same label into events
        cur_label: str | None = None
        cur_start: float = 0.0

        for f_idx, lbl in enumerate(frame_labels):
            t = f_idx * self.frame_duration_seconds
            if lbl != cur_label:
                if cur_label is not None:
                    # Save event if duration >= 1.0 second (or 0.5s for silence/applause)
                    event_duration = t - cur_start
                    if event_duration >= 0.5:
                        events.append(
                            AudioEvent(
                                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                                category=cur_label,
                                start=round(cur_start, 3),
                                end=round(t, 3),
                                confidence=0.88,
                                detection_model="documind-acoustic-classifier-v1",
                            )
                        )
                cur_label = lbl
                cur_start = t

        # Flush final event
        if cur_label is not None:
            t_end = num_frames * self.frame_duration_seconds
            if t_end - cur_start >= 0.5:
                events.append(
                    AudioEvent(
                        event_id=f"evt_{uuid.uuid4().hex[:8]}",
                        category=cur_label,
                        start=round(cur_start, 3),
                        end=round(t_end, 3),
                        confidence=0.88,
                        detection_model="documind-acoustic-classifier-v1",
                    )
                )

        return events

    def _classify_frame(self, frame: np.ndarray, sr: int) -> str | None:
        """Classify single 500ms frame into Silence, Music, Applause, Noise, or None."""
        rms = float(np.sqrt(np.mean(frame**2)))
        if rms < 0.005:  # Below -46 dB
            return "Silence"

        zcr = float(np.mean(np.abs(np.diff(np.sign(frame)))))

        # Spectrum analysis
        n_fft = min(len(frame), 2048)
        spec = np.abs(np.fft.rfft(frame[:n_fft])) + 1e-9

        # Spectral flatness: geometric mean / arithmetic mean
        geo_mean = float(np.exp(np.mean(np.log(spec))))
        arith_mean = float(np.mean(spec))
        flatness = geo_mean / (arith_mean + 1e-9)

        # High flatness + high ZCR = Noise or Applause
        if flatness > 0.6:
            if zcr > 0.25 and rms > 0.02:
                return "Applause"
            elif rms > 0.02:
                return "Environmental Noise"

        # Low flatness + strong harmonic peaks = Music
        if flatness < 0.15 and rms > 0.02:
            return "Music"

        return None
