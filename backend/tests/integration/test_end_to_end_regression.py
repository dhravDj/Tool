"""End-to-end regression tests verifying Phases 1 to 4 against real-world fixtures."""

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.hardware import hardware_governor
from app.main import app
from app.modules.extraction.pipeline import extraction_pipeline
from app.modules.files.detection.detector import universal_detector
from app.modules.image_intelligence.vision.engine import VisionIntelligenceEngine


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent.parent / "fixtures" / "real_world_dataset"


@pytest.fixture
def ground_truth(fixtures_dir: Path) -> dict:
    gt_file = fixtures_dir / "ground_truth.json"
    with open(gt_file, encoding="utf-8") as f:
        return json.load(f)


def test_hardware_governor_constraints():
    """Verify hardware governor limits are enforced."""
    status = hardware_governor.detect_hardware()
    assert status["cpu"]["active_workers_limit"] == settings.MAX_PARALLEL_WORKERS
    assert status["accelerator"]["gpu_concurrency_limit"] == settings.GPU_MAX_CONCURRENT_INFERENCE


def test_real_world_detection_accuracy(fixtures_dir: Path, ground_truth: dict):
    """Verify all real-world fixtures detect format, category, mismatch, and corruption accurately."""
    for filename, gt in ground_truth.items():
        file_path = fixtures_dir / filename
        res = universal_detector.detect_file(file_path, filename)

        assert res.format_id == gt["format_id"], (
            f"Format mismatch on {filename}: expected {gt['format_id']}, got {res.format_id}"
        )
        assert res.is_mismatch == gt.get("is_mismatch", False), f"Mismatch flag error on {filename}"
        assert res.is_corrupted == gt.get("is_corrupted", False), (
            f"Corrupted flag error on {filename}"
        )
        assert res.is_suspicious == gt.get("is_suspicious", False), (
            f"Suspicious flag error on {filename}"
        )


@pytest.mark.asyncio
async def test_real_world_document_extraction(fixtures_dir: Path, ground_truth: dict):
    """Verify text recall and structural extraction on PDF, DOCX, TXT, and MD."""
    doc_samples = ["invoice.pdf", "memo.docx", "notes.txt", "documentation.md"]
    for doc_name in doc_samples:
        doc_path = fixtures_dir / doc_name
        gt = ground_truth[doc_name]
        canonical_doc = await extraction_pipeline.extract_path(
            file_path=doc_path,
            format_id=gt["format_id"],
            original_filename=doc_name,
        )

        assert len(canonical_doc.blocks) > 0
        extracted_text = " ".join(b.text for b in canonical_doc.blocks)
        for expected in gt.get("expected_text", []):
            assert expected.lower() in extracted_text.lower(), (
                f"Expected '{expected}' missing from {doc_name}"
            )


def test_vision_engine_heuristic_classification():
    """Verify VisionIntelligenceEngine is transparently classified as heuristic CV."""
    engine = VisionIntelligenceEngine()
    assert engine.engine_name == "documind-heuristic-cv-v1"
    assert engine.engine_type == "heuristic"
    assert engine.hardware_acceleration == "cpu"


@pytest.mark.asyncio
async def test_batch_detection_concurrency_endpoint(fixtures_dir: Path):
    """Verify parallel batch detection API endpoint handles multiple files concurrently."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = [
            ("files", ("notes.txt", (fixtures_dir / "notes.txt").read_bytes(), "text/plain")),
            (
                "files",
                (
                    "documentation.md",
                    (fixtures_dir / "documentation.md").read_bytes(),
                    "text/markdown",
                ),
            ),
            (
                "files",
                ("invoice.pdf", (fixtures_dir / "invoice.pdf").read_bytes(), "application/pdf"),
            ),
        ]
        resp = await client.post("/api/v1/files/detect/batch", files=files)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_files"] == 3
        assert data["successful_detections"] == 3
