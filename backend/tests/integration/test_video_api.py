"""Integration tests for Video Intelligence API endpoints."""

import io
from pathlib import Path

import pytest
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "video"


@pytest.mark.asyncio
async def test_video_capabilities_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/video-intelligence/capabilities."""
    res = await async_client.get("/api/v1/video-intelligence/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    for fmt in ["mp4", "mkv", "mov", "avi", "webm"]:
        assert fmt in data["supported_formats"]

    assert data["scene_detection_available"] is True
    assert data["tracking_available"] is True
    assert data["audio_integration_available"] is True


@pytest.mark.asyncio
async def test_video_api_lifecycle(async_client: AsyncClient) -> None:
    """Test complete video lifecycle: upload -> analyze -> summary -> scenes -> keyframes -> timeline -> export."""
    fixture_path = FIXTURES_DIR / "video_speech_english.mp4"
    assert fixture_path.exists(), "video_speech_english.mp4 fixture must exist"

    file_bytes = fixture_path.read_bytes()

    # 1. Upload and persist file
    files = {
        "file": (
            "test_video.mp4",
            io.BytesIO(file_bytes),
            "video/mp4",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 2. Trigger Video Analysis
    analyze_res = await async_client.post(f"/api/v1/files/{file_id}/analyze-video")
    assert analyze_res.status_code == 200
    manifest = analyze_res.json()["data"]
    assert manifest["file_id"] == file_id
    assert manifest["status"] == "completed"
    assert manifest["scene_count"] >= 1
    assert manifest["keyframe_count"] >= 1

    # 3. Retrieve Video Analysis Overview
    overview_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis")
    assert overview_res.status_code == 200
    overview_data = overview_res.json()["data"]
    assert overview_data["status"] == "completed"
    assert overview_data["duration_seconds"] > 2.0
    assert overview_data["width"] == 320
    assert overview_data["height"] == 240

    # 4. Retrieve Full Canonical VideoDocument Result
    doc_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/result")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()["data"]
    assert len(doc_data["scenes"]) >= 1
    assert len(doc_data["keyframes"]) >= 1

    # 5. Retrieve Video Summary
    sum_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()["data"]
    assert sum_data["scene_count"] >= 1

    # 6. Retrieve Scenes and Specific Scene
    scenes_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/scenes")
    assert scenes_res.status_code == 200
    scenes_list = scenes_res.json()["data"]
    assert len(scenes_list) >= 1
    first_scene_id = scenes_list[0]["scene_id"]

    sc_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/scenes/{first_scene_id}")
    assert sc_res.status_code == 200
    assert sc_res.json()["data"]["scene_id"] == first_scene_id

    # 7. Retrieve Keyframes
    kf_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/keyframes")
    assert kf_res.status_code == 200
    assert len(kf_res.json()["data"]) >= 1

    # 8. Retrieve Timeline
    tl_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/timeline")
    assert tl_res.status_code == 200
    assert len(tl_res.json()["data"]) >= 1

    # 9. Retrieve Synchronized Transcript
    tr_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/transcript")
    assert tr_res.status_code == 200
    tr_data = tr_res.json()["data"]
    assert "DocuMind" in tr_data["transcript"]

    # 10. Retrieve Tracks and Detections
    tracks_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/tracks")
    assert tracks_res.status_code == 200

    dets_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/detections")
    assert dets_res.status_code == 200

    # 11. Retrieve Assets
    assets_res = await async_client.get(f"/api/v1/files/{file_id}/video-analysis/assets")
    assert assets_res.status_code == 200
    assert "artifacts" in assets_res.json()["data"]

    # 12. Test Exports (SRT, VTT, MD, TXT, JSON, Manifest)
    for exp_fmt in ["srt", "vtt", "md", "txt", "json", "manifest"]:
        exp_res = await async_client.get(
            f"/api/v1/files/{file_id}/video-analysis/export/{exp_fmt}"
        )
        assert exp_res.status_code == 200
        assert len(exp_res.content) > 0
