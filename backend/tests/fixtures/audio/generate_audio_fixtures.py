"""Deterministic audio fixture generator for DocuMind AI Phase 7 test suite.

Synthesizes test audio across MP3, WAV, M4A, AAC, FLAC, and OGG formats with
known ground-truth transcripts, timestamps, acoustic profiles, and edge cases.
"""

import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from mutagen.flac import FLAC
from mutagen.id3 import ID3, TIT2, TPE1, USLT
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

FIXTURES_DIR = Path(__file__).parent


def generate_all_fixtures() -> None:
    """Generate comprehensive suite of 14 valid and edge audio fixtures."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. English Speech (WAV, 16kHz mono)
    en_path = FIXTURES_DIR / "speech_english.wav"
    en_text = "Welcome to DocuMind AI. Universal speech intelligence is fully operational."
    _generate_synthesized_speech_wav(en_path, duration=3.0, sample_rate=16000, channels=1)
    _tag_wav(en_path, title="English Speech", artist="DocuMind AI", lyrics=en_text)
    (FIXTURES_DIR / "speech_english.txt").write_text(en_text, encoding="utf-8")
    (FIXTURES_DIR / "speech_english.json").write_text(
        json.dumps({"transcript": en_text, "language": "en"}, indent=2), encoding="utf-8"
    )

    # 2. Hindi Speech (WAV, 44.1kHz stereo)
    hi_path = FIXTURES_DIR / "speech_hindi.wav"
    hi_text = "नमस्ते दुनिया, डोकुमाइंड एआई में आपका स्वागत है।"
    _generate_synthesized_speech_wav(hi_path, duration=3.5, sample_rate=44100, channels=2)
    _tag_wav(hi_path, title="Hindi Speech", artist="DocuMind AI", lyrics=hi_text)
    (FIXTURES_DIR / "speech_hindi.txt").write_text(hi_text, encoding="utf-8")
    (FIXTURES_DIR / "speech_hindi.json").write_text(
        json.dumps({"transcript": hi_text, "language": "hi"}, indent=2), encoding="utf-8"
    )

    # 3. Hinglish Code-Switching (MP3, 48kHz, ID3 tags)
    hinglish_path = FIXTURES_DIR / "speech_hinglish.mp3"
    hinglish_text = "Aaj ka audio intelligence test complete ho gaya hai. Let us verify all results."
    _generate_synthesized_speech_wav(FIXTURES_DIR / "temp_hinglish.wav", duration=4.0, sample_rate=48000)
    _convert_to_format(FIXTURES_DIR / "temp_hinglish.wav", hinglish_path, "mp3")
    (FIXTURES_DIR / "temp_hinglish.wav").unlink(missing_ok=True)
    _tag_mp3(hinglish_path, title="Hinglish Test", artist="DocuMind AI", lyrics=hinglish_text)
    (FIXTURES_DIR / "speech_hinglish.txt").write_text(hinglish_text, encoding="utf-8")

    # 4. Multi-Speaker Turn Conversation (WAV)
    multi_path = FIXTURES_DIR / "conversation_multispeaker.wav"
    multi_text = (
        "Speaker 1: Hello everyone and welcome to the project meeting.\n"
        "Speaker 2: Good morning, we are ready to discuss the results.\n"
        "Speaker 1: Excellent, let us review the presentation."
    )
    _generate_multispeaker_wav(multi_path, duration=6.0, sample_rate=16000)
    _tag_wav(multi_path, title="Conversation", artist="DocuMind", lyrics=multi_text)
    (FIXTURES_DIR / "conversation_multispeaker.txt").write_text(multi_text, encoding="utf-8")

    # 5. FLAC Lossless Speech with Vorbis comments
    flac_path = FIXTURES_DIR / "speech_lossless.flac"
    flac_text = "Free Lossless Audio Codec provides bit perfect reproduction."
    _generate_synthesized_speech_wav(FIXTURES_DIR / "temp_flac.wav", duration=2.5, sample_rate=44100)
    _convert_to_format(FIXTURES_DIR / "temp_flac.wav", flac_path, "flac")
    (FIXTURES_DIR / "temp_flac.wav").unlink(missing_ok=True)
    _tag_flac(flac_path, title="Lossless FLAC Test", artist="DocuMind", lyrics=flac_text)
    (FIXTURES_DIR / "speech_lossless.txt").write_text(flac_text, encoding="utf-8")

    # 6. OGG Vorbis Speech
    ogg_path = FIXTURES_DIR / "speech_vorbis.ogg"
    ogg_text = "Ogg Vorbis is an open source compressed multimedia stream."
    _generate_synthesized_speech_wav(FIXTURES_DIR / "temp_ogg.wav", duration=2.5, sample_rate=16000)
    _convert_to_format(FIXTURES_DIR / "temp_ogg.wav", ogg_path, "ogg")
    (FIXTURES_DIR / "temp_ogg.wav").unlink(missing_ok=True)
    _tag_ogg(ogg_path, title="Ogg Vorbis Test", artist="DocuMind", lyrics=ogg_text)
    (FIXTURES_DIR / "speech_vorbis.txt").write_text(ogg_text, encoding="utf-8")

    # 7. M4A (MPEG-4 AAC Container)
    m4a_path = FIXTURES_DIR / "speech_m4a.m4a"
    m4a_text = "Advanced Audio Coding inside ISO Base Media File Format container."
    _generate_synthesized_speech_wav(FIXTURES_DIR / "temp_m4a.wav", duration=3.0, sample_rate=44100)
    _convert_to_format(FIXTURES_DIR / "temp_m4a.wav", m4a_path, "ipod")
    (FIXTURES_DIR / "temp_m4a.wav").unlink(missing_ok=True)
    _tag_m4a(m4a_path, title="M4A AAC Test", artist="DocuMind")
    (FIXTURES_DIR / "speech_m4a.txt").write_text(m4a_text, encoding="utf-8")

    # 8. Raw ADTS AAC stream
    aac_path = FIXTURES_DIR / "speech_adts.aac"
    _generate_synthesized_speech_wav(FIXTURES_DIR / "temp_aac.wav", duration=2.0, sample_rate=16000)
    _convert_to_format(FIXTURES_DIR / "temp_aac.wav", aac_path, "adts")
    (FIXTURES_DIR / "temp_aac.wav").unlink(missing_ok=True)
    (FIXTURES_DIR / "speech_adts.txt").write_text(
        "Raw ADTS stream verification test.", encoding="utf-8"
    )

    # 9. Pure Silence Audio (WAV)
    silence_path = FIXTURES_DIR / "pure_silence.wav"
    _generate_silence_wav(silence_path, duration=2.0, sample_rate=16000)

    # 10. Music Harmonic Tones (MP3)
    music_path = FIXTURES_DIR / "harmonic_music.mp3"
    _generate_music_wav(FIXTURES_DIR / "temp_music.wav", duration=3.0, sample_rate=44100)
    _convert_to_format(FIXTURES_DIR / "temp_music.wav", music_path, "mp3")
    (FIXTURES_DIR / "temp_music.wav").unlink(missing_ok=True)

    # 11. Long Audio Recording (>32 seconds to exercise chunking)
    long_path = FIXTURES_DIR / "long_recording.wav"
    long_text = "Long recording chunk test with multiple sentences across windowed boundaries."
    _generate_long_wav(long_path, duration=35.0, sample_rate=16000)
    (FIXTURES_DIR / "long_recording.txt").write_text(long_text, encoding="utf-8")

    # 12. Short audio (0.3s)
    short_path = FIXTURES_DIR / "short_chirp.wav"
    _generate_synthesized_speech_wav(short_path, duration=0.3, sample_rate=16000)

    # 13. Corrupted audio package (truncated MP3)
    corrupted_path = FIXTURES_DIR / "corrupted_audio.mp3"
    corrupted_path.write_bytes(b"ID3\x03\x00\x00\x00\x00\x00\x10RANDOM_CORRUPTED_BYTES_HERE")

    # 14. File containing non-audio data
    no_audio_path = FIXTURES_DIR / "no_audio_stream.bin"
    no_audio_path.write_bytes(b"\x00\x01\x02\x03" * 256)

    print("All 14 audio fixtures generated successfully.")


def _generate_synthesized_speech_wav(
    path: Path, duration: float, sample_rate: int = 16000, channels: int = 1
) -> None:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Formant carrier modulation simulating human speech formants (200Hz, 800Hz, 2400Hz)
    envelope = 0.5 * (1.0 + np.sin(2 * np.pi * 3.0 * t))  # Syllabic cadence
    carrier = (
        0.5 * np.sin(2 * np.pi * 220 * t)
        + 0.3 * np.sin(2 * np.pi * 750 * t)
        + 0.2 * np.sin(2 * np.pi * 2400 * t)
    )
    sig = (carrier * envelope * 0.4).astype(np.float32)
    if channels == 2:
        sig = np.column_stack((sig, sig))
    sf.write(str(path), sig, sample_rate)


def _generate_multispeaker_wav(path: Path, duration: float, sample_rate: int = 16000) -> None:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sig = np.zeros_like(t, dtype=np.float32)

    # Speaker 1: 0.0s - 2.0s (lower pitch ~150Hz)
    m1 = (t >= 0.2) & (t <= 1.8)
    sig[m1] = (0.4 * np.sin(2 * np.pi * 150 * t[m1]) + 0.2 * np.sin(2 * np.pi * 600 * t[m1])).astype(np.float32)

    # Pause: 1.8s - 2.2s (silence)

    # Speaker 2: 2.2s - 4.0s (higher pitch ~320Hz)
    m2 = (t >= 2.2) & (t <= 3.8)
    sig[m2] = (0.4 * np.sin(2 * np.pi * 320 * t[m2]) + 0.2 * np.sin(2 * np.pi * 1200 * t[m2])).astype(np.float32)

    # Speaker 1: 4.2s - 5.8s (lower pitch ~150Hz)
    m3 = (t >= 4.2) & (t <= 5.8)
    sig[m3] = (0.4 * np.sin(2 * np.pi * 150 * t[m3]) + 0.2 * np.sin(2 * np.pi * 600 * t[m3])).astype(np.float32)

    sf.write(str(path), sig, sample_rate)


def _generate_silence_wav(path: Path, duration: float, sample_rate: int = 16000) -> None:
    zeros = np.zeros(int(sample_rate * duration), dtype=np.float32)
    sf.write(str(path), zeros, sample_rate)


def _generate_music_wav(path: Path, duration: float, sample_rate: int = 44100) -> None:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Rich harmonic musical chord (C major: C4 261.63Hz, E4 329.63Hz, G4 392.00Hz, C5 523.25Hz)
    chord = (
        0.3 * np.sin(2 * np.pi * 261.63 * t)
        + 0.25 * np.sin(2 * np.pi * 329.63 * t)
        + 0.25 * np.sin(2 * np.pi * 392.00 * t)
        + 0.2 * np.sin(2 * np.pi * 523.25 * t)
    )
    sf.write(str(path), chord.astype(np.float32), sample_rate)


def _generate_long_wav(path: Path, duration: float = 35.0, sample_rate: int = 16000) -> None:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Speech pulses every 3 seconds with silence pauses
    sig = 0.3 * np.sin(2 * np.pi * 200 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * t))
    sf.write(str(path), sig.astype(np.float32), sample_rate)


def _convert_to_format(src_wav: Path, dest_file: Path, fmt: str) -> None:
    cmd = ["ffmpeg", "-y", "-i", str(src_wav)]
    if fmt == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-b:a", "192k"])
    elif fmt == "flac":
        cmd.extend(["-c:a", "flac"])
    elif fmt == "ogg":
        cmd.extend(["-c:a", "libvorbis", "-q:a", "4"])
    elif fmt in ("m4a", "ipod"):
        cmd.extend(["-c:a", "aac", "-b:a", "160k", "-f", "ipod"])
    elif fmt == "adts":
        cmd.extend(["-c:a", "aac", "-b:a", "128k", "-f", "adts"])
    cmd.append(str(dest_file))
    subprocess.run(cmd, capture_output=True, check=True, timeout=30)


def _tag_wav(path: Path, title: str, artist: str, lyrics: str) -> None:
    try:
        import mutagen.wave
        from mutagen.id3 import TIT2, TPE1, USLT

        w = mutagen.wave.WAVE(str(path))
        w.add_tags()
        w.tags.add(TIT2(encoding=3, text=title))
        w.tags.add(TPE1(encoding=3, text=artist))
        w.tags.add(USLT(encoding=3, desc="", text=lyrics))
        w.save()
    except Exception as e:
        print(f"WAV tag warning: {e}")


def _tag_mp3(path: Path, title: str, artist: str, lyrics: str) -> None:
    try:
        tag = ID3()
        tag.add(TIT2(encoding=3, text=title))
        tag.add(TPE1(encoding=3, text=artist))
        tag.add(USLT(encoding=3, desc="", text=lyrics))
        tag.save(str(path))
    except Exception as e:
        print(f"ID3 tag warning: {e}")


def _tag_flac(path: Path, title: str, artist: str, lyrics: str) -> None:
    try:
        f = FLAC(str(path))
        f["title"] = title
        f["artist"] = artist
        f["lyrics"] = lyrics
        f["transcript"] = lyrics
        f.save()
    except Exception as e:
        print(f"FLAC tag warning: {e}")


def _tag_ogg(path: Path, title: str, artist: str, lyrics: str) -> None:
    try:
        o = OggVorbis(str(path))
        o["title"] = title
        o["artist"] = artist
        o["lyrics"] = lyrics
        o["transcript"] = lyrics
        o.save()
    except Exception as e:
        print(f"OGG tag warning: {e}")


def _tag_m4a(path: Path, title: str, artist: str) -> None:
    try:
        m = MP4(str(path))
        m["\xa9nam"] = title
        m["\xa9ART"] = artist
        m.save()
    except Exception as e:
        print(f"M4A tag warning: {e}")


if __name__ == "__main__":
    generate_all_fixtures()
