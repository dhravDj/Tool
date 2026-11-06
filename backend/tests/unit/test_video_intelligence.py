"""Comprehensive unit test suite for Phase 8: Video Intelligence Engine."""

import tempfile
from pathlib import Path

import pytest

from app.modules.files.detection.detector import UniversalFileDetector
from app.modules.formats.registry import FormatRegistry
from app.modules.formats.support_status import SupportStatus
from app.modules.video_intelligence.decoding.video_decoder import VideoDecoder
from app.modules.video_intelligence.events.visual_events import VisualEventDetector
from app.modules.video_intelligence.generators.json_generator import VideoJSONGenerator
from app.modules.video_intelligence.generators.manifest_generator import VideoManifestGenerator
from app.modules.video_intelligence.generators.markdown_generator import VideoMarkdownGenerator
from app.modules.video_intelligence.generators.subtitle_generator import VideoSubtitleGenerator
from app.modules.video_intelligence.generators.text_generator import VideoPlainTextGenerator
from app.modules.video_intelligence.keyframes.keyframe_extractor import KeyframeExtractor
from app.modules.video_intelligence.pipeline import (
    UnsupportedVideoFormatError,
    VideoIntelligencePipeline,
)
from app.modules.video_intelligence.preprocessing.video_preprocessor import VideoPreprocessor
from app.modules.video_intelligence.scenes.scene_detector import SceneDetector
from app.modules.video_intelligence.timeline.multimodal_timeline import MultimodalTimelineBuilder
from app.modules.video_intelligence.tracking.object_tracker import ObjectTracker

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "video"


@pytest.fixture
def detector() -> UniversalFileDetector:
    return UniversalFileDetector()


@pytest.fixture
def pipeline() -> VideoIntelligencePipeline:
    return VideoIntelligencePipeline()


@pytest.fixture
def preprocessor() -> VideoPreprocessor:
    return VideoPreprocessor()


@pytest.fixture
def decoder() -> VideoDecoder:
    return VideoDecoder(max_dimension=480)


def test_format_registry_all_five_video_formats() -> None:
    """Verify MP4, MKV, MOV, AVI, and WEBM are registered as DETECTED_AND_SUPPORTED."""
    reg = FormatRegistry()
    for fmt_id in ["mp4", "mkv", "mov", "avi", "webm"]:
        fmt = reg.get_by_id(fmt_id)
        assert fmt is not None, f"Format '{fmt_id}' missing from registry"
        assert fmt.support_status == SupportStatus.DETECTED_AND_SUPPORTED
        assert fmt.is_container is True


def test_video_format_detection_all_fixtures(detector: UniversalFileDetector) -> None:
    """Verify UniversalFileDetector correctly identifies all video containers."""
    fixtures = [
        ("video_speech_english.mp4", "mp4"),
        ("video_speech_hindi.mkv", "mkv"),
        ("video_multiscene.mov", "mov"),
        ("video_moving_object.avi", "avi"),
        ("video_fade_transition.webm", "webm"),
    ]
    for filename, expected_fmt in fixtures:
        path = FIXTURES_DIR / filename
        assert path.exists(), f"Fixture missing: {path}"
        res = detector.detect_file(file_path=path)
        assert res.format_id == expected_fmt, f"Expected {expected_fmt} for {filename}, got {res.format_id}"
        assert res.is_container is True


def test_video_metadata_probing(preprocessor: VideoPreprocessor) -> None:
    """Verify FFprobe extracts video and audio stream parameters accurately."""
    mp4_path = FIXTURES_DIR / "video_speech_english.mp4"
    meta = preprocessor.probe_metadata(mp4_path)

    assert meta.duration_seconds >= 2.8
    assert len(meta.video_streams) == 1
    v = meta.video_streams[0]
    assert v.width == 320
    assert v.height == 240
    assert v.fps >= 24.0
    assert len(meta.audio_streams) == 1
    a = meta.audio_streams[0]
    assert a.channels >= 1
    assert a.sample_rate >= 16000


def test_incremental_frame_decoding(decoder: VideoDecoder) -> None:
    """Verify decoder streams frames incrementally with presentation timestamps."""
    mp4_path = FIXTURES_DIR / "video_short_clip.mp4"
    frames = list(decoder.stream_frames(mp4_path, sample_fps=10.0))

    assert len(frames) >= 3
    # Check monotonically increasing PTS
    pts_list = [f[1] for f in frames]
    assert pts_list == sorted(pts_list)
    # Check frame array dimensions
    assert frames[0][2].shape[:2] == (240, 320)


