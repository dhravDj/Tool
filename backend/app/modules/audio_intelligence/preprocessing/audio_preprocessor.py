"""Audio preprocessing, metadata extraction, decoding, and VAD chunking pipeline."""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import mutagen
import numpy as np
import soundfile as sf

from app.modules.audio_intelligence.schemas.audio_document import AudioMetadata

logger = logging.getLogger(__name__)


class AudioPreprocessingError(Exception):
    """Raised when audio decoding, probing, or preprocessing fails."""


class AudioChunk:
    """Represents a time-bounded slice of an audio file for windowed processing."""

    def __init__(
        self,
        chunk_id: str,
        start_seconds: float,
        end_seconds: float,
        file_path: str,
        is_last: bool = False,
    ) -> None:
        self.chunk_id = chunk_id
        self.start_seconds = start_seconds
        self.end_seconds = end_seconds
        self.file_path = file_path
        self.is_last = is_last

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)


class AudioPreprocessor:
    """Probes media metadata, decodes diverse audio containers, resamples, and segments."""

    def __init__(
        self,
        target_sample_rate: int = 16000,
        chunk_duration_seconds: float = 30.0,
        chunk_overlap_seconds: float = 1.0,
        silence_threshold_db: float = -40.0,
        min_silence_duration_seconds: float = 0.5,
    ) -> None:
        self.target_sample_rate = target_sample_rate
        self.chunk_duration_seconds = chunk_duration_seconds
        self.chunk_overlap_seconds = chunk_overlap_seconds
        self.silence_threshold_db = silence_threshold_db
        self.min_silence_duration_seconds = min_silence_duration_seconds

    def probe_metadata(self, file_path: str | Path) -> AudioMetadata:
        """Extract stream parameters and embedded container tags via ffprobe and mutagen."""
        path_str = str(file_path)
        if not os.path.exists(path_str):
            raise AudioPreprocessingError(f"Audio file not found: {path_str}")

        file_size = os.path.getsize(path_str)
        if file_size == 0:
            raise AudioPreprocessingError(f"Audio file is empty (0 bytes): {path_str}")

        # 1. Run ffprobe with JSON output (strict non-shell command)
        ffprobe_cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            path_str,
        ]

        try:
            res = subprocess.run(
                ffprobe_cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"ffprobe invocation failed: {e}. Falling back to soundfile/mutagen.")
            return self._probe_fallback(path_str, file_size)

        if res.returncode != 0 or not res.stdout.strip():
            logger.warning("ffprobe returned non-zero. Attempting fallback probe.")
            return self._probe_fallback(path_str, file_size)

        try:
            probe_data = json.loads(res.stdout)
        except json.JSONDecodeError:
            return self._probe_fallback(path_str, file_size)

        streams = probe_data.get("streams", [])
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        if not audio_streams:
            raise AudioPreprocessingError(f"No usable audio stream found in container: {path_str}")

        primary_stream = audio_streams[0]
        fmt_info = probe_data.get("format", {})

        # Extract stream fields
        codec = primary_stream.get("codec_name", "unknown")
        format_name = fmt_info.get("format_name", Path(path_str).suffix.lstrip(".").lower())
        if "," in format_name:
            # e.g. "mp3,mp2" -> "mp3", "mov,mp4,m4a,3gp,3g2,mj2" -> "m4a" or suffix
            ext = Path(path_str).suffix.lstrip(".").lower()
            format_name = ext if ext in format_name else format_name.split(",")[0]

        try:
            sample_rate = int(primary_stream.get("sample_rate", 0))
        except (ValueError, TypeError):
            sample_rate = 0

        try:
            channels = int(primary_stream.get("channels", 1))
        except (ValueError, TypeError):
            channels = 1

        channel_layout = primary_stream.get("channel_layout", "stereo" if channels == 2 else "mono")

        # Duration: prefer stream duration, fallback to format duration
        raw_duration = primary_stream.get("duration") or fmt_info.get("duration") or 0.0
        try:
            duration = float(raw_duration)
        except (ValueError, TypeError):
            duration = 0.0

        # Bit depth
        bit_depth: int | None = None
        if "bits_per_sample" in primary_stream and primary_stream["bits_per_sample"]:
            try:
                bit_depth = int(primary_stream["bits_per_sample"])
            except (ValueError, TypeError):
                bit_depth = None
        elif "bits_per_raw_sample" in primary_stream and primary_stream["bits_per_raw_sample"]:
            try:
                bit_depth = int(primary_stream["bits_per_raw_sample"])
            except (ValueError, TypeError):
                bit_depth = None

        # Bitrate
        bitrate_kbps: float | None = None
        raw_bitrate = primary_stream.get("bit_rate") or fmt_info.get("bit_rate")
        if raw_bitrate:
            try:
                bitrate_kbps = round(float(raw_bitrate) / 1000.0, 1)
            except (ValueError, TypeError):
                bitrate_kbps = None

        # Tags extraction (merge ffprobe tags + mutagen tags)
        tags: dict[str, Any] = fmt_info.get("tags", {})
        title: str | None = tags.get("title") or tags.get("TITLE")
        artist: str | None = tags.get("artist") or tags.get("ARTIST")
        album: str | None = tags.get("album") or tags.get("ALBUM")
        genre: str | None = tags.get("genre") or tags.get("GENRE")
        date: str | None = tags.get("date") or tags.get("DATE") or tags.get("creation_time")

        # Enrich with mutagen if available
        try:
            mg = mutagen.File(path_str)
            if mg is not None and hasattr(mg, "tags") and mg.tags:
                mg_tags = dict(mg.tags)
                if not title and "TIT2" in mg_tags:
                    title = str(mg_tags["TIT2"])
                if not artist and "TPE1" in mg_tags:
                    artist = str(mg_tags["TPE1"])
                if not album and "TALB" in mg_tags:
                    album = str(mg_tags["TALB"])
        except Exception as e:
            logger.debug(f"Mutagen tag enrichment advisory: {e}")

        return AudioMetadata(
            format=format_name,
            codec=codec,
            duration_seconds=round(duration, 3),
            sample_rate=sample_rate,
            channels=channels,
            channel_layout=channel_layout,
            bit_depth=bit_depth,
            bitrate_kbps=bitrate_kbps,
            file_size_bytes=file_size,
            audio_stream_count=len(audio_streams),
            title=title,
            artist=artist,
            album=album,
            genre=genre,
            date=date,
            raw_tags=tags,
        )

    def _probe_fallback(self, path_str: str, file_size: int) -> AudioMetadata:
        """SoundFile + Mutagen fallback probing if ffprobe is absent."""
        format_name = Path(path_str).suffix.lstrip(".").lower()
        duration = 0.0
        sample_rate = 16000
        channels = 1
        codec = format_name

        try:
            info = sf.info(path_str)
            duration = float(info.duration)
            sample_rate = int(info.samplerate)
            channels = int(info.channels)
            codec = (info.subtype or format_name).lower()
        except Exception as e:
            logger.warning(f"SoundFile fallback info failed: {e}")

        # Check mutagen for duration if soundfile failed
        if duration <= 0:
            try:
                mg = mutagen.File(path_str)
                if mg and hasattr(mg, "info") and mg.info:
                    duration = float(getattr(mg.info, "length", 0.0))
                    sample_rate = int(getattr(mg.info, "sample_rate", sample_rate))
                    channels = int(getattr(mg.info, "channels", channels))
            except Exception as e:
                logger.warning(f"Mutagen duration fallback failed: {e}")

        if duration <= 0:
            raise AudioPreprocessingError(
                f"No usable audio streams or recognizable audio format found in: {path_str}"
            )

        return AudioMetadata(
            format=format_name,
            codec=codec,
            duration_seconds=round(duration, 3),
            sample_rate=sample_rate,
            channels=channels,
            channel_layout="stereo" if channels == 2 else "mono",
            bit_depth=16,
            bitrate_kbps=None,
            file_size_bytes=file_size,
            audio_stream_count=1,
        )

    def resample_to_pcm16_wav(
        self,
        input_path: str | Path,
        output_path: str | Path,
        target_sample_rate: int | None = None,
        mono: bool = True,
    ) -> str:
        """Resample any decoded audio input into normalized 16-bit PCM WAV using FFmpeg."""
        sr = target_sample_rate or self.target_sample_rate
        channels = 1 if mono else 2

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(sr),
            "-ac",
            str(channels),
            str(output_path),
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
        if res.returncode != 0 or not os.path.exists(str(output_path)):
            err = res.stderr or "Unknown ffmpeg decoding failure"
            raise AudioPreprocessingError(f"FFmpeg decoding failed: {err}")

        return str(output_path)

    def inspect_amplitude(self, audio_data: np.ndarray) -> dict[str, float]:
        """Compute acoustic amplitude metrics: RMS energy, peak amplitude, and dynamic range."""
        if len(audio_data) == 0:
            return {"rms": 0.0, "peak": 0.0, "dynamic_range_db": 0.0}

        float_data = audio_data.astype(np.float32)
        if np.max(np.abs(float_data)) > 1.0:
            float_data = float_data / 32768.0

        peak = float(np.max(np.abs(float_data)))
        rms = float(np.sqrt(np.mean(float_data**2)))
        dr = 20.0 * np.log10(peak / (rms + 1e-9)) if rms > 1e-9 and peak > 1e-9 else 0.0

        return {
            "rms": round(rms, 5),
            "peak": round(peak, 5),
            "dynamic_range_db": round(max(0.0, dr), 2),
        }

    def detect_silence(self, file_path: str | Path) -> list[tuple[float, float]]:
        """Detect silence intervals (start_sec, end_sec) using FFmpeg silencedetect."""
        cmd = [
            "ffmpeg",
            "-i",
            str(file_path),
            "-af",
            f"silencedetect=noise={self.silence_threshold_db}dB:d={self.min_silence_duration_seconds}",
            "-f",
            "null",
            "-",
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        silences: list[tuple[float, float]] = []

        cur_start: float | None = None
        for line in res.stderr.splitlines():
            if "silence_start:" in line:
                try:
                    parts = line.split("silence_start:")
                    cur_start = float(parts[1].split()[0])
                except (ValueError, IndexError):
                    cur_start = None
            elif "silence_end:" in line and cur_start is not None:
                try:
                    parts = line.split("silence_end:")
                    cur_end = float(parts[1].split()[0])
                    silences.append((round(cur_start, 3), round(cur_end, 3)))
                    cur_start = None
                except (ValueError, IndexError):
                    cur_start = None

        return silences

    def generate_chunks(
        self,
        audio_file_path: str | Path,
        total_duration: float,
        temp_dir: str | Path,
    ) -> list[AudioChunk]:
        """Generate windowed, VAD-aware chunks for long audio files."""
        path_str = str(audio_file_path)
        chunks: list[AudioChunk] = []

        if total_duration <= self.chunk_duration_seconds:
            # Short recording: single chunk
            chunks.append(
                AudioChunk(
                    chunk_id="chunk_0",
                    start_seconds=0.0,
                    end_seconds=total_duration,
                    file_path=path_str,
                    is_last=True,
                )
            )
            return chunks

        # Long recording: slice into chunks with safe boundaries
        silence_intervals = self.detect_silence(path_str)

        start = 0.0
        chunk_idx = 0

        while start < total_duration:
            ideal_end = start + self.chunk_duration_seconds
            if ideal_end >= total_duration:
                end = total_duration
            else:
                # Seek nearest silence midpoint within [ideal_end - 4s, ideal_end + 4s]
                best_cut = ideal_end
                for s_start, s_end in silence_intervals:
                    s_mid = (s_start + s_end) / 2.0
                    if abs(s_mid - ideal_end) < 4.0:
                        best_cut = s_mid
                        break
                end = min(total_duration, best_cut)

            chunk_file = os.path.join(str(temp_dir), f"chunk_{chunk_idx}.wav")
            # Extract slice via ffmpeg -ss start -to end
            duration_slice = end - start
            slice_cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                str(round(start, 3)),
                "-i",
                path_str,
                "-t",
                str(round(duration_slice, 3)),
                "-acodec",
                "copy",
                chunk_file,
            ]
            res = subprocess.run(slice_cmd, capture_output=True, text=True, check=False, timeout=30)
            if res.returncode != 0:
                # Fallback to re-encoding PCM slice
                slice_cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    str(round(start, 3)),
                    "-i",
                    path_str,
                    "-t",
                    str(round(duration_slice, 3)),
                    "-acodec",
                    "pcm_s16le",
                    chunk_file,
                ]
                subprocess.run(slice_cmd, capture_output=True, text=True, check=False, timeout=30)

            is_last = end >= total_duration
            chunks.append(
                AudioChunk(
                    chunk_id=f"chunk_{chunk_idx}",
                    start_seconds=round(start, 3),
                    end_seconds=round(end, 3),
                    file_path=chunk_file,
                    is_last=is_last,
                )
            )

            if is_last:
                break

            # Advance with slight overlap for VAD continuity
            start = end - self.chunk_overlap_seconds
            chunk_idx += 1

        return chunks
