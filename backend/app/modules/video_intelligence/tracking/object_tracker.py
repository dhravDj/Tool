"""Lightweight object detection and multi-frame trajectory tracking."""

import logging
from typing import Any

import cv2
import numpy as np

from app.modules.video_intelligence.schemas.video_document import (
    VideoDetection,
    VideoObservation,
    VideoTrack,
)

logger = logging.getLogger(__name__)


def compute_iou(box_a: list[float], box_b: list[float]) -> float:
    """Compute Intersection-over-Union between two normalized bounding boxes [ymin, xmin, ymax, xmax]."""
    y_min_a, x_min_a, y_max_a, x_max_a = box_a
    y_min_b, x_min_b, y_max_b, x_max_b = box_b

    inter_ymin = max(y_min_a, y_min_b)
    inter_xmin = max(x_min_a, x_min_b)
    inter_ymax = min(y_max_a, y_max_b)
    inter_xmax = min(x_max_a, x_max_b)

    inter_w = max(0.0, inter_xmax - inter_xmin)
    inter_h = max(0.0, inter_ymax - inter_ymin)
    inter_area = inter_w * inter_h

    area_a = max(0.0, x_max_a - x_min_a) * max(0.0, y_max_a - y_min_a)
    area_b = max(0.0, x_max_b - x_min_b) * max(0.0, y_max_b - y_min_b)
    union_area = area_a + area_b - inter_area

    if union_area <= 0.0:
        return 0.0
    return float(inter_area / union_area)


