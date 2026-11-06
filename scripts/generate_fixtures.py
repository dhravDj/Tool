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

# Save ground_truth.json
gt_path = fixtures_dir / "ground_truth.json"
gt_path.write_text(json.dumps(ground_truth, indent=2), encoding="utf-8")
print(f"Generated {len(ground_truth)} real-world fixtures in {fixtures_dir}")