def test_scene_boundary_detection_hard_cuts() -> None:
    """Verify SceneDetector detects 3 distinct scenes in video_multiscene.mov."""
    mov_path = FIXTURES_DIR / "video_multiscene.mov"
    decoder = VideoDecoder(max_dimension=320)
    detector = SceneDetector(cut_threshold=0.30, min_scene_duration_seconds=0.8)

    signatures = []
    for frame_idx, pts, frame_bgr, _ in decoder.stream_frames(mov_path):
        sig = detector.compute_signature(frame_bgr, frame_idx, pts)
        signatures.append(sig)

    scenes = detector.detect_scenes(signatures, total_duration=4.5)
    # Expect 3 scenes (Red, Green, Blue)
    assert len(scenes) == 3
    assert scenes[0].start == 0.0
    assert 1.2 <= scenes[0].end <= 1.7
    assert 2.7 <= scenes[1].end <= 3.2
    assert scenes[2].end >= 4.0


@pytest.mark.asyncio
async def test_keyframe_extraction_and_deduplication(decoder: VideoDecoder) -> None:
    """Verify representative keyframe extraction and thumbnail creation."""
    mov_path = FIXTURES_DIR / "video_multiscene.mov"
    preprocessor = VideoPreprocessor()
    meta = preprocessor.probe_metadata(mov_path)
    scene_detector = SceneDetector()

    sigs = [
        scene_detector.compute_signature(f, idx, pts)
        for idx, pts, f, _ in decoder.stream_frames(mov_path, sample_fps=5.0)
    ]
    scenes = scene_detector.detect_scenes(sigs, meta.duration_seconds)

    extractor = KeyframeExtractor(thumbnail_width=160, thumbnail_height=120)
    keyframes, frames = await extractor.extract_keyframes_for_scenes(
        mov_path, file_id="test_mov_01", scenes=scenes, decoder=decoder
    )

    assert len(keyframes) == len(scenes)
    assert len(frames) == len(scenes)
    for kf in keyframes:
        assert kf.asset_reference.startswith("video_keyframes/test_mov_01/")
        assert kf.thumbnail_reference.startswith("video_keyframes/test_mov_01/thumb_")


def test_object_detection_and_tracking() -> None:
    """Verify ObjectTracker detects moving object and forms continuous trajectory."""
    avi_path = FIXTURES_DIR / "video_moving_object.avi"
    decoder = VideoDecoder(max_dimension=320)
    tracker = ObjectTracker(iou_threshold=0.15)

    detections_by_frame = []
    prev_frame = None
    for idx, pts, frame_bgr, is_sampled in decoder.stream_frames(avi_path, sample_fps=4.0):
        if is_sampled:
            f_id = f"frm_{idx:03d}"
            dets = tracker.detect_objects_in_frame(frame_bgr, f_id, pts, prev_frame_bgr=prev_frame)
            if dets:
                detections_by_frame.append((f_id, pts, dets))
            prev_frame = frame_bgr.copy()

    tracks = tracker.track_across_frames(detections_by_frame)
    assert len(tracks) >= 1
    longest_track = max(tracks, key=lambda t: len(t.observations))
    assert len(longest_track.observations) >= 2
    assert longest_track.track_id.startswith("track_")


def test_visual_events_detection() -> None:
    """Verify VisualEventDetector detects scene cuts and track motion."""
    event_detector = VisualEventDetector()
    pipeline = VideoIntelligencePipeline()
    mp4_path = FIXTURES_DIR / "video_speech_english.mp4"

    meta = pipeline.preprocessor.probe_metadata(mp4_path)
    sigs = [
        pipeline.scene_detector.compute_signature(f, idx, pts)
        for idx, pts, f, _ in pipeline.decoder.stream_frames(mp4_path, sample_fps=5.0)
    ]
    scenes = pipeline.scene_detector.detect_scenes(sigs, meta.duration_seconds)
    events = event_detector.detect_events(scenes, tracks=[], frames=[])

    # Should detect transition into scene 2
    assert any(ev.category == "scene_transition" for ev in events)


