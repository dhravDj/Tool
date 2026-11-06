"""Integration tests for Audio Intelligence API endpoints."""

import io
from pathlib import Path

import pytest
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "audio"


@pytest.mark.asyncio
async def test_audio_capabilities_and_models_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/audio-intelligence/capabilities and /models."""
    res = await async_client.get("/api/v1/audio-intelligence/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    for fmt in ["aac", "flac", "m4a", "mp3", "ogg", "wav"]:
        assert fmt in data["supported_formats"]

    assert data["diarization_available"] is True
    assert data["sound_events_available"] is True

    # Test models endpoint
    res_models = await async_client.get("/api/v1/audio-intelligence/models")
    assert res_models.status_code == 200
    body_models = res_models.json()
    assert "supported_models" in body_models["data"]


@pytest.mark.asyncio
async def test_audio_api_lifecycle(async_client: AsyncClient) -> None:
    """Test complete audio lifecycle: upload -> analyze -> transcript -> segments -> export."""
    fixture_path = FIXTURES_DIR / "speech_english.wav"
    assert fixture_path.exists(), "speech_english.wav fixture must exist"

    file_bytes = fixture_path.read_bytes()

    # 1. Upload and persist file
    files = {
        "file": (
            "test_meeting.wav",
            io.BytesIO(file_bytes),
            "audio/wav",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 2. Trigger Audio Analysis
    analyze_res = await async_client.post(f"/api/v1/files/{file_id}/analyze-audio")
    assert analyze_res.status_code == 200
    manifest = analyze_res.json()["data"]
    assert manifest["file_id"] == file_id
    assert manifest["status"] == "completed"
    assert manifest["segment_count"] >= 1

    # 3. Retrieve Audio Analysis Overview
    overview_res = await async_client.get(f"/api/v1/files/{file_id}/audio-analysis")
    assert overview_res.status_code == 200
    overview_data = overview_res.json()["data"]
    assert overview_data["status"] == "completed"
    assert overview_data["duration_seconds"] > 2.0

    # 4. Retrieve Full Canonical AudioDocument
    doc_res = await async_client.get(f"/api/v1/files/{file_id}/audio-analysis/result")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()["data"]
    assert len(doc_data["segments"]) >= 1

    # 5. Retrieve Transcript
    tr_res = await async_client.get(f"/api/v1/files/{file_id}/audio-analysis/transcript")
    assert tr_res.status_code == 200
    tr_data = tr_res.json()["data"]
    assert "DocuMind" in tr_data["transcript"]

    # 6. Retrieve Segments with Search
    seg_res = await async_client.get(
        f"/api/v1/files/{file_id}/audio-analysis/segments?q=DocuMind"
    )
    assert seg_res.status_code == 200
    seg_data = seg_res.json()["data"]
    assert len(seg_data) >= 1

    # 7. Retrieve Speakers
    spk_res = await async_client.get(f"/api/v1/files/{file_id}/audio-analysis/speakers")
    assert spk_res.status_code == 200
    spk_data = spk_res.json()["data"]
    assert len(spk_data) >= 1

    # 8. Retrieve Events
    evt_res = await async_client.get(f"/api/v1/files/{file_id}/audio-analysis/events")
    assert evt_res.status_code == 200

    # 9. Test Exports (SRT, VTT, MD)
    for exp_fmt in ["srt", "vtt", "md", "txt", "json"]:
        exp_res = await async_client.get(
            f"/api/v1/files/{file_id}/audio-analysis/export/{exp_fmt}"
        )
        assert exp_res.status_code == 200
        assert len(exp_res.content) > 0
