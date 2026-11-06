"""Incremental video frame decoding, presentation timestamp extraction, and scaling."""

import logging
from collections.abc import Generator
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoDecoder:
    """Streams video frames incrementally without loading entire videos into RAM."""

    def __init__(self, max_dimension: int = 720) -> None:
        self.max_dimension = max_dimension

    def stream_frames(
        self,
        file_path: Path | str,
        sample_fps: float | None = None,
        max_frames: int | None = None,
    ) -> Generator[tuple[int, float, np.ndarray, bool], None, None]:
        """Stream frames incrementally.

        Yields (frame_index, timestamp_seconds, frame_bgr, is_sampled).
        """
        p = Path(file_path).resolve()
        cap = cv2.VideoCapture(str(p))
        if not cap.isOpened():
            logger.error("Could not open video file for decoding: %s", p)
            return

        nominal_fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        if nominal_fps <= 0.0 or np.isnan(nominal_fps):
            nominal_fps = 25.0

        sample_interval = (1.0 / sample_fps) if (sample_fps and sample_fps > 0) else None
        last_sample_time = -1.0
        frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                # Retrieve presentation timestamp in milliseconds
                pos_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                if pos_msec > 0:
                    pts = pos_msec / 1000.0
                else:
                    pts = frame_idx / nominal_fps

                # Check if this frame should be sampled for deep analysis
                is_sampled = False
                if sample_interval is None:
                    is_sampled = True
                elif last_sample_time < 0 or (pts - last_sample_time) >= sample_interval:
                    is_sampled = True
                    last_sample_time = pts

                # Resize if exceeding max_dimension
                h, w = frame.shape[:2]
                if max(h, w) > self.max_dimension:
                    scale = self.max_dimension / float(max(h, w))
                    new_w = max(1, int(w * scale))
                    new_h = max(1, int(h * scale))
                    frame_scaled = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                else:
                    frame_scaled = frame

                yield frame_idx, round(pts, 3), frame_scaled, is_sampled
                frame_idx += 1

                if max_frames and frame_idx >= max_frames:
                    break
        finally:
            cap.release()

    def extract_frame_at_timestamp(
        self,
        file_path: Path | str,
        timestamp_seconds: float,
    ) -> np.ndarray | None:
        """Extract a single frame closest to the specified timestamp."""
        p = Path(file_path).resolve()
        cap = cv2.VideoCapture(str(p))
        if not cap.isOpened():
            return None

        try:
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_seconds * 1000.0)
            ret, frame = cap.read()
            if not ret or frame is None:
                return None
            return frame
        finally:
            cap.release()
