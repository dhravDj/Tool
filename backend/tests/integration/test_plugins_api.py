"""Integration tests for plugin introspection API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_plugins_api(async_client: AsyncClient):
    response = await async_client.get("/api/v1/plugins")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["total_plugins"] >= 5
    plugin_names = [p["name"] for p in data["plugins"]]
    assert "mock_text_detector" in plugin_names
    assert "mock_text_extractor" in plugin_names
    assert "mock_local_ai_provider" in plugin_names


@pytest.mark.asyncio
async def test_get_plugin_details_api(async_client: AsyncClient):
    response = await async_client.get("/api/v1/plugins/mock_text_detector")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["name"] == "mock_text_detector"
    assert payload["data"]["plugin_type"] == "detector"


@pytest.mark.asyncio
async def test_get_nonexistent_plugin_api(async_client: AsyncClient):
    response = await async_client.get("/api/v1/plugins/non_existent_engine")
    assert response.status_code == 404
