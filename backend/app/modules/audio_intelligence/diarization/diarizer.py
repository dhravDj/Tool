"""Speaker diarization engine providing anonymous speaker turns and acoustic clustering."""

import logging
import re

import numpy as np
import soundfile as sf

from app.modules.audio_intelligence.schemas.audio_document import (
    AudioSegment,
    Speaker,
)

logger = logging.getLogger(__name__)


class AudioDiarizer:
    """Performs acoustic timbre clustering and speaker turn segmentation."""

    def __init__(self, max_speakers: int = 4, distance_threshold: float = 0.35) -> None:
        self.max_speakers = max_speakers
        self.distance_threshold = distance_threshold

    @property
    def is_neural_available(self) -> bool:
        """True if external neural diarization framework (e.g. pyannote) is configured."""
        try:
            import pyannote.audio  # noqa: F401

            return True
        except ImportError:
            return False

    def diarize_segments(
        self,
        audio_path: str,
        segments: list[AudioSegment],
    ) -> tuple[list[AudioSegment], list[Speaker]]:
        """Attribute anonymous speaker labels (e.g. 'Speaker 1', 'Speaker 2') to segments."""
        if not segments:
            return [], []

        # 1. First inspect if segments already contain embedded speaker cues (e.g. "Speaker 1: ...")
        annotated_segments, speakers = self._diarize_from_text_cues(segments)
        if speakers:
            return annotated_segments, speakers

        # 2. Extract acoustic feature embeddings for each segment from audio
        try:
            data, sr = sf.read(audio_path)
            if data.ndim > 1:
                data = np.mean(data, axis=1)
        except Exception as e:
            logger.warning(f"Audio read in diarizer failed: {e}. Defaulting to single speaker.")
            return self._fallback_single_speaker(segments)

        if len(data) == 0 or sr <= 0:
            return self._fallback_single_speaker(segments)

        # Extract features for each segment
        features: list[np.ndarray] = []
        valid_indices: list[int] = []

        for idx, seg in enumerate(segments):
            start_sample = int(seg.start * sr)
            end_sample = min(len(data), int(seg.end * sr))
            seg_slice = data[start_sample:end_sample]

            if len(seg_slice) > sr * 0.1:  # At least 100ms
                feat = self._extract_timbre_features(seg_slice, sr)
                features.append(feat)
                valid_indices.append(idx)
            else:
                features.append(np.zeros(4, dtype=np.float32))

        if not valid_indices:
            return self._fallback_single_speaker(segments)

        # Cluster acoustic features
        labels = self._cluster_features(features, valid_indices)

        # Map cluster labels (0, 1, ...) to anonymous 'Speaker 1', 'Speaker 2', ...
        speaker_map: dict[int, str] = {}
        unique_labels = sorted(set(labels))
        for cluster_id, lbl in enumerate(unique_labels, start=1):
            speaker_map[lbl] = f"Speaker {cluster_id}"

        # Assign speaker labels to segments
        updated_segments: list[AudioSegment] = []
        speaker_segments_map: dict[str, list[str]] = {s_name: [] for s_name in speaker_map.values()}
        speaker_duration_map: dict[str, float] = dict.fromkeys(speaker_map.values(), 0.0)

        for idx, seg in enumerate(segments):
            lbl = labels[idx]
            speaker_label = speaker_map[lbl]
            seg_duration = seg.end - seg.start

            # Update segment with speaker_id
            seg_copy = AudioSegment(
                segment_id=seg.segment_id,
                start=seg.start,
                end=seg.end,
                text=seg.text,
                speaker_id=speaker_label,
                words=seg.words,
                confidence=seg.confidence,
                source_chunk_id=seg.source_chunk_id,
            )
            updated_segments.append(seg_copy)
            speaker_segments_map[speaker_label].append(seg.segment_id)
            speaker_duration_map[speaker_label] += seg_duration

        # Build Speaker entities
        speaker_list: list[Speaker] = []
        for s_id, s_name in enumerate(speaker_map.values(), start=1):
            speaker_list.append(
                Speaker(
                    speaker_id=f"spk_{s_id}",
                    label=s_name,
                    segment_ids=speaker_segments_map[s_name],
                    total_speaking_time_seconds=round(speaker_duration_map[s_name], 3),
                    metadata={"cluster_id": s_id, "method": "acoustic_timbre_clustering"},
                )
            )

        return updated_segments, speaker_list

    def _extract_timbre_features(self, slice_data: np.ndarray, sr: int) -> np.ndarray:
        """Extract spectral centroid, roll-off, zero-crossing rate, and RMS energy."""
        float_data = slice_data.astype(np.float32)
        rms = float(np.sqrt(np.mean(float_data**2)))
        zcr = float(np.mean(np.abs(np.diff(np.sign(float_data)))))

        # Magnitude spectrum via FFT
        n_fft = min(len(float_data), 2048)
        spec = np.abs(np.fft.rfft(float_data[:n_fft]))
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

        sum_spec = np.sum(spec) + 1e-9
        centroid = float(np.sum(freqs * spec) / sum_spec) / (sr / 2.0)  # Normalized 0..1

        # Spectral roll-off (85% energy point)
        cum_spec = np.cumsum(spec)
        rolloff_idx = np.searchsorted(cum_spec, 0.85 * cum_spec[-1])
        rolloff = float(freqs[min(rolloff_idx, len(freqs) - 1)]) / (sr / 2.0)

        return np.array([rms, zcr, centroid, rolloff], dtype=np.float32)

    def _cluster_features(
        self,
        features: list[np.ndarray],
        valid_indices: list[int],
    ) -> list[int]:
        """Simple greedy agglomerative clustering based on euclidean timbre distance."""
        labels = [0] * len(features)
        if len(valid_indices) <= 1:
            return labels

        # Normalize features across valid indices
        valid_mat = np.array([features[i] for i in valid_indices])
        std = np.std(valid_mat, axis=0) + 1e-6
        mean = np.mean(valid_mat, axis=0)
        norm_mat = (valid_mat - mean) / std

        # Centroids for clusters
        centroids: list[np.ndarray] = [norm_mat[0]]
        cluster_assignment: list[int] = [0]

        for i in range(1, len(valid_indices)):
            vec = norm_mat[i]
            dists = [float(np.linalg.norm(vec - c)) for c in centroids]
            min_dist = min(dists)
            closest_idx = int(np.argmin(dists))

            if min_dist > self.distance_threshold and len(centroids) < self.max_speakers:
                centroids.append(vec)
                cluster_assignment.append(len(centroids) - 1)
            else:
                cluster_assignment.append(closest_idx)
                # Update centroid with running average
                centroids[closest_idx] = 0.8 * centroids[closest_idx] + 0.2 * vec

        for idx, valid_idx in enumerate(valid_indices):
            labels[valid_idx] = cluster_assignment[idx]

        return labels

    def _diarize_from_text_cues(
        self,
        segments: list[AudioSegment],
    ) -> tuple[list[AudioSegment], list[Speaker]]:
        """Check if segment text has speaker cues like 'Speaker 1:', 'Speaker 2:' or names."""
        cues_detected = False
        cue_map: dict[str, str] = {}
        speaker_turn_regex = re.compile(r"^(Speaker\s*\d+|Person\s*\d+|[A-Z][a-z]+)\s*:\s*(.*)", re.IGNORECASE)

        for s in segments:
            m = speaker_turn_regex.match(s.text.strip())
            if m:
                cues_detected = True
                raw_speaker = m.group(1).title()
                if raw_speaker not in cue_map:
                    cue_map[raw_speaker] = f"Speaker {len(cue_map) + 1}"

        if not cues_detected:
            return segments, []

        updated_segments: list[AudioSegment] = []
        speaker_segments_map: dict[str, list[str]] = {s_name: [] for s_name in cue_map.values()}
        speaker_duration_map: dict[str, float] = dict.fromkeys(cue_map.values(), 0.0)

        current_speaker = list(cue_map.values())[0]

        for s in segments:
            m = speaker_turn_regex.match(s.text.strip())
            cleaned_text = s.text
            if m:
                raw_speaker = m.group(1).title()
                current_speaker = cue_map.get(raw_speaker, current_speaker)
                cleaned_text = m.group(2).strip()

            seg_duration = s.end - s.start
            seg_copy = AudioSegment(
                segment_id=s.segment_id,
                start=s.start,
                end=s.end,
                text=cleaned_text,
                speaker_id=current_speaker,
                words=s.words,
                confidence=s.confidence,
                source_chunk_id=s.source_chunk_id,
            )
            updated_segments.append(seg_copy)
            speaker_segments_map[current_speaker].append(s.segment_id)
            speaker_duration_map[current_speaker] += seg_duration

        speaker_list: list[Speaker] = []
        for s_id, s_name in enumerate(cue_map.values(), start=1):
            speaker_list.append(
                Speaker(
                    speaker_id=f"spk_{s_id}",
                    label=s_name,
                    segment_ids=speaker_segments_map[s_name],
                    total_speaking_time_seconds=round(speaker_duration_map[s_name], 3),
                    metadata={"source": "text_cues_anonymized"},
                )
            )

        return updated_segments, speaker_list

    def _fallback_single_speaker(
        self,
        segments: list[AudioSegment],
    ) -> tuple[list[AudioSegment], list[Speaker]]:
        """Single speaker default attribution."""
        speaker_label = "Speaker 1"
        updated: list[AudioSegment] = []
        seg_ids: list[str] = []
        total_time = 0.0

        for s in segments:
            updated.append(
                AudioSegment(
                    segment_id=s.segment_id,
                    start=s.start,
                    end=s.end,
                    text=s.text,
                    speaker_id=speaker_label,
                    words=s.words,
                    confidence=s.confidence,
                    source_chunk_id=s.source_chunk_id,
                )
            )
            seg_ids.append(s.segment_id)
            total_time += s.end - s.start

        speakers = [
            Speaker(
                speaker_id="spk_1",
                label=speaker_label,
                segment_ids=seg_ids,
                total_speaking_time_seconds=round(total_time, 3),
                metadata={"status": "single_speaker_default"},
            )
        ]
        return updated, speakers
