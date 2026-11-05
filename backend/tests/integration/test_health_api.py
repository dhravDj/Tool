"""Integration tests for application health, liveness, and readiness probes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_probe(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    # Health endpoint returns 200 or 503 depending on database reachability
    assert response.status_code in (200, 503)
    payload = response.json()
    assert "data" in payload
    data = payload["data"]
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "storage" in data
    assert "ai_engine" in data


@pytest.mark.asyncio
async def test_readiness_probe(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/readiness")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "ready" in data
    assert "checks" in data