class ObjectTracker:
    """Lightweight, hardware-efficient object detector and IoU-based multi-frame tracker."""

    def __init__(
        self,
        iou_threshold: float = 0.25,
        min_contour_area_pct: float = 0.015,
        max_lost_seconds: float = 2.0,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.min_contour_area_pct = min_contour_area_pct
        self.max_lost_seconds = max_lost_seconds
        self._track_counter = 0

        # Load standard Haar cascades for human/body silhouettes if available
        self._cascade_body: Any = None
        try:
            cv2_data = getattr(cv2, "data", None)
            if cv2_data is not None:
                haarcascades_dir = getattr(cv2_data, "haarcascades", "")
                cascade_path = haarcascades_dir + "haarcascade_fullbody.xml"
                cascade_cls = getattr(cv2, "CascadeClassifier", None)
                if cascade_cls:
                    self._cascade_body = cascade_cls(cascade_path)
                    if hasattr(self._cascade_body, "empty") and self._cascade_body.empty():
                        self._cascade_body = None
        except Exception:
            self._cascade_body = None

    def detect_objects_in_frame(
        self,
        frame_bgr: np.ndarray,
        frame_id: str,
        timestamp: float,
        prev_frame_bgr: np.ndarray | None = None,
    ) -> list[VideoDetection]:
        """Detect salient visual entities and moving objects in a frame."""
        h, w = frame_bgr.shape[:2]
        frame_area = float(h * w)
        detections: list[VideoDetection] = []

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Cascade classifier for person/human presence
        if self._cascade_body is not None:
            try:
                bodies = self._cascade_body.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30)
                )
                for bx, by, bw, bh in bodies:
                    box = [
                        round(float(by) / h, 4),
                        round(float(bx) / w, 4),
                        round(float(by + bh) / h, 4),
                        round(float(bx + bw) / w, 4),
                    ]
                    detections.append(
                        VideoDetection(
                            frame_id=frame_id,
                            timestamp=timestamp,
                            object_class="person",
                            bounding_box=box,
                            confidence=0.88,
                        )
                    )
            except Exception as e:
                logger.debug("Body cascade detection error: %s", e)

        # 2. Motion / Contour detection relative to previous frame
        if prev_frame_bgr is not None and prev_frame_bgr.shape == frame_bgr.shape:
            prev_gray = cv2.cvtColor(prev_frame_bgr, cv2.COLOR_BGR2GRAY)
            frame_diff = cv2.absdiff(prev_gray, gray)
            _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            dilated = cv2.dilate(thresh, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if (area / frame_area) >= self.min_contour_area_pct:
                    cx, cy, cw, ch = cv2.boundingRect(cnt)
                    box = [
                        round(float(cy) / h, 4),
                        round(float(cx) / w, 4),
                        round(float(cy + ch) / h, 4),
                        round(float(cx + cw) / w, 4),
                    ]
                    # Check if already covered by an existing detection
                    is_duplicate = any(compute_iou(box, d.bounding_box) > 0.5 for d in detections)
                    if not is_duplicate:
                        aspect = float(cw) / float(ch) if ch > 0 else 1.0
                        cls_name = "vehicle" if aspect > 1.6 and (area / frame_area) > 0.05 else "object"
                        detections.append(
                            VideoDetection(
                                frame_id=frame_id,
                                timestamp=timestamp,
                                object_class=cls_name,
                                bounding_box=box,
                                confidence=0.75,
                            )
                        )

        # 3. High-contrast salient rectangular regions (e.g. presentation boxes, widgets)
        if not detections:
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if 0.04 <= (area / frame_area) <= 0.60:
                    cx, cy, cw, ch = cv2.boundingRect(cnt)
                    box = [
                        round(float(cy) / h, 4),
                        round(float(cx) / w, 4),
                        round(float(cy + ch) / h, 4),
                        round(float(cx + cw) / w, 4),
                    ]
                    detections.append(
                        VideoDetection(
                            frame_id=frame_id,
                            timestamp=timestamp,
                            object_class="visual_element",
                            bounding_box=box,
                            confidence=0.70,
                        )
                    )
                    if len(detections) >= 3:
                        break

        return detections

    def track_across_frames(
        self,
        detections_by_frame: list[tuple[str, float, list[VideoDetection]]],
    ) -> list[VideoTrack]:
        """Link frame detections across consecutive timestamps using IoU matching."""
        active_tracks: dict[str, VideoTrack] = {}
        completed_tracks: list[VideoTrack] = []

        for frame_id, ts, frame_dets in detections_by_frame:
            matched_detection_indices: set[int] = set()
            matched_track_ids: set[str] = set()

            # Match active tracks to new frame detections
            for track_id, track in active_tracks.items():
                if not track.observations:
                    continue
                last_obs = track.observations[-1]
                # If lost for too long, retire track
                if (ts - last_obs.timestamp) > self.max_lost_seconds:
                    continue

                best_iou = 0.0
                best_det_idx = -1

                for idx, det in enumerate(frame_dets):
                    if idx in matched_detection_indices:
                        continue
                    if det.object_class != track.object_class and track.object_class != "object":
                        continue
                    iou = compute_iou(last_obs.bounding_box, det.bounding_box)
                    if iou > best_iou:
                        best_iou = iou
                        best_det_idx = idx

                if best_iou >= self.iou_threshold and best_det_idx >= 0:
                    # Update existing track
                    matched_det = frame_dets[best_det_idx]
                    matched_det.track_id = track_id
                    track.observations.append(
                        VideoObservation(
                            frame_id=frame_id,
                            timestamp=ts,
                            bounding_box=matched_det.bounding_box,
                            confidence=matched_det.confidence,
                        )
                    )
                    track.last_seen_seconds = ts
                    track.duration_seconds = round(ts - track.first_seen_seconds, 3)
                    matched_detection_indices.add(best_det_idx)
                    matched_track_ids.add(track_id)

            # Retire stale tracks
            remaining_active: dict[str, VideoTrack] = {}
            for t_id, t in active_tracks.items():
                if t_id not in matched_track_ids and (ts - t.last_seen_seconds) > self.max_lost_seconds:
                    completed_tracks.append(t)
                else:
                    remaining_active[t_id] = t
            active_tracks = remaining_active

            # Spawn new tracks for unmatched detections
            for idx, det in enumerate(frame_dets):
                if idx not in matched_detection_indices:
                    self._track_counter += 1
                    new_track_id = f"track_{self._track_counter:03d}"
                    det.track_id = new_track_id
                    new_track = VideoTrack(
                        track_id=new_track_id,
                        object_class=det.object_class,
                        first_seen_seconds=ts,
                        last_seen_seconds=ts,
                        duration_seconds=0.0,
                        confidence=det.confidence,
                        observations=[
                            VideoObservation(
                                frame_id=frame_id,
                                timestamp=ts,
                                bounding_box=det.bounding_box,
                                confidence=det.confidence,
                            )
                        ],
                    )
                    active_tracks[new_track_id] = new_track

        # Gather remaining active tracks
        completed_tracks.extend(active_tracks.values())
        # Sort by first seen timestamp
        completed_tracks.sort(key=lambda t: t.first_seen_seconds)
        return completed_tracks
