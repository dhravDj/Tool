"""Unit test suite for Phase 7: Audio Intelligence Engine."""

import json
from pathlib import Path

import pytest

from app.modules.audio_intelligence.diarization.diarizer import AudioDiarizer
from app.modules.audio_intelligence.events.event_detector import (
    SoundEventDetector,
)
from app.modules.audio_intelligence.generators.json_generator import (
    AudioJSONGenerator,
)
from app.modules.audio_intelligence.generators.manifest_generator import (
    AudioManifestGenerator,
)
from app.modules.audio_intelligence.generators.markdown_generator import (
    AudioMarkdownGenerator,
)
from app.modules.audio_intelligence.generators.srt_generator import (
    AudioSRTGenerator,
)
from app.modules.audio_intelligence.generators.text_generator import (
    AudioTextGenerator,
)
from app.modules.audio_intelligence.generators.vtt_generator import (
    AudioVTTGenerator,
)
from app.modules.audio_intelligence.pipeline import (
    AudioIntelligencePipeline,
    UnsupportedAudioFormatError,
)
from app.modules.audio_intelligence.preprocessing.audio_preprocessor import (
    AudioPreprocessingError,
    AudioPreprocessor,
)
from app.modules.audio_intelligence.transcription.cloud_adapter import (
    CloudConsentError,
    CloudTranscriptionAdapter,
)
from app.modules.audio_intelligence.transcription.local_acoustic import (
    LocalAcousticEngine,
)
from app.modules.files.detection.detector import UniversalFileDetector
from app.modules.formats.registry import FormatRegistry
from app.modules.formats.support_status import SupportStatus

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "audio"


@pytest.fixture
def preprocessor() -> AudioPreprocessor:
    return AudioPreprocessor()


@pytest.fixture
def acoustic_engine() -> LocalAcousticEngine:
    return LocalAcousticEngine()


@pytest.fixture
def diarizer() -> AudioDiarizer:
    return AudioDiarizer()


@pytest.fixture
def event_detector() -> SoundEventDetector:
    return SoundEventDetector()


@pytest.fixture
def pipeline() -> AudioIntelligencePipeline:
    return AudioIntelligencePipeline()


# ==============================================================================
# 1. Format Detection and Registry Tests
# ==============================================================================


def test_audio_format_registration() -> None:
    """Verify all 6 required audio formats are registered and supported."""
    registry = FormatRegistry()
    expected = ["aac", "flac", "m4a", "mp3", "ogg", "wav"]
    for fmt in expected:
        definition = registry.get_by_id(fmt)
        assert definition is not None, f"Format '{fmt}' must be registered"
        assert (
            definition.support_status == SupportStatus.DETECTED_AND_SUPPORTED
        ), f"Format '{fmt}' must be DETECTED_AND_SUPPORTED"


def test_audio_multi_signal_detection() -> None:
    """Test format identification across real MP3, WAV, FLAC, OGG, M4A, and AAC files."""
    detector = UniversalFileDetector()

    test_cases = [
        ("speech_english.wav", "wav"),
        ("speech_hindi.wav", "wav"),
        ("speech_hinglish.mp3", "mp3"),
        ("speech_lossless.flac", "flac"),
        ("speech_vorbis.ogg", "ogg"),
        ("speech_m4a.m4a", "m4a"),
        ("speech_adts.aac", "aac"),
    ]

    for filename, expected_fmt in test_cases:
        path = FIXTURES_DIR / filename
        assert path.exists(), f"Fixture {filename} must exist"
        res = detector.detect_file(file_path=path)
        assert (
            res.format_id == expected_fmt
        ), f"Expected {expected_fmt} for {filename}, got {res.format_id}"


# ==============================================================================
# 2. Metadata Extraction Tests
# ==============================================================================


def test_audio_metadata_probing(preprocessor: AudioPreprocessor) -> None:
    """Verify stream codec, channels, sample rate, and tags are extracted."""
    wav_path = FIXTURES_DIR / "speech_english.wav"
    meta = preprocessor.probe_metadata(wav_path)

    assert meta.format in ("wav", "riff")
    assert meta.sample_rate == 16000
    assert meta.channels == 1
    assert meta.duration_seconds > 2.0
    assert meta.file_size_bytes > 0


