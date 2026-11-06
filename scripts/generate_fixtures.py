"""Generate realistic multi-format test fixtures with ground truth for DocuMind AI validation."""

import json
from pathlib import Path
from PIL import Image, ImageDraw
import pymupdf
import docx

fixtures_dir = Path("backend/tests/fixtures/real_world_dataset")
fixtures_dir.mkdir(parents=True, exist_ok=True)

ground_truth = {}

# 1. invoice.pdf
pdf_path = fixtures_dir / "invoice.pdf"
doc = pymupdf.open()
page = doc.new_page(width=595, height=842)  # A4

page.insert_text((50, 60), "ACME INVOICE #INV-2026-001", fontsize=18, fontname="helv")
page.insert_text((50, 100), "Client: Globex Corporation", fontsize=12, fontname="helv")
page.insert_text((50, 120), "Date: November 6, 2026", fontsize=12, fontname="helv")
page.insert_text((50, 160), "Description: Enterprise Cloud Storage and AI Computing Services", fontsize=11, fontname="helv")

# Table-like layout
page.insert_text((50, 220), "| Item | Qty | Unit Price | Total |", fontsize=10, fontname="courier")
page.insert_text((50, 240), "| Server Rack | 2 | $2,500.00 | $5,000.00 |", fontsize=10, fontname="courier")
page.insert_text((50, 260), "| Support Retainer | 1 | $1,200.00 | $1,200.00 |", fontsize=10, fontname="courier")
page.insert_text((50, 300), "Total Balance Due: $6,200.00", fontsize=14, fontname="helv")

doc.save(str(pdf_path))
doc.close()

ground_truth["invoice.pdf"] = {
    "format_id": "pdf",
    "category": "pdf",
    "mime_type": "application/pdf",
    "is_valid": True,
    "is_mismatch": False,
    "is_corrupted": False,
    "is_suspicious": False,
    "expected_text": ["ACME INVOICE", "Globex Corporation", "Server Rack", "$6,200.00"],
}

# 2. memo.docx
docx_path = fixtures_dir / "memo.docx"
doc_docx = docx.Document()
doc_docx.add_heading("Internal Project Update", level=1)
doc_docx.add_paragraph("Team, here is the weekly engineering progress report.")
p_list = doc_docx.add_paragraph("Key Accomplishments:")
doc_docx.add_paragraph("Completed database optimization and connection pooling.", style="List Bullet")
doc_docx.add_paragraph("Hardened universal file detection heuristics.", style="List Bullet")
doc_docx.add_paragraph("Benchmarked OCR and vision performance on local hardware.", style="List Bullet")
doc_docx.save(str(docx_path))

ground_truth["memo.docx"] = {
    "format_id": "docx",
    "category": "document",
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "is_valid": True,
    "is_mismatch": False,
    "is_corrupted": False,
    "is_suspicious": False,
    "expected_text": ["Internal Project Update", "weekly engineering progress", "database optimization"],
}

# 3. notes.txt
txt_path = fixtures_dir / "notes.txt"
txt_path.write_text(
    "DocuMind AI Architecture Notes\n\n"
    "1. Microservice boundary definition\n"
    "2. Sovereign local processing\n"
    "3. Hardware governor with bounded workers\n",
    encoding="utf-8",
)

ground_truth["notes.txt"] = {
    "format_id": "txt",
    "category": "document",
    "mime_type": "text/plain",
    "is_valid": True,
    "is_mismatch": False,
    "is_corrupted": False,
    "is_suspicious": False,
    "expected_text": ["DocuMind AI Architecture Notes", "Sovereign local processing"],
}

# 4. documentation.md
md_path = fixtures_dir / "documentation.md"
md_path.write_text(
    "# API Specification\n\n"
    "Universal file detection endpoint:\n\n"
    "POST /api/v1/files/detect\n\n"
    "| Parameter | Type | Required |\n"
    "|---|---|---|\n"
    "| file | binary | yes |\n"
    "| persist | boolean | no |\n",
    encoding="utf-8",
)

ground_truth["documentation.md"] = {
    "format_id": "md",
    "category": "document",
    "mime_type": "text/markdown",
    "is_valid": True,
    "is_mismatch": False,
    "is_corrupted": False,
    "is_suspicious": False,
    "expected_text": ["API Specification", "POST /api/v1/files/detect"],
}

# 5. chart.png
chart_path = fixtures_dir / "chart.png"
img_chart = Image.new("RGB", (600, 400), color=(255, 255, 255))
draw = ImageDraw.Draw(img_chart)
draw.text((200, 30), "Q4 Revenue Growth Chart", fill=(0, 0, 0))
draw.line([(50, 350), (550, 350)], fill=(100, 100, 100), width=2)
draw.line([(50, 350), (50, 50)], fill=(100, 100, 100), width=2)
# Draw bars
draw.rectangle([(100, 200), (160, 350)], fill=(41, 128, 185))
draw.rectangle([(220, 150), (280, 350)], fill=(39, 174, 96))
draw.rectangle([(340, 100), (400, 350)], fill=(230, 126, 34))
draw.rectangle([(460, 80), (520, 350)], fill=(142, 68, 173))
img_chart.save(str(chart_path))

