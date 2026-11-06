"""Integration tests for Code Intelligence API endpoints."""

import io
from pathlib import Path

import pytest
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "code"


@pytest.mark.asyncio
async def test_code_capabilities_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/code-intelligence/capabilities."""
    res = await async_client.get("/api/v1/code-intelligence/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    for lang in ["py", "js", "ts", "jsx", "tsx", "html", "css", "java", "c", "cpp", "go", "rs", "php", "sql"]:
        assert lang in data["supported_languages"]
    assert "symbol_extraction" in data["features"]


@pytest.mark.asyncio
async def test_code_api_lifecycle(async_client: AsyncClient) -> None:
    """Test complete code lifecycle: upload -> analyze -> overview -> result -> symbols -> deps -> diagnostics -> metrics -> source -> export."""
    fixture_path = FIXTURES_DIR / "sample_python.py"
    file_bytes = fixture_path.read_bytes()

    # 1. Upload and persist file
    files = {
        "file": (
            "sample_python.py",
            io.BytesIO(file_bytes),
            "text/x-python",
        )
    }
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 2. Trigger Code Analysis
    analyze_res = await async_client.post(f"/api/v1/files/{file_id}/analyze-code")
    assert analyze_res.status_code == 200
    manifest = analyze_res.json()["data"]
    assert manifest["file_id"] == file_id
    assert manifest["status"] == "completed"
    assert manifest["language"] == "py"
    assert manifest["symbols_count"] >= 3

    # 3. Retrieve Code Analysis Overview
    overview_res = await async_client.get(f"/api/v1/files/{file_id}/code-analysis")
    assert overview_res.status_code == 200
    overview_data = overview_res.json()["data"]
    assert overview_data["status"] == "completed"
    assert overview_data["language"] == "py"
    assert overview_data["total_lines"] > 20

    # 4. Retrieve Full Canonical CodeDocument Result
    doc_res = await async_client.get(f"/api/v1/files/{file_id}/code-analysis/result")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()["data"]
    assert len(doc_data["symbols"]) >= 3
    assert len(doc_data["imports"]) >= 3

    # 5. Retrieve Symbols
    sym_res = await async_client.get(f"/api/v1/files/{file_id}/code-analysis/symbols")
    assert sym_res.status_code == 200
    sym_list = sym_res.json()["data"]
    assert len(sym_list) >= 3
    sym_names = [s["name"] for s in sym_list]
    assert "UserAccount" in sym_names

    # 6. Retrieve Dependencies
    dep_res = await async_client.get(f"/api/v1/files/{file_id}/code-analysis/dependencies")
    assert dep_res.status_code == 200
    dep_data = dep_res.json()["data"]
    assert len(dep_data["imports"]) >= 3
    assert len(dep_data["dependencies"]) >= 1

    # 7. Retrieve Diagnostics
    diag_res = await async_client.get(f"/api/v1/files/{file_id}/code-analysis/diagnostics")
    assert diag_res.status_code == 200
    diag_list = diag_res.json()["data"]
    assert len(diag_list) >= 1
    assert any(d["rule_id"] == "SEC-HARDCODED-SECRET" for d in diag_list)

    # 8. Retrieve Metrics
    met_res = await async_client.get(f"/api/v1/files/{file_id}/code-analysis/metrics")
    assert met_res.status_code == 200
    met_data = met_res.json()["data"]
    assert met_data["total_lines"] > 20
    assert met_data["class_count"] >= 1

    # 9. Retrieve Source Code
    src_res = await async_client.get(f"/api/v1/files/{file_id}/code-analysis/source")
    assert src_res.status_code == 200
    assert "class UserAccount" in src_res.text

    # 10. Exports (JSON, Markdown, TXT)
    for exp_fmt in ["json", "markdown", "txt"]:
        exp_res = await async_client.get(f"/api/v1/files/{file_id}/code-analysis/export/{exp_fmt}")
        assert exp_res.status_code == 200
        assert len(exp_res.text) > 50