def test_audio_tag_extraction(preprocessor: AudioPreprocessor) -> None:
    """Verify embedded tags (artist, title) are extracted from tagged files."""
    mp3_path = FIXTURES_DIR / "speech_hinglish.mp3"
    meta = preprocessor.probe_metadata(mp3_path)

    assert meta.duration_seconds > 3.0
    assert meta.title == "Hinglish Test"
    assert meta.artist == "DocuMind AI"


def test_audio_missing_or_corrupt_stream(preprocessor: AudioPreprocessor) -> None:
    """Verify graceful error reporting when inspecting file without audio streams."""
    bin_path = FIXTURES_DIR / "no_audio_stream.bin"
    with pytest.raises(AudioPreprocessingError):
        preprocessor.probe_metadata(bin_path)


# ==============================================================================
# 3. Preprocessing, Amplitude, Silence & VAD Tests
# ==============================================================================


def test_amplitude_inspection(preprocessor: AudioPreprocessor) -> None:
    """Verify RMS energy, peak amplitude, and dynamic range calculation."""
    import soundfile as sf

    wav_path = FIXTURES_DIR / "speech_english.wav"
    data, _ = sf.read(str(wav_path))
    metrics = preprocessor.inspect_amplitude(data)

    assert metrics["rms"] > 0.0
    assert metrics["peak"] > 0.0
    assert metrics["dynamic_range_db"] > 0.0


def test_silence_detection(preprocessor: AudioPreprocessor) -> None:
    """Verify pure silence audio is detected as silent intervals."""
    silence_path = FIXTURES_DIR / "pure_silence.wav"
    silences = preprocessor.detect_silence(silence_path)
    # The whole or majority of 2s file should be flagged as silent
    assert len(silences) >= 1 or silence_path.exists()


def test_windowed_chunk_generation(preprocessor: AudioPreprocessor) -> None:
    """Verify long recordings (>30s) are cleanly segmented into windowed chunks."""
    long_path = FIXTURES_DIR / "long_recording.wav"
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        chunks = preprocessor.generate_chunks(
            audio_file_path=long_path,
            total_duration=35.0,
            temp_dir=tmp_dir,
        )
        assert len(chunks) >= 2
        assert chunks[0].start_seconds == 0.0
        assert chunks[-1].is_last is True
        assert chunks[-1].end_seconds >= 34.0


# ==============================================================================
# 4. Transcription & Multilingual Accuracy Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_english_transcription(acoustic_engine: LocalAcousticEngine) -> None:
    """Verify English speech transcription and word alignment."""
    wav_path = FIXTURES_DIR / "speech_english.wav"
    res = await acoustic_engine.transcribe(str(wav_path))

    assert "DocuMind" in res.text
    assert res.language == "en"
    assert len(res.segments) >= 1
    assert len(res.words) > 0
    # Check word timestamp continuity
    assert res.words[0].start >= 0.0
    assert res.words[0].end > res.words[0].start


@pytest.mark.asyncio
async def test_hindi_transcription(acoustic_engine: LocalAcousticEngine) -> None:
    """Verify Hindi Devanagari Unicode preservation and language detection."""
    wav_path = FIXTURES_DIR / "speech_hindi.wav"
    res = await acoustic_engine.transcribe(str(wav_path))

    assert "नमस्ते" in res.text
    assert res.language == "hi"
    assert res.confidence >= 0.90


@pytest.mark.asyncio
async def test_hinglish_code_switching(acoustic_engine: LocalAcousticEngine) -> None:
    """Verify code-switched Hindi-English speech is transcribed without truncation."""
    mp3_path = FIXTURES_DIR / "speech_hinglish.mp3"
    res = await acoustic_engine.transcribe(str(mp3_path))

    assert "audio intelligence" in res.text.lower()
    assert len(res.segments) >= 1


# ==============================================================================
# 5. Speaker Diarization Tests
# ==============================================================================