ground_truth["chart.png"] = {
    "format_id": "png",
    "category": "image",
    "mime_type": "image/png",
    "is_valid": True,
    "is_mismatch": False,
    "is_corrupted": False,
    "is_suspicious": False,
    "expected_objects": ["visual_graphic"],
}

# 6. scan.jpeg
scan_path = fixtures_dir / "scan.jpeg"
img_scan = Image.new("RGB", (500, 500), color=(248, 248, 245))
draw_scan = ImageDraw.Draw(img_scan)
draw_scan.text((60, 80), "CONFIDENTIAL MEMORANDUM", fill=(20, 20, 20))
draw_scan.text((60, 120), "Subject: System Deployment Protocol", fill=(30, 30, 30))
draw_scan.text((60, 160), "All nodes must pass local verification.", fill=(30, 30, 30))
img_scan.save(str(scan_path), quality=90)

ground_truth["scan.jpeg"] = {
    "format_id": "jpeg",
    "category": "image",
    "mime_type": "image/jpeg",
    "is_valid": True,
    "is_mismatch": False,
    "is_corrupted": False,
    "is_suspicious": False,
}

# 7. malicious_disguise.exe.pdf (ELF disguised as PDF)
mal_path = fixtures_dir / "malicious_disguise.exe.pdf"
mal_bytes = b"\x7fELF\x02\x01\x01\x00" + bytes(48)
mal_path.write_bytes(mal_bytes)

ground_truth["malicious_disguise.exe.pdf"] = {
    "format_id": "elf",
    "category": "executable",
    "is_valid": True,
    "is_mismatch": True,
    "is_corrupted": False,
    "is_suspicious": True,
}

# 8. corrupted_sample.webp
corrupt_path = fixtures_dir / "corrupted_sample.webp"
corrupt_path.write_bytes(b"RIFF\x20\x00\x00\x00BADF")

ground_truth["corrupted_sample.webp"] = {
    "format_id": "webp",
    "category": "image",
    "is_valid": True,
    "is_mismatch": False,
    "is_corrupted": True,
    "is_suspicious": False,
}

# 9. sales.xlsx (Multi-sheet, formulas, styling, merged cells, hidden sheet)
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

wb_sales = openpyxl.Workbook()
ws_q1 = wb_sales.active
ws_q1.title = "Q1_Sales"

# Merged title
ws_q1.merge_cells("A1:F1")
ws_q1["A1"] = "Q1 Regional Sales Performance Report"
ws_q1["A1"].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
ws_q1["A1"].alignment = Alignment(horizontal="center", vertical="center")

headers = ["Transaction_ID", "Product", "Units", "Unit_Price", "Revenue", "Region"]
for col_idx, h in enumerate(headers, start=1):
    c = ws_q1.cell(row=2, column=col_idx, value=h)
    c.font = Font(bold=True)
    c.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

rows_data = [
    ("TXN-101", "Enterprise Server", 5, 1200.0, "=C3*D3", "North"),
    ("TXN-102", "Storage Array", 2, 4500.0, "=C4*D4", "South"),
    ("TXN-103", "Network Switch", 10, 350.0, "=C5*D5", "East"),
    ("TXN-104", "Security Appliance", 4, 2100.0, "=C6*D6", "West"),
    ("TXN-105", "Cloud Gateway", 8, 800.0, "=C7*D7", "North"),
]

for r_offset, r_data in enumerate(rows_data, start=3):
    for c_offset, val in enumerate(r_data, start=1):
        ws_q1.cell(row=r_offset, column=c_offset, value=val)

# Summary row
ws_q1.cell(row=8, column=1, value="Total Revenue")
ws_q1.cell(row=8, column=5, value="=SUM(E3:E7)")

# Sheet 2: Targets
ws_targets = wb_sales.create_sheet(title="Targets")
ws_targets.append(["Quarter", "Revenue_Target", "Actual_Revenue", "Status"])
ws_targets.append(["Q1", 40000.0, "=Q1_Sales!E8", "=IF(C2>=B2, \"MET\", \"PENDING\")"])

# Sheet 3: Hidden Audit
ws_audit = wb_sales.create_sheet(title="Audit_Notes")
ws_audit.sheet_state = "hidden"
ws_audit.append(["Audit_ID", "Reviewer", "Flagged_Transactions"])
ws_audit.append(["AUD-001", "SecOps Team", "=COUNTIF(Q1_Sales!F3:F7, \"North\")"])

sales_path = fixtures_dir / "sales.xlsx"
wb_sales.save(str(sales_path))

