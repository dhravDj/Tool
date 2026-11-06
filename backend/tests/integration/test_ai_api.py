"""Integration tests for Phase 11 Universal AI Intelligence API endpoints."""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_capabilities_api(async_client: AsyncClient) -> None:
    res = await async_client.get("/api/v1/ai/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["default_llm_model"] == "documind-sovereign-llm-v1"
    assert data["embedding_dimension"] == 384
    assert len(data["available_providers"]) == 3
    assert "hybrid_search" in data["features"]


@pytest.mark.asyncio
async def test_ai_providers_api(async_client: AsyncClient) -> None:
    res = await async_client.get("/api/v1/ai/providers")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    providers = body["data"]
    prov_names = [p["provider_name"] for p in providers]
    assert "sovereign" in prov_names
    assert "ollama" in prov_names
    assert "gemini" in prov_names


@pytest.mark.asyncio
async def test_ai_settings_api(async_client: AsyncClient) -> None:
    # Update settings
    put_res = await async_client.put(
        "/api/v1/ai/settings",
        json={
            "cloud_consent_given": True,
            "ollama_base_url": "http://127.0.0.1:11434",
        },
    )
    assert put_res.status_code == 200
    assert put_res.json()["data"]["status"] == "settings_updated"

    # Get settings
    get_res = await async_client.get("/api/v1/ai/settings")
    assert get_res.status_code == 200
    settings = get_res.json()["data"]
    assert settings["default_provider"] == "sovereign"
    assert settings["cloud_consent_given"] is True


@pytest.mark.asyncio
async def test_ai_chat_and_abstention(async_client: AsyncClient) -> None:
    # Chat with no indexed files for an unknown question -> expect explicit evidence abstention
    chat_res = await async_client.post(
        "/api/v1/ai/chat",
        json={
            "message": "What is the speed of light in kilometers per second?",
            "provider": "sovereign",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()["data"]
    assert "no evidence" in chat_data["message"]["content"].lower()
    assert len(chat_data["citations"]) == 0


@pytest.mark.asyncio
async def test_ai_chat_streaming(async_client: AsyncClient) -> None:
    stream_res = await async_client.post(
        "/api/v1/ai/chat/stream",
        json={"message": "Summarize architecture", "provider": "sovereign"},
    )
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers.get("content-type", "")
    content = stream_res.text
    assert "event: retrieval" in content
    assert "event: done" in content


@pytest.mark.asyncio
async def test_ai_full_lifecycle(async_client: AsyncClient) -> None:
    # 1. Upload a sample document
    sample_text = (
        "Project Orion Financial Report 2026.\n"
        "Total company revenue reached $15.5 million with a gross margin of 68%.\n"
        "Operating costs were reduced by 12% following automation initiatives.\n"
        "The project was executed between January 15, 2026 and October 30, 2026.\n"
    )
    files = {
        "file": (
            "orion_report.txt",
            io.BytesIO(sample_text.encode("utf-8")),
            "text/plain",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 2. Extract Document Content
    extract_res = await async_client.post(f"/api/v1/files/{file_id}/extract")
    assert extract_res.status_code in (200, 202)

    # 3. Index File into Knowledge Base
    index_res = await async_client.post(f"/api/v1/ai/index/{file_id}?force=true")
    if index_res.status_code != 200:
        print("INDEX RESPONSE ERROR:", index_res.status_code, index_res.text)
    assert index_res.status_code == 200
    idx_data = index_res.json()["data"]
    assert idx_data["file_id"] == file_id
    assert idx_data["total_chunks"] >= 1

    # 4. Check Index Status
    status_res = await async_client.get(f"/api/v1/ai/index/{file_id}/status")
    assert status_res.status_code == 200
    st_data = status_res.json()["data"]
    assert st_data["is_indexed"] is True
    assert st_data["chunk_count"] >= 1

    # 5. Hybrid Search
    search_res = await async_client.post(
        "/api/v1/ai/search",
        json={"query": "revenue gross margin", "search_mode": "hybrid", "top_k": 5},
    )
    assert search_res.status_code == 200
    s_data = search_res.json()["data"]
    assert s_data["total_hits"] >= 1
    assert any("15.5 million" in h["content"] for h in s_data["hits"])

    # 6. RAG Chat Query with Citation Grounding
    chat_res = await async_client.post(
        "/api/v1/ai/chat",
        json={
            "message": "What was the total company revenue and gross margin?",
            "file_ids": [file_id],
            "provider": "sovereign",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()["data"]
    answer = chat_data["message"]["content"]
    assert "15.5 million" in answer or "revenue" in answer.lower()
    assert len(chat_data["citations"]) >= 1
    cit = chat_data["citations"][0]
    assert cit["filename"] == "orion_report.txt"

    # 7. Summarize File
    summary_res = await async_client.post(
        "/api/v1/ai/summarize?refresh=true",
        json={"file_id": file_id, "summary_type": "bullet"},
    )
    assert summary_res.status_code == 200
    sum_data = summary_res.json()["data"]
    assert "orion_report.txt" in sum_data["filename"]
    assert len(sum_data["key_findings"]) >= 1

    # 8. Structured Extraction
    extract_struct_res = await async_client.post(
        "/api/v1/ai/extract-structured",
        json={"file_id": file_id, "fields": ["title", "monetary_amounts", "dates"]},
    )
    assert extract_struct_res.status_code == 200
    es_data = extract_struct_res.json()["data"]["extracted_data"]
    assert len(es_data.get("monetary_amounts", [])) >= 1

    # 9. Telemetry Usage
    telemetry_res = await async_client.get("/api/v1/ai/usage")
    assert telemetry_res.status_code == 200
    telem = telemetry_res.json()["data"]
    assert telem["total_tokens_used"] > 0
    assert telem["total_inference_calls"] > 0