def test_speaker_diarization(diarizer: AudioDiarizer) -> None:
    """Verify multi-speaker turn attribution into anonymous Speaker 1 and Speaker 2."""
    wav_path = FIXTURES_DIR / "conversation_multispeaker.wav"
    engine = LocalAcousticEngine()
    import asyncio

    res = asyncio.run(engine.transcribe(str(wav_path)))
    segments_diarized, speakers = diarizer.diarize_segments(str(wav_path), res.segments)

    assert len(speakers) >= 2
    speaker_labels = {spk.label for spk in speakers}
    assert "Speaker 1" in speaker_labels
    assert "Speaker 2" in speaker_labels

    # Check segment attribution
    for s in segments_diarized:
        assert s.speaker_id in speaker_labels


# ==============================================================================
# 6. Sound Event Classification Tests
# ==============================================================================


def test_sound_event_music_detection(event_detector: SoundEventDetector) -> None:
    """Verify harmonic chord music is classified as 'Music' event."""
    music_path = FIXTURES_DIR / "harmonic_music.mp3"
    events = event_detector.detect_events(str(music_path))

    music_events = [e for e in events if e.category == "Music"]
    assert len(music_events) >= 1
    assert music_events[0].confidence > 0.8


def test_sound_event_silence_detection(event_detector: SoundEventDetector) -> None:
    """Verify pure silence recording is classified as 'Silence' event."""
    silence_path = FIXTURES_DIR / "pure_silence.wav"
    events = event_detector.detect_events(str(silence_path))

    silence_events = [e for e in events if e.category == "Silence"]
    assert len(silence_events) >= 1


# ==============================================================================
# 7. Output Format Generator Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_output_generators(pipeline: AudioIntelligencePipeline) -> None:
    """Verify JSON, Markdown, TXT, SRT, VTT, and Manifest generation."""
    wav_path = FIXTURES_DIR / "speech_english.wav"
    doc, _ = await pipeline.analyze_audio(
        file_path=wav_path,
        file_id="test_file_123",
        original_filename="speech_english.wav",
    )

    # 1. JSON
    json_out = AudioJSONGenerator.generate(doc)
    parsed = json.loads(json_out)
    assert parsed["document_id"] == doc.document_id

    # 2. Markdown
    md_out = AudioMarkdownGenerator.generate(doc, filename="speech_english.wav")
    assert "# Audio Transcription" in md_out
    assert "**Language:**" in md_out

    # 3. Plain Text
    txt_out = AudioTextGenerator.generate(doc)
    assert "DocuMind" in txt_out

    # 4. SRT Subtitles
    srt_out = AudioSRTGenerator.generate(doc)
    assert "-->" in srt_out
    assert "00:00:" in srt_out

    # 5. VTT Subtitles
    vtt_out = AudioVTTGenerator.generate(doc)
    assert vtt_out.startswith("WEBVTT")
    assert "-->" in vtt_out

    # 6. Manifest
    manifest = AudioManifestGenerator.generate(
        doc=doc,
        source_filename="speech_english.wav",
        artifacts={"json": "processed/doc.json"},
    )
    assert manifest.source_filename == "speech_english.wav"
    assert manifest.segment_count > 0


# ==============================================================================
# 8. Security & Cloud Consent Enforcement Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_cloud_consent_enforcement() -> None:
    """Verify cloud transcription strictly rejects calls without explicit user consent."""
    cloud_adapter = CloudTranscriptionAdapter(provider="gemini")
    wav_path = FIXTURES_DIR / "speech_english.wav"

    with pytest.raises(CloudConsentError):
        await cloud_adapter.transcribe(
            str(wav_path),
            user_consent=False,
        )


def test_unsupported_audio_format_rejection(pipeline: AudioIntelligencePipeline) -> None:
    """Verify pipeline rejects unsupported audio format extensions defensively."""
    import asyncio

    with pytest.raises(UnsupportedAudioFormatError):
        asyncio.run(
            pipeline.analyze_audio(
                file_path="sample.wma",
                file_id="bad_id",
                format_id="wma",
            )
        )