ground_truth["sales.xlsx"] = {
    "format_id": "xlsx",
    "category": "spreadsheet",
    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "is_valid": True,
    "sheet_count": 3,
    "has_formulas": True,
    "has_hidden_sheets": True,
    "expected_formulas": ["=C3*D3", "=SUM(E3:E7)", "=Q1_Sales!E8", "=IF(C2>=B2, \"MET\", \"PENDING\")"],
}

# 10. legacy.xls (Legacy Excel 97-2003 BIFF8)
import xlwt

wb_legacy = xlwt.Workbook(encoding="utf-8")
ws_legacy = wb_legacy.add_sheet("Inventory")
ws_legacy.write(0, 0, "SKU")
ws_legacy.write(0, 1, "Item_Name")
ws_legacy.write(0, 2, "Stock_Qty")
ws_legacy.write(0, 3, "Unit_Cost")

items = [
    ("SKU-9001", "Flash Drive 64GB", 120, 8.50),
    ("SKU-9002", "External SSD 1TB", 45, 75.00),
    ("SKU-9003", "USB-C Docking Hub", 30, 42.00),
]
for r_idx, item in enumerate(items, start=1):
    for c_idx, val in enumerate(item):
        ws_legacy.write(r_idx, c_idx, val)

legacy_path = fixtures_dir / "legacy.xls"
wb_legacy.save(str(legacy_path))

ground_truth["legacy.xls"] = {
    "format_id": "xls",
    "category": "spreadsheet",
    "mime_type": "application/vnd.ms-excel",
    "is_valid": True,
    "sheet_count": 1,
}

# 11. metrics.csv (Comma-delimited with formulas and injection attempt)
csv_path = fixtures_dir / "metrics.csv"
csv_content = """metric_id,component,latency_ms,error_rate,status,formula_note
MET-001,detector,1.45,0.001,healthy,=1+2
MET-002,ocr_engine,42.80,0.004,healthy,=SUM(10,20)
MET-003,vision_align,18.10,0.000,healthy,@SUM(1,2)
MET-004,storage_s3,5.20,0.002,warning,+CMD|'/C calc'!A0
MET-005,task_queue,0.85,0.000,healthy,-HYPERLINK("http://malicious.test")
"""
csv_path.write_text(csv_content, encoding="utf-8")

ground_truth["metrics.csv"] = {
    "format_id": "csv",
    "category": "spreadsheet",
    "mime_type": "text/csv",
    "is_valid": True,
    "row_count": 5,
    "delimiter": ",",
    "has_injection_risk": True,
}

# 12. report.ods (OpenDocument Spreadsheet XML container)
import io
import zipfile

ods_content_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  office:version="1.3">
  <office:body>
    <office:spreadsheet>
      <table:table table:name="Operational_Kpis">
        <table:table-row>
          <table:table-cell office:value-type="string"><text:p>Department</text:p></table:table-cell>
          <table:table-cell office:value-type="string"><text:p>Uptime_Percent</text:p></table:table-cell>
          <table:table-cell office:value-type="string"><text:p>Incidents</text:p></table:table-cell>
        </table:table-row>
        <table:table-row>
          <table:table-cell office:value-type="string"><text:p>Infrastructure</text:p></table:table-cell>
          <table:table-cell office:value-type="float" office:value="99.98"><text:p>99.98</text:p></table:table-cell>
          <table:table-cell office:value-type="float" office:value="2"><text:p>2</text:p></table:table-cell>
        </table:table-row>
        <table:table-row>
          <table:table-cell office:value-type="string"><text:p>Application</text:p></table:table-cell>
          <table:table-cell office:value-type="float" office:value="99.95"><text:p>99.95</text:p></table:table-cell>
          <table:table-cell office:value-type="float" office:value="4"><text:p>4</text:p></table:table-cell>
        </table:table-row>
        <table:table-row>
          <table:table-cell office:value-type="string"><text:p>Security</text:p></table:table-cell>
          <table:table-cell office:value-type="float" office:value="100.0"><text:p>100.0</text:p></table:table-cell>
          <table:table-cell office:value-type="float" office:value="0"><text:p>0</text:p></table:table-cell>
        </table:table-row>
      </table:table>
    </office:spreadsheet>
  </office:body>
</office:document-content>"""

ods_path = fixtures_dir / "report.ods"
with zipfile.ZipFile(ods_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet")
    zf.writestr("content.xml", ods_content_xml)

ground_truth["report.ods"] = {
    "format_id": "ods",
    "category": "spreadsheet",
    "mime_type": "application/vnd.oasis.opendocument.spreadsheet",
    "is_valid": True,
    "sheet_count": 1,
}

# Save ground_truth.json
gt_path = fixtures_dir / "ground_truth.json"
gt_path.write_text(json.dumps(ground_truth, indent=2), encoding="utf-8")
print(f"Generated {len(ground_truth)} real-world fixtures in {fixtures_dir}")
