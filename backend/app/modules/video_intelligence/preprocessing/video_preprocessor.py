"""Video preprocessing, FFprobe stream inspection, and audio extraction."""

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.modules.video_intelligence.schemas.video_document import (
    AudioStreamInfo,
    VideoMetadata,
    VideoStreamInfo,
)

logger = logging.getLogger(__name__)


class VideoPreprocessor:
    """Probes multimedia streams and extracts audio tracks for downstream processing."""

    def __init__(self, ffprobe_bin: str = "ffprobe", ffmpeg_bin: str = "ffmpeg") -> None:
        self.ffprobe_bin = shutil.which(ffprobe_bin) or ffprobe_bin
        self.ffmpeg_bin = shutil.which(ffmpeg_bin) or ffmpeg_bin

    def probe_metadata(self, file_path: Path | str) -> VideoMetadata:
        """Inspect video and audio stream parameters using ffprobe with OpenCV fallback."""
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Video file not found: {p}")

        file_size = p.stat().st_size
        filename = p.name
        container_fmt = p.suffix.lstrip(".").lower()

        try:
            cmd = [
                self.ffprobe_bin,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(p),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                return self._parse_ffprobe_json(data, filename, file_size, container_fmt)
        except Exception as e:
            logger.warning("ffprobe probe failed for %s (%s). Falling back to OpenCV inspection.", p, e)

        # Fallback inspection via OpenCV
        return self._probe_opencv_fallback(p, filename, file_size, container_fmt)

    def _parse_ffprobe_json(
        self,
        data: dict[str, Any],
        filename: str,
        file_size: int,
        container_fmt: str,
    ) -> VideoMetadata:
        """Parse structured JSON from ffprobe stdout."""
        fmt_data = data.get("format", {})
        duration = float(fmt_data.get("duration", 0.0) or 0.0)
        bitrate_raw = fmt_data.get("bit_rate")
        bitrate_kbps = float(bitrate_raw) / 1000.0 if bitrate_raw else None
        creation_time = fmt_data.get("tags", {}).get("creation_time")
        tags = fmt_data.get("tags", {})

        video_streams: list[VideoStreamInfo] = []
        audio_streams: list[AudioStreamInfo] = []

        streams = data.get("streams", [])
        for s in streams:
            codec_type = s.get("codec_type", "").lower()
            if codec_type == "video":
                v_info = self._parse_video_stream(s)
                video_streams.append(v_info)
            elif codec_type == "audio":
                a_info = self._parse_audio_stream(s)
                audio_streams.append(a_info)

        # Container format from ffprobe format_name (e.g. 'mov,mp4,m4a,3gp,3g2,mj2')
        detected_container = fmt_data.get("format_name", container_fmt).split(",")[0].strip()

        return VideoMetadata(
            filename=filename,
            container_format=detected_container or container_fmt,
            file_size_bytes=file_size,
            duration_seconds=duration,
            bitrate_kbps=bitrate_kbps,
            stream_count=len(streams),
            creation_time=creation_time,
            tags=tags,
            video_streams=video_streams,
            audio_streams=audio_streams,
        )

    def _parse_video_stream(self, s: dict[str, Any]) -> VideoStreamInfo:
        """Parse video stream attributes."""
        idx = int(s.get("index", 0))
        codec = s.get("codec_name", "unknown")
        profile = s.get("profile", "")
        width = int(s.get("width", 0) or 0)
        height = int(s.get("height", 0) or 0)
        pixel_fmt = s.get("pix_fmt", "yuv420p")
        color_space = s.get("color_space")
        aspect_ratio = s.get("display_aspect_ratio") or f"{width}:{height}" if width and height else None

        # Parse FPS
        fps = 0.0
        avg_fps = 0.0
        r_frame_rate = s.get("r_frame_rate", "")
        avg_frame_rate = s.get("avg_frame_rate", "")

        def _eval_ratio(val: str) -> float:
            if "/" in val:
                num, den = val.split("/", 1)
                try:
                    return float(num) / float(den) if float(den) != 0 else 0.0
                except (ValueError, ZeroDivisionError):
                    return 0.0
            try:
                return float(val)
            except ValueError:
                return 0.0

        if r_frame_rate:
            fps = _eval_ratio(r_frame_rate)
        if avg_frame_rate:
            avg_fps = _eval_ratio(avg_frame_rate)
        if fps == 0.0 and avg_fps > 0.0:
            fps = avg_fps
        if avg_fps == 0.0 and fps > 0.0:
            avg_fps = fps

        is_vfr = abs(fps - avg_fps) > 0.5 if (fps > 0 and avg_fps > 0) else False

        # Bit depth
        bit_depth = int(s.get("bits_per_raw_sample", 8) or 8)

        # Bitrate
        v_bitrate_raw = s.get("bit_rate")
        v_bitrate = float(v_bitrate_raw) / 1000.0 if v_bitrate_raw else None

        # Rotation
        rotation = 0
        side_data = s.get("side_data_list", [])
        for sd in side_data:
            if "rotation" in sd:
                try:
                    rotation = int(sd["rotation"])
                except (ValueError, TypeError):
                    pass
        if rotation == 0 and "tags" in s and "rotate" in s["tags"]:
            try:
                rotation = int(s["tags"]["rotate"])
            except (ValueError, TypeError):
                pass

        # Frame count
        nb_frames = s.get("nb_frames")
        frame_count = int(nb_frames) if nb_frames and nb_frames.isdigit() else None

        return VideoStreamInfo(
            index=idx,
            codec=codec,
            codec_profile=str(profile),
            width=width,
            height=height,
            resolution=f"{width}x{height}",
            fps=round(fps, 3),
            avg_fps=round(avg_fps, 3),
            pixel_format=pixel_fmt,
            bit_depth=bit_depth,
            color_space=color_space,
            aspect_ratio=aspect_ratio,
            rotation=rotation,
            frame_count=frame_count,
            bitrate_kbps=v_bitrate,
            is_variable_frame_rate=is_vfr,
        )

    def _parse_audio_stream(self, s: dict[str, Any]) -> AudioStreamInfo:
        """Parse audio stream attributes."""
        idx = int(s.get("index", 0))
        codec = s.get("codec_name", "unknown")
        sample_rate = int(s.get("sample_rate", 0) or 0)
        channels = int(s.get("channels", 1) or 1)
        layout = s.get("channel_layout", "stereo" if channels == 2 else "mono")
        a_bitrate_raw = s.get("bit_rate")
        a_bitrate = float(a_bitrate_raw) / 1000.0 if a_bitrate_raw else None
        duration_raw = s.get("duration")
        duration = float(duration_raw) if duration_raw else None
        start_time_raw = s.get("start_time")
        start_time_offset = float(start_time_raw) if start_time_raw else 0.0
        lang = s.get("tags", {}).get("language")

        return AudioStreamInfo(
            index=idx,
            codec=codec,
            sample_rate=sample_rate,
            channels=channels,
            channel_layout=layout,
            bitrate_kbps=a_bitrate,
            duration_seconds=duration,
            language=lang,
            start_time_offset=start_time_offset,
        )

    def _probe_opencv_fallback(
        self,
        file_path: Path,
        filename: str,
        file_size: int,
        container_fmt: str,
    ) -> VideoMetadata:
        """Fallback inspection using OpenCV VideoCapture when ffprobe is missing."""
        import cv2

        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            return VideoMetadata(
                filename=filename,
                container_format=container_fmt,
                file_size_bytes=file_size,
                duration_seconds=0.0,
            )

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = (frame_count / fps) if (fps > 0 and frame_count > 0) else 0.0

        # FourCC codec
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)
        codec_chars = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)]).strip()
        codec = codec_chars if codec_chars.isalnum() else "unknown"

        cap.release()

        v_stream = VideoStreamInfo(
            index=0,
            codec=codec,
            width=width,
            height=height,
            resolution=f"{width}x{height}",
            fps=round(fps, 3),
            avg_fps=round(fps, 3),
            frame_count=frame_count if frame_count > 0 else None,
        )

        return VideoMetadata(
            filename=filename,
            container_format=container_fmt,
            file_size_bytes=file_size,
            duration_seconds=round(duration, 3),
            stream_count=1,
            video_streams=[v_stream],
            audio_streams=[],
        )

    def extract_audio_stream(
        self,
        video_path: Path | str,
        output_wav_path: Path | str,
        audio_stream_index: int = 0,
    ) -> bool:
        """Extract and resample audio track from video to 16kHz mono WAV for Phase 7 analysis."""
        vp = Path(video_path).resolve()
        op = Path(output_wav_path).resolve()
        op.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i",
            str(vp),
            "-map",
            f"0:a:{audio_stream_index}",
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(op),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if res.returncode == 0 and op.exists() and op.stat().st_size > 44:
                return True
            logger.warning("Audio extraction failed (exit %d): %s", res.returncode, res.stderr)
            return False
        except Exception as e:
            logger.warning("Failed executing FFmpeg audio extraction: %s", e)
            return False
