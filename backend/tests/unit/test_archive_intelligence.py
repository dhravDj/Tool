"""Unit tests for Archive & Nested File Processing Engine (Phase 10)."""

import json
from pathlib import Path

import pytest

from app.modules.archive_intelligence.extractors.safe_extractor import SafeArchiveExtractor
from app.modules.archive_intelligence.generators.child_manifest_generator import (
    ArchiveChildFileManifestGenerator,
)
from app.modules.archive_intelligence.generators.extraction_report_generator import (
    ArchiveExtractionReportGenerator,
)
from app.modules.archive_intelligence.generators.json_generator import ArchiveJSONGenerator
from app.modules.archive_intelligence.generators.manifest_generator import (
    ArchiveManifestGenerator,
)
from app.modules.archive_intelligence.generators.markdown_generator import (
    ArchiveMarkdownGenerator,
)
from app.modules.archive_intelligence.generators.security_report_generator import (
    ArchiveSecurityReportGenerator,
)
from app.modules.archive_intelligence.generators.text_generator import ArchivePlainTextGenerator
from app.modules.archive_intelligence.generators.tree_generator import ArchiveTreeGenerator
from app.modules.archive_intelligence.hierarchy import ArchiveHierarchyBuilder
from app.modules.archive_intelligence.inspectors.registry import inspector_registry
from app.modules.archive_intelligence.pipeline import archive_pipeline

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "archives"


def test_archive_capabilities() -> None:
    """Verify engine capabilities expose all 10 formats and safety features."""
    caps = archive_pipeline.get_capabilities()
    assert "supported_formats" in caps
    expected_fmts = ["zip", "7z", "tar", "tar.gz", "tgz", "gz", "tar.bz2", "tbz2", "tar.xz", "txz"]
    for fmt in expected_fmts:
        assert fmt in caps["supported_formats"]
    assert caps["max_nesting_depth"] == 5
    assert caps["max_entries_per_archive"] == 10000
    assert "archive_bomb_protection" in caps["features"]
    assert "path_traversal_defense" in caps["features"]


def test_inspect_valid_mixed_zip() -> None:
    """Inspect mixed ZIP archive with docs, images, code, and structured data."""
    zip_path = FIXTURES_DIR / "valid_mixed.zip"
    meta, entries, safety = inspector_registry.inspect(zip_path)

    assert meta["format"] == "zip"
    assert meta["comment"] == "DocuMind AI Test Archive"
    assert len(entries) == 6
    assert meta["file_count"] == 6
    assert meta["directory_count"] == 0
    assert not safety.corruption_detected
    assert not safety.encryption_detected

    filenames = {e.filename for e in entries}
    assert "sample.pdf" in filenames
    assert "notes.txt" in filenames
    assert "icon.png" in filenames
    assert "table.csv" in filenames
    assert "main.py" in filenames
    assert "config.json" in filenames

    # Check categories
    cat_by_file = {e.filename: e.detection_result.get("category") for e in entries}
    assert cat_by_file["sample.pdf"] in ("document", "pdf")
    assert cat_by_file["icon.png"] == "image"
    assert cat_by_file["table.csv"] == "spreadsheet"
    assert cat_by_file["main.py"] == "code"
    assert cat_by_file["config.json"] == "structured_data"


def test_inspect_7z_archive() -> None:
    """Inspect 7z archive without full decompression."""
    sevenz_path = FIXTURES_DIR / "valid_7z.7z"
    meta, entries, safety = inspector_registry.inspect(sevenz_path)

    assert meta["format"] == "7z"
    assert len(entries) >= 2
    assert not safety.encryption_detected
    filenames = {e.filename for e in entries}
    assert "info.txt" in filenames
    assert "calc.py" in filenames


def test_inspect_tar_variants() -> None:
    """Inspect TAR, TAR.GZ, TAR.BZ2, and TAR.XZ archives."""
    for filename in [
        "valid_tar.tar",
        "valid_targz.tar.gz",
        "valid_tgz.tgz",
        "valid_tarbz2.tar.bz2",
        "valid_tarxz.tar.xz",
    ]:
        tar_path = FIXTURES_DIR / filename
        meta, entries, safety = inspector_registry.inspect(tar_path)
        assert len(entries) >= 1
        assert not safety.corruption_detected


