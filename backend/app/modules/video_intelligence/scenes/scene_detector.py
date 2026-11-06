"""Content-aware visual scene boundary detection."""

import logging
from dataclasses import dataclass

import cv2
import numpy as np

from app.modules.video_intelligence.schemas.video_document import VideoScene

logger = logging.getLogger(__name__)


@dataclass
class FrameSignature:
    """Compact perceptual signature of a single video frame."""

    frame_index: int
    timestamp: float
    hist: np.ndarray
    mean_luminance: float


class SceneDetector:
    """Detects hard cuts, gradual fades, and transitions using perceptual difference metrics."""

    def __init__(
        self,
        cut_threshold: float = 0.35,
        fade_luminance_threshold: float = 12.0,
        min_scene_duration_seconds: float = 0.5,
    ) -> None:
        self.cut_threshold = cut_threshold
        self.fade_luminance_threshold = fade_luminance_threshold
        self.min_scene_duration = min_scene_duration_seconds

    def compute_signature(self, frame_bgr: np.ndarray, frame_index: int, timestamp: float) -> FrameSignature:
        """Calculate normalized 2D HSV color histogram and mean luminance."""
        # Convert to HSV
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        # Compute 16x16 Hue-Sat histogram
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

        # Mean luminance in grayscale
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        mean_lum = float(np.mean(gray))

        return FrameSignature(
            frame_index=frame_index,
            timestamp=timestamp,
            hist=hist,
            mean_luminance=mean_lum,
        )

    def detect_scenes(
        self,
        signatures: list[FrameSignature],
        total_duration: float,
    ) -> list[VideoScene]:
        """Group frame signatures into distinct temporal scenes."""
        if not signatures:
            # Single fallback scene
            return [
                VideoScene(
                    scene_id="scene_001",
                    start=0.0,
                    end=max(0.1, total_duration),
                    duration=max(0.1, total_duration),
                    start_frame=0,
                    end_frame=0,
                    transition_type="continuous",
                    confidence=1.0,
                )
            ]

        cut_points: list[tuple[int, float, str]] = []  # (frame_idx, timestamp, transition_type)
        prev_sig = signatures[0]

        for sig in signatures[1:]:
            # 1. Histogram correlation / distance
            # cv2.HISTCMP_CORREL returns 1 for identical, -1 to 0 for very different
            correlation = cv2.compareHist(prev_sig.hist, sig.hist, cv2.HISTCMP_CORREL)
            diff_score = 1.0 - max(0.0, correlation)

            # 2. Fade detection (luminance drops below threshold or jumps sharply)
            is_fade = (
                prev_sig.mean_luminance < self.fade_luminance_threshold
                and sig.mean_luminance >= self.fade_luminance_threshold
            ) or (
                prev_sig.mean_luminance >= self.fade_luminance_threshold
                and sig.mean_luminance < self.fade_luminance_threshold
            )

            # 3. Check cut threshold
            if diff_score >= self.cut_threshold or is_fade:
                trans_type = "fade" if is_fade else "cut"
                # Check if elapsed time since last cut point exceeds minimum scene duration
                last_time = cut_points[-1][1] if cut_points else signatures[0].timestamp
                if (sig.timestamp - last_time) >= self.min_scene_duration:
                    cut_points.append((sig.frame_index, sig.timestamp, trans_type))

            prev_sig = sig

        # Build VideoScene list from cut points
        scenes: list[VideoScene] = []
        cur_start_idx = signatures[0].frame_index
        cur_start_time = signatures[0].timestamp

        for i, (cut_frame, cut_time, trans_type) in enumerate(cut_points):
            sc_duration = round(cut_time - cur_start_time, 3)
            scenes.append(
                VideoScene(
                    scene_id=f"scene_{i + 1:03d}",
                    start=round(cur_start_time, 3),
                    end=round(cut_time, 3),
                    duration=sc_duration,
                    start_frame=cur_start_idx,
                    end_frame=max(cur_start_idx, cut_frame - 1),
                    transition_type=trans_type,
                    confidence=0.92 if trans_type == "cut" else 0.85,
                )
            )
            cur_start_idx = cut_frame
            cur_start_time = cut_time

        # Final trailing scene
        final_end_time = max(total_duration, signatures[-1].timestamp)
        final_end_idx = signatures[-1].frame_index
        scenes.append(
            VideoScene(
                scene_id=f"scene_{len(scenes) + 1:03d}",
                start=round(cur_start_time, 3),
                end=round(final_end_time, 3),
                duration=round(max(0.1, final_end_time - cur_start_time), 3),
                start_frame=cur_start_idx,
                end_frame=final_end_idx,
                transition_type="continuous",
                confidence=0.95,
            )
        )

        return scenes
