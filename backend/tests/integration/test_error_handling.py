"""Integration tests for exception handling, request IDs, and security error responses."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_id_header_injected(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/liveness")
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_custom_request_id_propagated(async_client: AsyncClient):
    custom_id = "test-correlation-id-12345"
    response = await async_client.get(
        "/api/v1/health/liveness",
        headers={"X-Request-ID": custom_id},
    )
    assert response.headers.get("X-Request-ID") == custom_id


@pytest.mark.asyncio
async def test_not_found_structured_error(async_client: AsyncClient):
    response = await async_client.get("/api/v1/files/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "RESOURCE_NOT_FOUND" or "detail" in payload
