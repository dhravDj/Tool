"""Unit tests for Phase 9 Structured Data Intelligence Engine."""

from pathlib import Path

from app.modules.structured_data_intelligence.generators.csv_generator import StructuredCSVGenerator
from app.modules.structured_data_intelligence.generators.json_generator import (
    StructuredJSONGenerator,
)
from app.modules.structured_data_intelligence.generators.markdown_generator import (
    StructuredMarkdownGenerator,
)
from app.modules.structured_data_intelligence.pipeline import structured_pipeline

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "structured"


def test_structured_pipeline_capabilities():
    """Verify capabilities list all 5 supported structured formats and features."""
    caps = structured_pipeline.get_capabilities()
    assert len(caps["supported_formats"]) == 5
    for fmt in ["json", "xml", "yaml", "toml", "parquet"]:
        assert fmt in caps["supported_formats"]
    assert "json_duplicate_key_detection" in caps["features"]
    assert "xml_xxe_protection" in caps["features"]
    assert "parquet_columnar_profiling_zero_dataframe" in caps["features"]


async def test_json_engine_valid_and_nested():
    """Test standard valid JSON and nested hierarchy profiling."""
    fixture_path = FIXTURES_DIR / "valid.json"
    doc = await structured_pipeline.analyze_structured_data(
        fixture_path, file_id="json_01", original_filename="valid.json"
    )

    assert doc.format == "json"
    assert doc.validation_results.is_valid is True
    assert doc.data_profile.total_rows >= 1
    assert doc.data_profile.total_columns >= 4

    col_names = [c.name for c in doc.data_profile.column_profiles]
    assert "system" in col_names
    assert "version" in col_names
    assert "active" in col_names

    # Test deeply nested JSON
    nested_path = FIXTURES_DIR / "nested.json"
    nested_doc = await structured_pipeline.analyze_structured_data(
        nested_path, file_id="json_nested", original_filename="nested.json"
    )
    assert nested_doc.validation_results.is_valid is True
    assert any("level1" in c.name for c in nested_doc.data_profile.column_profiles)


async def test_json_duplicate_key_detection():
    """Test duplicate key detection in JSON."""
    fixture_path = FIXTURES_DIR / "duplicate_keys.json"
    doc = await structured_pipeline.analyze_structured_data(
        fixture_path, file_id="json_dup", original_filename="duplicate_keys.json"
    )

    assert doc.format == "json"
    assert doc.validation_results.is_valid is True
    assert len(doc.validation_results.duplicate_keys) > 0
    assert "user_id" in doc.validation_results.duplicate_keys or "theme" in doc.validation_results.duplicate_keys


async def test_json_invalid_syntax():
    """Test malformed JSON error handling."""
    fixture_path = FIXTURES_DIR / "invalid.json"
    doc = await structured_pipeline.analyze_structured_data(
        fixture_path, file_id="json_inv", original_filename="invalid.json"
    )

    assert doc.validation_results.is_valid is False
    assert len(doc.validation_results.schema_errors) > 0


async def test_xml_engine_and_xxe_defense():
    """Test XML parsing and defensive XXE attack mitigation."""
    valid_path = FIXTURES_DIR / "valid.xml"
    doc = await structured_pipeline.analyze_structured_data(
        valid_path, file_id="xml_01", original_filename="valid.xml"
    )

    assert doc.format == "xml"
    assert doc.validation_results.is_valid is True
    assert doc.data_profile.total_rows >= 2
    assert any("book" in c.name for c in doc.data_profile.column_profiles)

    # Test XXE attack interception
    xxe_path = FIXTURES_DIR / "xxe_attack.xml"
    xxe_doc = await structured_pipeline.analyze_structured_data(
        xxe_path, file_id="xml_xxe", original_filename="xxe_attack.xml"
    )

    # DefusedXML blocks entity resolution safely
    all_warnings_and_errors = (
        xxe_doc.validation_results.security_warnings
        + xxe_doc.validation_results.schema_errors
        + xxe_doc.warnings
    )
    assert any("xxe" in w.lower() or "entity" in w.lower() or "forbidden" in w.lower() for w in all_warnings_and_errors)


