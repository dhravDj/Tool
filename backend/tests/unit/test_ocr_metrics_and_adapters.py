"""Unit tests for OCR evaluation metrics (CER/WER) and VisionAdapter classification."""

from PIL import Image

from app.modules.image_intelligence.ocr.metrics import (
    calculate_cer,
    calculate_wer,
    evaluate_ocr_accuracy,
)
from app.modules.image_intelligence.vision.adapters import HeuristicVisionAdapter
from app.modules.image_intelligence.vision.engine import VisionIntelligenceEngine


def test_calculate_cer_identical():
    ref = "DocuMind AI universal file intelligence platform"
    hyp = "DocuMind AI universal file intelligence platform"
    assert calculate_cer(ref, hyp) == 0.0


def test_calculate_cer_substitutions():
    ref = "DocuMind"
    hyp = "DocuM1nd"  # 1 substitution in 8 chars = 1/8 = 0.125
    cer = calculate_cer(ref, hyp)
    assert cer == 0.125


def test_calculate_wer_identical():
    ref = "This is a clean document page"
    hyp = "This is a clean document page"
    assert calculate_wer(ref, hyp) == 0.0


def test_calculate_wer_mismatches():
    ref = "invoice number forty two"
    hyp = "invoice number 42"  # 'forty two' replaced with '42' -> 2 edits in 4 words = 0.5
    wer = calculate_wer(ref, hyp)
    assert wer == 0.5


def test_evaluate_ocr_accuracy_report():
    ref = "Quarterly financial earnings report"
    hyp = "Quarterly financial earnings report"
    rep = evaluate_ocr_accuracy(ref, hyp)

    assert rep["cer"] == 0.0
    assert rep["wer"] == 0.0
    assert rep["char_accuracy_pct"] == 100.0
    assert rep["word_accuracy_pct"] == 100.0
    assert rep["reference_word_count"] == 4


def test_vision_engine_honest_classification():
    engine = VisionIntelligenceEngine()
    assert engine.engine_name == "documind-heuristic-cv-v1"
    assert engine.engine_type == "heuristic"
    assert engine.hardware_acceleration == "cpu"

    adapter = HeuristicVisionAdapter()
    assert adapter.engine_name == "documind-heuristic-cv-v1"
    assert adapter.engine_type == "heuristic"

    # Test scene analysis returns heuristic document_page classification
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    caption, scene_type, objects, colors, regions = engine.analyze_scene(
        img, ocr_text="DocuMind Invoice #123456 Total Due"
    )
    assert scene_type == "document_page"
    assert "text_document" in objects
    assert len(colors) > 0
