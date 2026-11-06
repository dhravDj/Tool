"""Integration tests for Spreadsheet Intelligence API endpoints."""

import io

import openpyxl
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_spreadsheet_capabilities_api(async_client: AsyncClient) -> None:
    """Test GET /api/v1/spreadsheet-intelligence/capabilities."""
    res = await async_client.get("/api/v1/spreadsheet-intelligence/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    for fmt in ["xlsx", "xls", "csv", "tsv", "ods"]:
        assert fmt in data["supported_formats"]

    assert data["formula_extraction_supported"] is True
    assert data["formula_execution_allowed"] is False
    assert data["max_rows_limit"] == 1_000_000


@pytest.mark.asyncio
async def test_spreadsheet_api_lifecycle(async_client: AsyncClient) -> None:
    """Test full spreadsheet intelligence lifecycle from upload to analysis and download."""
    # 1. Create a synthetic XLSX workbook in memory
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SalesData"
    ws["A1"] = "Region"
    ws["B1"] = "Q1_Sales"
    ws["C1"] = "Q2_Sales"
    ws["D1"] = "Total"

    ws["A2"] = "North"
    ws["B2"] = 12000
    ws["C2"] = 15000
    ws["D2"] = "=B2+C2"

    ws["A3"] = "South"
    ws["B3"] = 18000
    ws["C3"] = 22000
    ws["D3"] = "=B3+C3"

    buf = io.BytesIO()
    wb.save(buf)
    wb.close()
    buf.seek(0)

    # 2. Upload and detect file
    files = {"file": ("sales_q1_q2.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    upload_res = await async_client.post("/api/v1/files/detect?persist=true", files=files)
    assert upload_res.status_code == 200
    file_id = upload_res.json()["data"]["persisted_file_id"]
    assert file_id is not None

    # 3. Trigger spreadsheet analysis
    analyze_res = await async_client.post(f"/api/v1/files/{file_id}/analyze-spreadsheet")
    assert analyze_res.status_code == 200
    manifest = analyze_res.json()["data"]
    assert manifest["file_id"] == file_id
    assert manifest["status"] == "completed"
    assert manifest["worksheet_count"] == 1
    assert manifest["formula_count"] == 2
    assert "json" in manifest["artifacts"]
    assert "markdown" in manifest["artifacts"]

    # 4. Retrieve spreadsheet analysis overview
    overview_res = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis")
    assert overview_res.status_code == 200
    ov_data = overview_res.json()["data"]
    assert ov_data["file_id"] == file_id
    assert ov_data["format"] == "xlsx"
    assert ov_data["sheet_count"] == 1
    assert ov_data["formula_count"] == 2

    # 5. Retrieve full canonical SpreadsheetDocument JSON
    doc_res = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis/result")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()["data"]
    assert len(doc_data["worksheets"]) == 1
    assert doc_data["worksheets"][0]["name"] == "SalesData"

    # 6. Retrieve worksheets list
    sheets_res = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis/worksheets")
    assert sheets_res.status_code == 200
    sheets_list = sheets_res.json()["data"]
    assert len(sheets_list) == 1
    assert sheets_list[0]["name"] == "SalesData"

    # 7. Retrieve paginated worksheet data
    ws_data_res = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis/worksheets/sheet_1?page=1&page_size=20")
    assert ws_data_res.status_code == 200
    ws_page = ws_data_res.json()["data"]
    assert ws_page["name"] == "SalesData"
    assert len(ws_page["rows"]) == 3  # Header + 2 data rows

    # 8. Retrieve summary
    summary_res = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis/summary")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()["data"]
    assert summary_data["total_formulas"] == 2

    # 9. Download artifacts (JSON, Markdown, CSV, XLSX)
    dl_json = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis/download?format=json")
    assert dl_json.status_code == 200
    assert dl_json.headers["content-type"] == "application/json"

    dl_md = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis/download?format=markdown")
    assert dl_md.status_code == 200
    assert "text/markdown" in dl_md.headers["content-type"]

    dl_csv = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis/download?format=csv&sheet_position=1")
    assert dl_csv.status_code == 200
    assert "text/csv" in dl_csv.headers["content-type"]
    assert "Region,Q1_Sales,Q2_Sales,Total" in dl_csv.text

    dl_xlsx = await async_client.get(f"/api/v1/files/{file_id}/spreadsheet-analysis/download?format=xlsx")
    assert dl_xlsx.status_code == 200
    assert len(dl_xlsx.content) > 100