def test_inspect_single_gz() -> None:
    """Inspect standalone .csv.gz archive."""
    gz_path = FIXTURES_DIR / "valid_single.csv.gz"
    meta, entries, safety = inspector_registry.inspect(gz_path)
    assert meta["format"] == "gz"
    assert len(entries) == 1
    assert entries[0].filename == "valid_single.csv"
    assert entries[0].detection_result.get("category") == "spreadsheet"


def test_empty_archive() -> None:
    """Inspect empty archive without errors."""
    empty_path = FIXTURES_DIR / "empty.zip"
    meta, entries, safety = inspector_registry.inspect(empty_path)
    assert len(entries) == 0
    assert not safety.corruption_detected


def test_unicode_paths_and_hierarchy() -> None:
    """Inspect archive with Unicode and emoji names and build tree."""
    uni_path = FIXTURES_DIR / "unicode_paths.zip"
    meta, entries, safety = inspector_registry.inspect(uni_path)
    assert len(entries) == 3

    tree = ArchiveHierarchyBuilder.build_tree("unicode_archive", entries)
    assert tree.file_count == 3
    child_names = {c.name for c in tree.children}
    assert "dokument_üöä_測試.txt" in child_names
    assert "données_café.json" in child_names
    assert "emoji_🚀_report.md" in child_names


def test_duplicate_and_case_collision_detection() -> None:
    """Verify duplicate paths and case collisions are detected with warnings."""
    dup_path = FIXTURES_DIR / "duplicate_paths.zip"
    meta, entries, safety = inspector_registry.inspect(dup_path)
    tree = ArchiveHierarchyBuilder.build_tree("dup_archive", entries)

    all_warnings: list[str] = []

    def collect_warnings(node):
        all_warnings.extend(node.warnings)
        for c in node.children:
            collect_warnings(c)

    collect_warnings(tree)

    has_dup = any("Duplicate entry" in w for w in all_warnings)
    has_case = any("Case collision" in w for w in all_warnings)
    assert has_dup
    assert has_case


def test_path_traversal_blocking(tmp_path: Path) -> None:
    """Verify directory traversal '../' is detected and blocked during extraction."""
    slip_path = FIXTURES_DIR / "slip_traversal.zip"
    meta, entries, safety = inspector_registry.inspect(slip_path)
    assert safety.path_traversal_blocked > 0

    extractor = SafeArchiveExtractor()
    out_dir = tmp_path / "extracted_slip"
    extracted, blocked, failed, ext_safety = extractor.extract(slip_path, out_dir)

    assert ext_safety.path_traversal_blocked > 0
    assert len(blocked) >= 1
    # Ensure no files escaped out_dir
    for item in out_dir.rglob("*"):
        assert item.resolve().is_relative_to(out_dir.resolve())
    assert not (tmp_path / "etc" / "passwd").exists()


def test_absolute_paths_neutralization(tmp_path: Path) -> None:
    """Verify absolute and Windows drive paths are neutralized or blocked."""
    abs_path = FIXTURES_DIR / "absolute_path.zip"
    extractor = SafeArchiveExtractor()
    out_dir = tmp_path / "extracted_abs"
    extracted, blocked, failed, ext_safety = extractor.extract(abs_path, out_dir)

    for item in out_dir.rglob("*"):
        assert item.resolve().is_relative_to(out_dir.resolve())


def test_symlink_escape_blocking(tmp_path: Path) -> None:
    """Verify symlinks pointing outside extraction directory are blocked."""
    sym_path = FIXTURES_DIR / "symlink_escape.tar"
    meta, entries, safety = inspector_registry.inspect(sym_path)
    assert safety.symlink_entries_blocked > 0

    extractor = SafeArchiveExtractor()
    out_dir = tmp_path / "extracted_sym"
    extracted, blocked, failed, ext_safety = extractor.extract(sym_path, out_dir)
    assert len(blocked) >= 1
    blocked_reasons = [b["reason"] for b in blocked]
    assert any("Symlink" in r for r in blocked_reasons)


