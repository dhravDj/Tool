"""Fixture generation script for Presentation Intelligence test suite."""

import io
import struct
import zipfile
from pathlib import Path

import xlwt.CompoundDoc
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches


def generate_fixtures(output_dir: Path) -> dict[str, Path]:
    """Generate comprehensive presentation fixtures across PPTX, PPT, and ODP."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, Path] = {}

    # 1. Basic Text PPTX
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "DocuMind AI Architecture Overview"
    slide.placeholders[1].text = "Introduction to Universal File Intelligence"

    slide2 = prs.slides.add_slide(prs.slide_layouts[1])
    slide2.shapes.title.text = "Core Design Principles"
    tf = slide2.placeholders[1].text_frame
    tf.text = "Modular Monolith Architecture"
    p2 = tf.add_paragraph()
    p2.text = "API-First and Asynchronous Processing"

    p_basic = output_dir / "pptx_basic_text.pptx"
    prs.save(str(p_basic))
    generated["pptx_basic_text"] = p_basic

    # 2. Nested Bullets PPTX
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Taxonomy and Hierarchical Bullets"
    tf = slide.placeholders[1].text_frame
    tf.text = "Top Level Category: Documents"
    tf.paragraphs[0].level = 0

    p_l1 = tf.add_paragraph()
    p_l1.text = "Subcategory Level 1: Word Processing"
    p_l1.level = 1

    p_l2 = tf.add_paragraph()
    p_l2.text = "Subcategory Level 2: DOCX and ODT formats"
    p_l2.level = 2

    p_l1_b = tf.add_paragraph()
    p_l1_b.text = "Subcategory Level 1: Presentations"
    p_l1_b.level = 1

    p_nested = output_dir / "pptx_nested_bullets.pptx"
    prs.save(str(p_nested))
    generated["pptx_nested_bullets"] = p_nested

    # 3. Tables PPTX
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title only
    slide.shapes.title.text = "Quarterly Revenue Summary"

    rows, cols = 4, 3
    table_shape = slide.shapes.add_table(rows, cols, Inches(1), Inches(2), Inches(8), Inches(3))
    tbl = table_shape.table

    tbl.cell(0, 0).text = "Quarter"
    tbl.cell(0, 1).text = "Revenue ($M)"
    tbl.cell(0, 2).text = "Growth"

    data = [
        ("Q1 2026", "12.4", "+15%"),
        ("Q2 2026", "15.8", "+27%"),
        ("Q3 2026", "18.2", "+15%"),
    ]
    for r_idx, row_vals in enumerate(data, start=1):
        for c_idx, val in enumerate(row_vals):
            tbl.cell(r_idx, c_idx).text = val

    p_tables = output_dir / "pptx_tables.pptx"
    prs.save(str(p_tables))
    generated["pptx_tables"] = p_tables

    # 4. Native Charts PPTX
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Regional Market Share"

    chart_data = CategoryChartData()
    chart_data.categories = ["North America", "Europe", "Asia-Pacific", "Latin America"]
    chart_data.add_series("2025", (40.5, 30.2, 22.1, 7.2))
    chart_data.add_series("2026", (44.0, 32.5, 26.8, 8.5))

    slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(1),
        Inches(2),
        Inches(8),
        Inches(4.5),
        chart_data,
    )

    p_charts = output_dir / "pptx_native_charts.pptx"
    prs.save(str(p_charts))
    generated["pptx_native_charts"] = p_charts

    # 5. Embedded Images PPTX
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Product Visual Assets"

    # Create dummy PNG image in memory
    img = Image.new("RGB", (300, 200), color=(50, 120, 220))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    temp_img_path = output_dir / "_temp_fixture_image.png"
    with open(temp_img_path, "wb") as f:
        f.write(img_byte_arr.getvalue())

    slide.shapes.add_picture(
        str(temp_img_path),
        Inches(1.5),
        Inches(2.5),
        width=Inches(4),
        height=Inches(2.6),
    )
    if temp_img_path.exists():
        temp_img_path.unlink()

    p_images = output_dir / "pptx_images.pptx"
    prs.save(str(p_images))
    generated["pptx_images"] = p_images

    # 6. Speaker Notes PPTX
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Confidential Strategy Briefing"
    slide.placeholders[1].text = "Public facing slide content here."

    notes_slide = slide.notes_slide
    notes_tf = notes_slide.notes_text_frame
    notes_tf.text = "Internal speaker notes: Do not share specific margins before CFO sign-off."

    p_notes = output_dir / "pptx_speaker_notes.pptx"
    prs.save(str(p_notes))
    generated["pptx_speaker_notes"] = p_notes

    # 7. Grouped Shapes PPTX
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Process Flow Architecture"

    # Add shapes
    s1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(2), Inches(2), Inches(1))
    s1.text = "Ingestion Engine"
    s2 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4), Inches(2), Inches(2), Inches(1))
    s2.text = "Intelligence Pipeline"

    # Add connector shape
    connector = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(3.1), Inches(2.3), Inches(0.8), Inches(0.4))
    connector.name = "Flow Arrow"

    p_grouped = output_dir / "pptx_grouped_shapes.pptx"
    prs.save(str(p_grouped))
    generated["pptx_grouped_shapes"] = p_grouped

    # 8. Hidden Slides PPTX
    prs = Presentation()
    slide1 = prs.slides.add_slide(prs.slide_layouts[0])
    slide1.shapes.title.text = "Active Slide 1"

    slide2 = prs.slides.add_slide(prs.slide_layouts[0])
    slide2.shapes.title.text = "Backup Slide (Hidden)"
    # Set show="0" attribute on slide element to hide
    slide2.element.set("show", "0")

    slide3 = prs.slides.add_slide(prs.slide_layouts[0])
    slide3.shapes.title.text = "Active Slide 3"

    p_hidden = output_dir / "pptx_hidden_slides.pptx"
    prs.save(str(p_hidden))
    generated["pptx_hidden_slides"] = p_hidden

    # 9. Unicode & Hindi Text PPTX
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "बहुभाषी प्रस्तुति — Multilingual Intelligence"
    tf = slide.placeholders[1].text_frame
    tf.text = "नमस्ते दुनिया — DocuMind AI में आपका स्वागत है।"
    p_hindi = tf.add_paragraph()
    p_hindi.text = "विशेषताएँ: उच्च सटीकता और स्वचालित पहचान।"

    p_unicode = output_dir / "pptx_unicode_hindi.pptx"
    prs.save(str(p_unicode))
    generated["pptx_unicode_hindi"] = p_unicode

    # 10. ODP Presentation with Text & Tables
    odp_path = output_dir / "odp_text_tables.odp"
    with zipfile.ZipFile(odp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.presentation")
        zf.writestr(
            "meta.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0">
  <office:meta>
    <dc:title>OpenDocument Strategy</dc:title>
    <dc:creator>DocuMind Team</dc:creator>
    <dc:date>2026-11-06T12:00:00</dc:date>
  </office:meta>
</office:document-meta>""",
        )
        zf.writestr(
            "content.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0">
  <office:body>
    <office:presentation>
      <draw:page draw:name="Slide 1">
        <draw:frame svg:x="1in" svg:y="1in" svg:width="8in" svg:height="1.2in" presentation:class="title">
          <draw:text-box>
            <text:p>OpenDocument Presentation Header</text:p>
          </draw:text-box>
        </draw:frame>
        <draw:frame svg:x="1in" svg:y="2.5in" svg:width="8in" svg:height="2.5in">
          <draw:text-box>
            <text:p>ODP Key Deliverables</text:p>
            <text:list>
              <text:list-item><text:p>Native ODP extraction without external binaries</text:p></text:list-item>
              <text:list-item><text:p>Preservation of tables and speaker notes</text:p></text:list-item>
            </text:list>
          </draw:text-box>
        </draw:frame>
        <draw:frame svg:x="1in" svg:y="5.2in" svg:width="8in" svg:height="1.5in">
          <table:table>
            <table:table-row>
              <table:table-cell><text:p>Component</text:p></table:table-cell>
              <table:table-cell><text:p>Status</text:p></table:table-cell>
            </table:table-row>
            <table:table-row>
              <table:table-cell><text:p>ODP Engine</text:p></table:table-cell>
              <table:table-cell><text:p>Active</text:p></table:table-cell>
            </table:table-row>
          </table:table>
        </draw:frame>
        <presentation:notes>
          <draw:page>
            <draw:frame>
              <draw:text-box>
                <text:p>ODP Speaker Note: Test notes extraction in OpenDocument format.</text:p>
              </draw:text-box>
            </draw:frame>
          </draw:page>
        </presentation:notes>
      </draw:page>
    </office:presentation>
  </office:body>
</office:document-content>""",
        )
    generated["odp_text_tables"] = odp_path

    # 11. Genuine Legacy PPT (OLE2 Compound Document)
    class PptCompoundDoc(xlwt.CompoundDoc.XlsDoc):
        def _build_directory(self) -> None:
            self.dir_stream = b""
            dentry_name = "Root Entry\x00".encode("utf-16-le")
            dentry_name_sz = len(dentry_name)
            dentry_name_pad = b"\x00" * (64 - dentry_name_sz)
            self.dir_stream += struct.pack(
                "<64s H 2B 3l 9L l L L",
                dentry_name + dentry_name_pad,
                dentry_name_sz,
                0x05,
                0x01,
                -1,
                -1,
                1,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                -2,
                0,
                0,
            )
            dentry_name = "PowerPoint Document\x00".encode("utf-16-le")
            dentry_name_sz = len(dentry_name)
            dentry_name_pad = b"\x00" * (64 - dentry_name_sz)
            self.dir_stream += struct.pack(
                "<64s H 2B 3l 9L l L L",
                dentry_name + dentry_name_pad,
                dentry_name_sz,
                0x02,
                0x01,
                -1,
                -1,
                -1,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                0,
                self.book_stream_len,
                0,
            )
            empty_entry = struct.pack(
                "<64s H 2B 3l 9L l L L",
                b"\x00" * 64,
                0,
                0x00,
                0x01,
                -1,
                -1,
                -1,
                0, 0, 0, 0, 0, 0, 0, 0, 0,
                -2,
                0,
                0,
            )
            self.dir_stream += empty_entry * 2

    ppt_path = output_dir / "legacy_powerpoint.ppt"
    doc_ppt = PptCompoundDoc()
    t1 = b"Executive Review 2003 -- Legacy Binary Presentation"
    t2 = b"Key Highlights: Maintained for legacy compatibility"
    stream_data = (
        struct.pack("<HHI", 0, 4008, len(t1))
        + t1
        + struct.pack("<HHI", 0, 4008, len(t2))
        + t2
    )
    with open(ppt_path, "wb") as f:
        doc_ppt.save(f, stream_data)
    generated["legacy_powerpoint"] = ppt_path

    # 12. Corrupted / Malformed Presentation
    corrupted_path = output_dir / "corrupted_presentation.pptx"
    with open(corrupted_path, "wb") as f:
        f.write(b"PK\x03\x04\x14\x00\x00\x00Truncated corrupted zip data that cannot be decompressed")
    generated["corrupted_presentation"] = corrupted_path

    return generated


if __name__ == "__main__":
    out = Path(__file__).parent
    fixtures = generate_fixtures(out)
    print(f"Generated {len(fixtures)} presentation test fixtures in {out}:")
    for name, p in fixtures.items():
        print(f" - {name}: {p.name} ({p.stat().st_size} bytes)")
