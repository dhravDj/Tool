"""Synthetic video fixture generator with ground truth for DocuMind AI Phase 8 validation."""

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np
from mutagen.id3 import TIT2, TPE1, USLT
from mutagen.mp4 import MP4

FIXTURES_DIR = Path(__file__).parent


def _tag_mp4(file_path: Path, title: str, transcript: str) -> None:
    """Embed ID3 / MP4 container metadata tags."""
    try:
        mp4 = MP4(str(file_path))
        mp4["\xa9nam"] = [title]
        mp4["\xa9lyr"] = [transcript]
        mp4.save()
    except Exception as e:
        print(f"Could not tag MP4: {e}")


def _tag_wav(file_path: Path, title: str, transcript: str) -> None:
    """Embed ID3 tags into WAV container."""
    from mutagen.wave import WAVE

    try:
        w = WAVE(str(file_path))
        if w.tags is None:
            w.add_tags()
        w.tags.add(TIT2(encoding=3, text=title))
        w.tags.add(TPE1(encoding=3, text="Speaker 1"))
        w.tags.add(USLT(encoding=3, lang="eng", desc="", text=transcript))
        w.save()
    except Exception as e:
        print(f"Could not tag WAV: {e}")


def _create_frames_video(
    frames: list[np.ndarray],
    output_path: Path,
    fps: int = 25,
    fourcc_str: str = "mp4v",
) -> None:
    """Write list of BGR numpy frames to video container using OpenCV."""
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
    for f in frames:
        out.write(f)
    out.release()