def test_zip_bomb_detection() -> None:
    """Verify high compression ratio zip bomb is detected during inspection."""
    bomb_path = FIXTURES_DIR / "zip_bomb.zip"
    meta, entries, safety = inspector_registry.inspect(bomb_path)
    assert safety.compression_ratio_exceeded or safety.suspicious_entries > 0


def test_encrypted_archive_detection() -> None:
    """Verify password encryption flag is detected."""
    enc_path = FIXTURES_DIR / "encrypted.7z"
    meta, entries, safety = inspector_registry.inspect(enc_path)
    assert safety.encryption_detected or meta.get("is_encrypted")


def test_corrupted_archive_handling() -> None:
    """Verify corrupted zip and tar archives are safely flagged without crashing."""
    corrupt_zip = FIXTURES_DIR / "corrupted.zip"
    meta1, entries1, safety1 = inspector_registry.inspect(corrupt_zip)
    assert meta1["is_corrupted"]
    assert safety1.corruption_detected

    corrupt_tar = FIXTURES_DIR / "corrupted.tar.gz"
    meta2, entries2, safety2 = inspector_registry.inspect(corrupt_tar)
    assert meta2["is_corrupted"]
    assert safety2.corruption_detected


@pytest.mark.asyncio
async def test_output_generators() -> None:
    """Verify all 8 output generators produce valid non-empty reports."""
    zip_path = FIXTURES_DIR / "valid_mixed.zip"
    doc = await archive_pipeline.analyze_archive(
        file_path=zip_path,
        file_id="test_file_id",
        original_filename="valid_mixed.zip",
        mode="inspect_only",
    )

    # 1. JSON
    json_out = ArchiveJSONGenerator().generate(doc)
    assert json_out.startswith("{")
    data = json.loads(json_out)
    assert data["archive_format"] == "zip"

    # 2. Markdown
    md_out = ArchiveMarkdownGenerator().generate(doc)
    assert "# Archive Intelligence Report" in md_out
    assert "valid_mixed.zip" in md_out

    # 3. Plain Text
    txt_out = ArchivePlainTextGenerator().generate(doc)
    assert "DOCUMIND ARCHIVE REPORT" in txt_out

    # 4. Manifest (JSON and CSV)
    man_json = ArchiveManifestGenerator().generate(doc, "json")
    assert "sample.pdf" in man_json
    man_csv = ArchiveManifestGenerator().generate(doc, "csv")
    assert "original_path,normalized_path" in man_csv

    # 5. Tree
    tree_out = ArchiveTreeGenerator().generate(doc.hierarchy)
    assert "docs/" in tree_out or "sample.pdf" in tree_out

    # 6. Extraction Report
    ext_rep = ArchiveExtractionReportGenerator().generate(doc)
    assert "metrics" in json.loads(ext_rep)

    # 7. Security Report
    sec_rep = ArchiveSecurityReportGenerator().generate(doc)
    assert "safety_summary" in json.loads(sec_rep)

    # 8. Child Manifest
    child_man = ArchiveChildFileManifestGenerator().generate(doc)
    assert "children" in json.loads(child_man)


def test_safe_extraction_execution(tmp_path: Path) -> None:
    """Verify safe extraction creates real files and computes correct SHA256 hashes."""
    zip_path = FIXTURES_DIR / "valid_mixed.zip"
    extractor = SafeArchiveExtractor()
    out_dir = tmp_path / "extract_test"

    extracted, blocked, failed, safety = extractor.extract(zip_path, out_dir)
    assert len(extracted) == 6
    assert len(blocked) == 0
    assert len(failed) == 0

    for f_info in extracted:
        p = Path(f_info["extracted_path"])
        assert p.exists()
        assert p.stat().st_size == f_info["file_size"]
        assert len(f_info["sha256"]) == 64