async def test_yaml_engine_and_alias_bomb_defense():
    """Test YAML safe parsing and alias explosion defense."""
    valid_path = FIXTURES_DIR / "valid.yaml"
    doc = await structured_pipeline.analyze_structured_data(
        valid_path, file_id="yaml_01", original_filename="valid.yaml"
    )

    assert doc.format == "yaml"
    assert doc.validation_results.is_valid is True
    col_names = [c.name for c in doc.data_profile.column_profiles]
    assert any("services" in c for c in col_names)

    # Test Alias Bomb mitigation
    bomb_path = FIXTURES_DIR / "alias_bomb.yaml"
    bomb_doc = await structured_pipeline.analyze_structured_data(
        bomb_path, file_id="yaml_bomb", original_filename="alias_bomb.yaml"
    )
    all_warnings_and_errors = (
        bomb_doc.validation_results.security_warnings
        + bomb_doc.validation_results.schema_errors
        + bomb_doc.warnings
    )
    assert any("alias" in w.lower() or "bomb" in w.lower() for w in all_warnings_and_errors)


async def test_toml_engine_table_extraction():
    """Test TOML parsing and table/field extraction."""
    fixture_path = FIXTURES_DIR / "valid.toml"
    doc = await structured_pipeline.analyze_structured_data(
        fixture_path, file_id="toml_01", original_filename="valid.toml"
    )

    assert doc.format == "toml"
    assert doc.validation_results.is_valid is True
    col_names = [c.name for c in doc.data_profile.column_profiles]
    assert any("project" in c for c in col_names)
    assert any("database" in c for c in col_names)


async def test_parquet_engine_zero_dataframe_profiling():
    """Test Parquet column statistics and schema extraction without loading full dataframe."""
    fixture_path = FIXTURES_DIR / "valid.parquet"
    doc = await structured_pipeline.analyze_structured_data(
        fixture_path, file_id="pq_01", original_filename="valid.parquet"
    )

    assert doc.format == "parquet"
    assert doc.validation_results.is_valid is True
    assert doc.data_profile.total_rows == 5
    assert doc.data_profile.total_columns == 4

    col_map = {c.name: c for c in doc.data_profile.column_profiles}
    assert "id" in col_map
    assert "username" in col_map
    assert "balance" in col_map
    assert "is_verified" in col_map

    # Check that statistics were populated
    balance_col = col_map["balance"]
    assert balance_col.statistics is not None
    assert balance_col.statistics.null_count == 1
    assert balance_col.statistics.min_value is not None

    # Test corrupted parquet file
    corrupt_path = FIXTURES_DIR / "corrupted.parquet"
    corrupt_doc = await structured_pipeline.analyze_structured_data(
        corrupt_path, file_id="pq_err", original_filename="corrupted.parquet"
    )
    assert corrupt_doc.validation_results.is_valid is False
    assert len(corrupt_doc.validation_results.schema_errors) > 0


async def test_structured_generators():
    """Test JSON, Markdown, and CSV generators for structured documents."""
    fixture_path = FIXTURES_DIR / "valid.parquet"
    doc = await structured_pipeline.analyze_structured_data(
        fixture_path, file_id="gen_pq", original_filename="valid.parquet"
    )

    json_str = StructuredJSONGenerator().generate(doc)
    assert '"format": "parquet"' in json_str
    assert '"total_rows": 5' in json_str

    md_str = StructuredMarkdownGenerator().generate(doc)
    assert "# Structured Data Intelligence Report" in md_str
    assert "balance" in md_str

    csv_str = StructuredCSVGenerator().generate(doc)
    assert "balance" in csv_str
    assert "id" in csv_str
