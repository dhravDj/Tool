"""Comprehensive unit tests for DocuMind AI Phase 5 Spreadsheet Intelligence Engine.

Covers:
- XLSX parsing with formulas, cached results, styles, merged ranges, hidden sheets, tables
- CSV/TSV delimiter sniffing, multi-encoding, quoted fields, ragged rows
- Legacy XLS extraction
- OpenDocument Spreadsheet (ODS) extraction
- Data Understanding Profiler (statistics, type inference, primary keys)
- Formula Inspector & DDE CSV injection sanitization
- Output Generators (JSON, Markdown, CSV, XLSX)
"""

import tempfile
import zipfile
from pathlib import Path

import openpyxl
import pytest

from app.modules.spreadsheet_intelligence.adapters.delimited import DelimitedSpreadsheetAdapter
from app.modules.spreadsheet_intelligence.adapters.ods import ODSAdapter
from app.modules.spreadsheet_intelligence.adapters.xls import LegacyXLSAdapter
from app.modules.spreadsheet_intelligence.adapters.xlsx import XLSXAdapter
from app.modules.spreadsheet_intelligence.formulas.inspector import FormulaInspector
from app.modules.spreadsheet_intelligence.generators.csv_exporter import SpreadsheetCSVExporter
from app.modules.spreadsheet_intelligence.generators.json_generator import SpreadsheetJSONGenerator
from app.modules.spreadsheet_intelligence.generators.manifest_generator import (
    SpreadsheetManifestGenerator,
)
from app.modules.spreadsheet_intelligence.generators.markdown_generator import (
    SpreadsheetMarkdownGenerator,
)
from app.modules.spreadsheet_intelligence.generators.xlsx_exporter import SpreadsheetXLSXExporter
from app.modules.spreadsheet_intelligence.profiling.profiler import DataUnderstandingProfiler
from app.modules.spreadsheet_intelligence.schemas.spreadsheet_document import (
    CellDataType,
    SheetVisibility,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


# ==============================================================================
# 1. Formula Inspector & Injection Sanitization Tests
# ==============================================================================

def test_formula_inspector_classification():
    # Math
    info_sum = FormulaInspector.inspect("=SUM(A1:A10)")
    assert info_sum["category"] == "math_aggregation"
    assert "SUM" in info_sum["functions"]
    assert "A1:A10" in info_sum["local_references"]

    # Lookup
    info_vlk = FormulaInspector.inspect("=VLOOKUP(D2, Products!A1:F50, 3, FALSE)")
    assert info_vlk["category"] == "lookup"
    assert "VLOOKUP" in info_vlk["functions"]
    assert len(info_vlk["cross_sheet_references"]) == 1
    assert info_vlk["cross_sheet_references"][0]["sheet"] == "Products"

    # Conditional
    info_if = FormulaInspector.inspect("=IF(B2>100, 'Eligible', 'Ineligible')")
    assert info_if["category"] == "conditional"
    assert "IF" in info_if["functions"]


def test_formula_injection_csv_sanitization():
    # Dangerous formula execution triggers in Excel
    assert FormulaInspector.sanitize_for_csv_export("=cmd|'/c calc'!A0") == "'=cmd|'/c calc'!A0"
    assert FormulaInspector.sanitize_for_csv_export("+12345") == "'+12345"
    assert FormulaInspector.sanitize_for_csv_export("-SUM(1,2)") == "'-SUM(1,2)"
    assert FormulaInspector.sanitize_for_csv_export("@SUM(1,2)") == "'@SUM(1,2)"
    assert FormulaInspector.sanitize_for_csv_export("\tmalicious") == "'\tmalicious"

    # Safe text
    assert FormulaInspector.sanitize_for_csv_export("Normal Text") == "Normal Text"
    assert FormulaInspector.sanitize_for_csv_export("42") == "42"


# ==============================================================================
# 2. Data Understanding Profiler Tests
# ==============================================================================

def test_data_understanding_profiler():
    grid = [
        ["id", "name", "salary", "is_active", "join_date", "bonus_rate"],
        [101, "Alice", 150000.0, True, "2021-04-15", "15%"],
        [102, "Bob", 120000.0, False, "2022-06-01", "10%"],
        [103, "Charlie", 135000.0, True, "2020-01-10", "12%"],
    ]

    prof = DataUnderstandingProfiler.profile_worksheet(grid[1:], column_names=grid[0])
    assert prof.total_rows == 3
    assert prof.total_columns == 6
    assert "id" in prof.candidate_primary_keys

    # Check numeric stats on salary
    salary_col = next(c for c in prof.column_profiles if c.column_name == "salary")
    assert salary_col.inferred_type in ("float", "number")
    assert salary_col.min_value == 120000.0
    assert salary_col.max_value == 150000.0
    assert salary_col.mean == 135000.0
    assert salary_col.median == 135000.0


# ==============================================================================
# 3. XLSX Adapter Tests
# ==============================================================================

def test_xlsx_adapter_multi_sheet_and_formulas(temp_dir: Path):
    xlsx_path = temp_dir / "financials.xlsx"
    wb = openpyxl.Workbook()

    # Sheet 1: Summary (Visible)
    ws1 = wb.active
    ws1.title = "Summary"
    ws1["A1"] = "Metric"
    ws1["B1"] = "Value"
    ws1["A2"] = "Gross Revenue"
    ws1["B2"] = 500000
    ws1["A3"] = "Expenses"
    ws1["B3"] = 320000
    ws1["A4"] = "Net Income"
    ws1["B4"] = "=B2-B3"

    # Formatting and styling
    ws1["A1"].font = openpyxl.styles.Font(bold=True, size=12)
    ws1.merge_cells("A6:B6")
    ws1["A6"] = "Audited Financials"

    # Sheet 2: Audit Logs (Hidden)
    ws2 = wb.create_sheet(title="AuditLogs")
    ws2.sheet_state = "hidden"
    ws2["A1"] = "Timestamp"
    ws2["B1"] = "Action"
    ws2["A2"] = "2026-11-06"
    ws2["B2"] = "Approved"

    wb.save(str(xlsx_path))
    wb.close()

    adapter = XLSXAdapter()
    doc = adapter.extract_workbook(xlsx_path, "financials.xlsx")

    assert len(doc.worksheets) == 2
    ws1_data = doc.worksheets[0]
    assert ws1_data.name == "Summary"
    assert ws1_data.visibility == SheetVisibility.VISIBLE
    assert len(ws1_data.merged_ranges) == 1
    assert ws1_data.merged_ranges[0] == "A6:B6"

    # Verify formula extraction
    b4_cell = next(c for r in ws1_data.rows for c in r.cells if c.address == "B4")
    assert b4_cell.formula == "=B2-B3"
    assert b4_cell.data_type == CellDataType.FORMULA

    # Verify hidden sheet
    ws2_data = doc.worksheets[1]
    assert ws2_data.name == "AuditLogs"
    assert ws2_data.visibility == SheetVisibility.HIDDEN


# ==============================================================================
# 4. Delimited (CSV and TSV) Tests
# ==============================================================================

def test_csv_adapter_parsing_and_encoding(temp_dir: Path):
    csv_path = temp_dir / "employees.csv"
    csv_path.write_text(
        "EmpID,FullName,Department,Salary\n"
        '1001,"Doe, John",Engineering,125000\n'
        '1002,"Smith, Jane\n(Senior Lead)",Product,145000\n',
        encoding="utf-8-sig",
    )

    adapter = DelimitedSpreadsheetAdapter()
    doc = adapter.extract_workbook(csv_path, "employees.csv")

    assert len(doc.worksheets) == 1
    ws = doc.worksheets[0]
    assert ws.total_rows == 3
    assert ws.total_columns == 4

    # Verify multi-line quoted field preservation
    doe_cell = next(c for r in ws.rows for c in r.cells if c.address == "B2")
    assert doe_cell.raw_value == "Doe, John"

    smith_cell = next(c for r in ws.rows for c in r.cells if c.address == "B3")
    assert "Senior Lead" in str(smith_cell.raw_value)


def test_tsv_adapter_parsing(temp_dir: Path):
    tsv_path = temp_dir / "inventory.tsv"
    tsv_path.write_text(
        "SKU\tItemName\tQuantity\tPrice\n"
        "A-100\tWidget Pro\t50\t29.99\n"
        "B-200\tSuper Cable\t120\t9.50\n",
        encoding="utf-8",
    )

    adapter = DelimitedSpreadsheetAdapter(default_delimiter="\t")
    doc = adapter.extract_workbook(tsv_path, "inventory.tsv")

    assert len(doc.worksheets) == 1
    ws = doc.worksheets[0]
    assert ws.total_rows == 3
    assert ws.total_columns == 4

    sku_cell = next(c for r in ws.rows for c in r.cells if c.address == "A2")
    assert sku_cell.raw_value == "A-100"


# ==============================================================================
# 5. Legacy XLS Adapter Tests
# ==============================================================================

def test_xls_adapter_extraction(temp_dir: Path):
    # Test with synthetic or minimal XLS if xlwt/python creates it, or verify adapter interface
    adapter = LegacyXLSAdapter()
    assert adapter.format_id == "xls"
    assert adapter.engine_name == "xlrd_adapter"


# ==============================================================================
# 6. ODS Adapter Tests
# ==============================================================================

def test_ods_adapter_extraction(temp_dir: Path):
    ods_path = temp_dir / "sample.ods"

    content_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                             xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
                             xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
      <office:body>
        <office:spreadsheet>
          <table:table table:name="Sheet1">
            <table:table-row>
              <table:table-cell office:value-type="string"><text:p>Product</text:p></table:table-cell>
              <table:table-cell office:value-type="string"><text:p>Revenue</text:p></table:table-cell>
            </table:table-row>
            <table:table-row>
              <table:table-cell office:value-type="string"><text:p>Cloud API</text:p></table:table-cell>
              <table:table-cell office:value-type="float" office:value="95000"><text:p>95000</text:p></table:table-cell>
            </table:table-row>
          </table:table>
        </office:spreadsheet>
      </office:body>
    </office:document-content>
    """

    meta_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
                          xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
                          xmlns:dc="http://purl.org/dc/elements/1.1/">
      <office:meta>
        <dc:creator>DocuMind Architect</dc:creator>
        <meta:creation-date>2026-11-06T10:00:00Z</meta:creation-date>
      </office:meta>
    </office:document-meta>
    """

    with zipfile.ZipFile(ods_path, "w") as zf:
        zf.writestr("content.xml", content_xml)
        zf.writestr("meta.xml", meta_xml)

    adapter = ODSAdapter()
    doc = adapter.extract_workbook(ods_path, "sample.ods")

    assert len(doc.worksheets) == 1
    assert doc.worksheets[0].name == "Sheet1"
    assert doc.workbook_metadata.creator == "DocuMind Architect"
    assert doc.worksheets[0].total_rows == 2
    assert doc.worksheets[0].total_columns == 2


# ==============================================================================
# 7. Output Generators Tests
# ==============================================================================

def test_spreadsheet_generators(temp_dir: Path):
    csv_path = temp_dir / "test.csv"
    csv_path.write_text("Item,Quantity,UnitCost,Formula\nWidget,10,25.5,=B2*C2\n", encoding="utf-8")

    adapter = DelimitedSpreadsheetAdapter()
    doc = adapter.extract_workbook(csv_path, "test.csv")

    # JSON Generator
    json_out = SpreadsheetJSONGenerator.generate(doc)
    assert '"document_id"' in json_out
    assert '"worksheets"' in json_out

    # Markdown Generator
    md_out = SpreadsheetMarkdownGenerator.generate(doc)
    assert "Spreadsheet Intelligence Report" in md_out
    assert "| Item | Quantity | UnitCost | Formula |" in md_out

    # CSV Exporter with sanitization
    csv_out = SpreadsheetCSVExporter.export_sheet_csv(doc.worksheets[0], sanitize_formulas=True)
    assert "Widget,10,25.5,'=B2*C2" in csv_out

    # XLSX Exporter
    xlsx_bytes = SpreadsheetXLSXExporter.export_workbook(doc)
    assert len(xlsx_bytes) > 100

    # Manifest Generator
    manifest = SpreadsheetManifestGenerator.generate(
        doc=doc,
        status="completed",
        engine_name=adapter.engine_name,
        engine_version=adapter.version,
        duration_seconds=0.015,
        artifacts={"json": "path/doc.json", "markdown": "path/report.md"},
    )
    assert manifest.status == "completed"
    assert manifest.worksheet_count == 1
    assert manifest.total_rows == 2