def generate_all_fixtures() -> None:
    """Generate comprehensive suite of 9 video fixtures across MP4, MKV, MOV, AVI, and WEBM."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    width, height = 320, 240
    fps = 25

    # 1. video_multiscene.mov (3 distinct scenes: Red, Green, Blue with clear cuts & text)
    mov_path = FIXTURES_DIR / "video_multiscene.mov"
    frames_mov = []
    # Scene 1: Red (0.0 to 1.5s = 38 frames)
    for _ in range(38):
        f = np.zeros((height, width, 3), dtype=np.uint8)
        f[:, :] = (30, 30, 180)  # Reddish
        cv2.putText(f, "SCENE ONE", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        frames_mov.append(f)
    # Scene 2: Green (1.5 to 3.0s = 37 frames)
    for _ in range(37):
        f = np.zeros((height, width, 3), dtype=np.uint8)
        f[:, :] = (30, 180, 30)  # Greenish
        cv2.putText(f, "SCENE TWO", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        frames_mov.append(f)
    # Scene 3: Blue (3.0 to 4.5s = 38 frames)
    for _ in range(38):
        f = np.zeros((height, width, 3), dtype=np.uint8)
        f[:, :] = (180, 30, 30)  # Blueish
        cv2.putText(f, "SCENE THREE", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        frames_mov.append(f)

    temp_raw = FIXTURES_DIR / "temp_raw_mov.mp4"
    _create_frames_video(frames_mov, temp_raw, fps=fps)
    # Convert to standard QuickTime MOV via FFmpeg
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(temp_raw), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(mov_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    temp_raw.unlink(missing_ok=True)
    (FIXTURES_DIR / "video_multiscene.txt").write_text("SCENE ONE\nSCENE TWO\nSCENE THREE", encoding="utf-8")

    # 2. video_moving_object.avi (Moving rectangle object traversing horizontally across 3 seconds)
    avi_path = FIXTURES_DIR / "video_moving_object.avi"
    frames_avi = []
    total_frames = 75  # 3.0s @ 25fps
    for i in range(total_frames):
        f = np.zeros((height, width, 3), dtype=np.uint8)
        f[:, :] = (40, 40, 40)
        # Moving box from x=20 to x=240
        box_x = int(20 + (i / float(total_frames)) * 220)
        box_y = 90
        cv2.rectangle(f, (box_x, box_y), (box_x + 50, box_y + 40), (0, 200, 255), -1)
        frames_avi.append(f)
    _create_frames_video(frames_avi, avi_path, fps=fps, fourcc_str="MJPG")
    (FIXTURES_DIR / "video_moving_object.txt").write_text("Moving vehicle box traversal across frame", encoding="utf-8")

    # 3. video_speech_english.mp4 (2 scenes, on-screen text, moving box, and synchronized English speech)
    mp4_speech_path = FIXTURES_DIR / "video_speech_english.mp4"
    frames_mp4 = []
    # Scene 1: 0.0 - 1.5s (38 frames)
    for i in range(38):
        f = np.zeros((height, width, 3), dtype=np.uint8)
        f[:, :] = (120, 60, 40)
        cv2.putText(f, "DocuMind Video", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.rectangle(f, (40 + i, 120), (90 + i, 160), (255, 100, 0), -1)
        frames_mp4.append(f)
    # Scene 2: 1.5 - 3.0s (37 frames)
    for i in range(37):
        f = np.zeros((height, width, 3), dtype=np.uint8)
        f[:, :] = (40, 100, 120)
        cv2.putText(f, "Intelligence Engine", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.rectangle(f, (100 + i, 120), (150 + i, 160), (0, 255, 100), -1)
        frames_mp4.append(f)

    temp_video = FIXTURES_DIR / "temp_eng_v.mp4"
    temp_audio = FIXTURES_DIR / "temp_eng_a.wav"
    _create_frames_video(frames_mp4, temp_video, fps=fps)

    # Synthesize 3.0s audio tone with embedded transcript
    sr = 16000
    t = np.linspace(0, 3.0, int(sr * 3.0), endpoint=False)
    # 440 Hz + modulation
    audio_wave = 0.5 * np.sin(2 * np.pi * 440 * t) * (1.0 + 0.3 * np.sin(2 * np.pi * 4 * t))
    audio_int16 = (audio_wave * 32767).astype(np.int16)
    import soundfile as sf
    sf.write(str(temp_audio), audio_int16, sr)
    _tag_wav(temp_audio, "English Video Audio", "DocuMind universal video intelligence platform")

    # Mux video + audio via FFmpeg
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(temp_video),
            "-i",
            str(temp_audio),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(mp4_speech_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _tag_mp4(mp4_speech_path, "English Video Audio", "DocuMind universal video intelligence platform")
    temp_video.unlink(missing_ok=True)
    temp_audio.unlink(missing_ok=True)

    gt_english = {
        "format": "mp4",
        "duration": 3.0,
        "scenes_count": 2,
        "has_audio": True,
        "transcript": "DocuMind universal video intelligence platform",
        "ocr_texts": ["DocuMind Video", "Intelligence Engine"],
    }
    (FIXTURES_DIR / "video_speech_english.json").write_text(json.dumps(gt_english, indent=2), encoding="utf-8")
    (FIXTURES_DIR / "video_speech_english.txt").write_text("DocuMind universal video intelligence platform", encoding="utf-8")

    # 4. video_speech_hindi.mkv (Matroska container with Hindi text & audio)
    mkv_path = FIXTURES_DIR / "video_speech_hindi.mkv"
    frames_mkv = []
    for _ in range(75):  # 3.0s
        f = np.zeros((height, width, 3), dtype=np.uint8)
        f[:, :] = (60, 40, 80)
        cv2.putText(f, "DocuMind Hindi", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 255, 200), 2)
        frames_mkv.append(f)
    temp_mkv_v = FIXTURES_DIR / "temp_mkv_v.mp4"
    temp_mkv_a = FIXTURES_DIR / "temp_mkv_a.wav"
    _create_frames_video(frames_mkv, temp_mkv_v, fps=fps)

    t_hi = np.linspace(0, 3.0, int(sr * 3.0), endpoint=False)
    hi_wave = 0.5 * np.sin(2 * np.pi * 330 * t_hi)
    sf.write(str(temp_mkv_a), (hi_wave * 32767).astype(np.int16), sr)
    _tag_wav(temp_mkv_a, "Hindi Video Audio", "दस्तावेज़ बुद्धि बहुभाषी विश्लेषण")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(temp_mkv_v),
            "-i",
            str(temp_mkv_a),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-shortest",
            str(mkv_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    temp_mkv_v.unlink(missing_ok=True)
    temp_mkv_a.unlink(missing_ok=True)

    gt_hindi = {
        "format": "mkv",
        "duration": 3.0,
        "has_audio": True,
        "transcript": "दस्तावेज़ बुद्धि बहुभाषी विश्लेषण",
    }
    (FIXTURES_DIR / "video_speech_hindi.json").write_text(json.dumps(gt_hindi, indent=2, ensure_ascii=False), encoding="utf-8")
    (FIXTURES_DIR / "video_speech_hindi.txt").write_text("दस्तावेज़ बुद्धि बहुभाषी विश्लेषण", encoding="utf-8")

    # 5. video_no_audio.mp4 (Silent MP4)
    silent_path = FIXTURES_DIR / "video_no_audio.mp4"
    frames_silent = []
    for i in range(50):  # 2.0s
        f = np.zeros((height, width, 3), dtype=np.uint8)
        f[:, :] = (50, 50, 50)
        cv2.circle(f, (50 + i * 3, 120), 20, (0, 180, 255), -1)
        frames_silent.append(f)
    temp_silent = FIXTURES_DIR / "temp_silent.mp4"
    _create_frames_video(frames_silent, temp_silent, fps=fps)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(temp_silent), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(silent_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    temp_silent.unlink(missing_ok=True)
    (FIXTURES_DIR / "video_no_audio.txt").write_text("Silent video without audio stream", encoding="utf-8")

    # 6. video_fade_transition.webm (WebM container with fade to black)
    webm_path = FIXTURES_DIR / "video_fade_transition.webm"
    frames_webm = []
    # Scene 1: bright (0.0 to 1.5s = 37 frames)
    for _ in range(37):
        f = np.ones((height, width, 3), dtype=np.uint8) * 200
        cv2.putText(f, "Bright Scene", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        frames_webm.append(f)
    # Fade to black: 1.5 to 2.0s (13 frames)
    for i in range(13):
        val = int(200 * (1.0 - (i / 12.0)))
        f = np.ones((height, width, 3), dtype=np.uint8) * val
        frames_webm.append(f)
    # Scene 2: black (2.0 to 3.0s = 25 frames)
    for _ in range(25):
        f = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.putText(f, "Fade End", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        frames_webm.append(f)

    temp_webm = FIXTURES_DIR / "temp_webm.mp4"
    _create_frames_video(frames_webm, temp_webm, fps=fps)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(temp_webm), "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "30", "-an", str(webm_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    temp_webm.unlink(missing_ok=True)
    (FIXTURES_DIR / "video_fade_transition.txt").write_text("WebM video with gradual fade to black transition", encoding="utf-8")

    # 7. video_short_clip.mp4 (0.5s duration)
    short_path = FIXTURES_DIR / "video_short_clip.mp4"
    frames_short = [np.ones((height, width, 3), dtype=np.uint8) * 128 for _ in range(12)]
    temp_short = FIXTURES_DIR / "temp_short.mp4"
    _create_frames_video(frames_short, temp_short, fps=fps)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(temp_short), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(short_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    temp_short.unlink(missing_ok=True)

    # 8. corrupted_video.mp4 (Corrupted ISO-BMFF header)
    corrupted_path = FIXTURES_DIR / "corrupted_video.mp4"
    corrupted_path.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00BAD_TRUNCATED_STREAM")

    # 9. no_video_stream.bin (Random non-video bytes)
    no_video_path = FIXTURES_DIR / "no_video_stream.bin"
    no_video_path.write_bytes(b"NON_VIDEO_STREAM_DATA_0123456789" * 32)

    print(f"Generated {len(list(FIXTURES_DIR.glob('*.*')))} video fixtures in {FIXTURES_DIR}")


if __name__ == "__main__":
    generate_all_fixtures()