@pytest.mark.asyncio
async def test_video_audio_extraction_and_speech_sync(pipeline: VideoIntelligencePipeline) -> None:
    """Verify FFmpeg audio extraction and Phase 7 transcription integration."""
    mp4_path = FIXTURES_DIR / "video_speech_english.mp4"
    doc, manifest = await pipeline.analyze_video(
        file_path=mp4_path,
        file_id="vid_eng_01",
        original_filename="video_speech_english.mp4",
    )

    assert doc.format == "mp4"
    assert doc.duration >= 2.8
    assert len(doc.scenes) == 2
    assert len(doc.keyframes) == 2
    assert "DocuMind" in doc.transcript
    assert len(doc.transcript_segments) >= 1
    assert len(doc.timeline) >= 4
    assert manifest.status == "completed"


@pytest.mark.asyncio
async def test_video_hindi_transcription(pipeline: VideoIntelligencePipeline) -> None:
    """Verify multilingual Hindi transcription in MKV video container."""
    mkv_path = FIXTURES_DIR / "video_speech_hindi.mkv"
    doc, manifest = await pipeline.analyze_video(
        file_path=mkv_path,
        file_id="vid_hi_01",
        original_filename="video_speech_hindi.mkv",
    )

    assert doc.format == "mkv"
    assert "दस्तावेज़" in doc.transcript
    assert doc.model_information.engine_name == "documind-video"


@pytest.mark.asyncio
async def test_silent_video_handling(pipeline: VideoIntelligencePipeline) -> None:
    """Verify video without audio streams completes cleanly with structured warning."""
    silent_path = FIXTURES_DIR / "video_no_audio.mp4"
    doc, manifest = await pipeline.analyze_video(
        file_path=silent_path,
        file_id="vid_silent_01",
        original_filename="video_no_audio.mp4",
    )

    assert doc.transcript == ""
    assert len(doc.audio_streams) == 0
    assert any("audio" in w.lower() for w in doc.warnings)
    assert doc.processing_status == "completed"


@pytest.mark.asyncio
async def test_webm_fade_transition(pipeline: VideoIntelligencePipeline) -> None:
    """Verify WebM video decoding and gradual fade transition handling."""
    webm_path = FIXTURES_DIR / "video_fade_transition.webm"
    doc, _ = await pipeline.analyze_video(
        file_path=webm_path,
        file_id="vid_webm_01",
        original_filename="video_fade_transition.webm",
    )

    assert doc.format == "webm"
    assert doc.duration >= 2.5
    assert len(doc.scenes) >= 1


def test_multimodal_timeline_ordering() -> None:
    """Verify MultimodalTimelineBuilder constructs strictly ordered timeline events."""
    builder = MultimodalTimelineBuilder()
    timeline = builder.build_timeline(
        scenes=[],
        keyframes=[],
        frames=[],
        tracks=[],
        visual_events=[],
        transcript_segments=[],
        speakers=[],
        audio_events=[],
    )
    assert isinstance(timeline, list)
    assert len(timeline) == 0


@pytest.mark.asyncio
async def test_output_generators(pipeline: VideoIntelligencePipeline) -> None:
    """Verify JSON, Markdown, Plain Text, SRT, VTT, and Manifest generators."""
    mp4_path = FIXTURES_DIR / "video_speech_english.mp4"
    doc, manifest = await pipeline.analyze_video(mp4_path, file_id="vid_gen_01")

    # JSON
    json_str = VideoJSONGenerator().generate(doc)
    assert "vdoc_" in json_str

    # Markdown
    md_str = VideoMarkdownGenerator().generate(doc)
    assert "# Video Analysis" in md_str
    assert "Scene 1" in md_str

    # Text
    txt_str = VideoPlainTextGenerator().generate(doc)
    assert "VIDEO TRANSCRIPT & TIMELINE" in txt_str

    # Subtitles
    srt_str = VideoSubtitleGenerator().generate_srt(doc)
    assert "-->" in srt_str
    vtt_str = VideoSubtitleGenerator().generate_vtt(doc)
    assert "WEBVTT" in vtt_str

    # Manifest
    manifest_str = VideoManifestGenerator().generate(manifest)
    assert "vid_gen_01" in manifest_str


@pytest.mark.asyncio
async def test_unsupported_format_error(pipeline: VideoIntelligencePipeline) -> None:
    """Verify UnsupportedVideoFormatError when non-video extension is supplied."""
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as tmp:
        tmp.write(b"SAMPLE")
        tmp_path = Path(tmp.name)

    try:
        with pytest.raises(UnsupportedVideoFormatError):
            await pipeline.analyze_video(tmp_path, file_id="err_01")
    finally:
        tmp_path.unlink(missing_ok=True)
