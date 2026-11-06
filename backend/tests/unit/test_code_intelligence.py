"""Unit tests for Phase 9 Code Intelligence Engine."""

from pathlib import Path

from app.modules.code_intelligence.generators.json_generator import CodeJSONGenerator
from app.modules.code_intelligence.generators.markdown_generator import CodeMarkdownGenerator
from app.modules.code_intelligence.generators.text_generator import CodePlainTextGenerator
from app.modules.code_intelligence.pipeline import code_pipeline

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "code"


def test_code_pipeline_capabilities():
    """Verify capabilities list all 14 supported languages and analysis tools."""
    caps = code_pipeline.get_capabilities()
    assert len(caps["supported_languages"]) == 14
    for lang in ["py", "js", "ts", "jsx", "tsx", "html", "css", "java", "c", "cpp", "go", "rs", "php", "sql"]:
        assert lang in caps["supported_languages"]
    assert "symbol_extraction" in caps["features"]
    assert "security_vulnerability_detection" in caps["features"]


async def test_python_parser_extraction():
    """Test Python parser AST analysis, symbols, imports, dependencies, metrics, diagnostics."""
    fixture_path = FIXTURES_DIR / "sample_python.py"
    doc = await code_pipeline.analyze_code(fixture_path, file_id="py_01", original_filename="sample_python.py")

    assert doc.language == "py"
    assert doc.syntax_validation.is_valid is True
    assert doc.metrics.total_lines > 20
    assert doc.metrics.function_count >= 2
    assert doc.metrics.class_count >= 1

    # Check extracted symbols
    symbol_names = [s.name for s in doc.symbols]
    assert "UserAccount" in symbol_names
    assert "fetch_user_data" in symbol_names
    assert "get_display_name" in symbol_names

    # Check imports & external dependencies
    import_mods = [imp.module_name for imp in doc.imports]
    assert "requests" in import_mods
    assert "pydantic" in import_mods
    assert "os" in import_mods

    dep_names = [dep.name for dep in doc.dependencies]
    assert "requests" in dep_names
    assert "pydantic" in dep_names

    # Check security diagnostics (API_KEY secret detection, unused import)
    rule_ids = [diag.rule_id for diag in doc.diagnostics]
    assert "SEC-HARDCODED-SECRET" in rule_ids
    assert "PY-UNUSED-IMPORT" in rule_ids


async def test_python_syntax_error_graceful_handling():
    """Verify broken Python code triggers syntax diagnostic and does not crash."""
    fixture_path = FIXTURES_DIR / "sample_python_syntax_error.py"
    doc = await code_pipeline.analyze_code(fixture_path, file_id="py_err", original_filename="sample_python_syntax_error.py")

    assert doc.syntax_validation.is_valid is False
    assert len(doc.syntax_validation.errors) > 0
    assert any("SYNTAX-ERROR" in diag.rule_id for diag in doc.diagnostics)


async def test_javascript_parser():
    """Test JavaScript symbol extraction, require imports, and debugger diagnostic."""
    fixture_path = FIXTURES_DIR / "sample_javascript.js"
    doc = await code_pipeline.analyze_code(fixture_path, file_id="js_01", original_filename="sample_javascript.js")

    assert doc.language == "js"
    symbol_names = [s.name for s in doc.symbols]
    assert "CalculationService" in symbol_names
    assert "processBatch" in symbol_names

    dep_names = [dep.name for dep in doc.dependencies]
    assert "lodash" in dep_names

    rule_ids = [diag.rule_id for diag in doc.diagnostics]
    assert "JS-DEBUGGER-STMT" in rule_ids


async def test_typescript_parser():
    """Test TypeScript interfaces, types, classes, functions, and import parsing."""
    fixture_path = FIXTURES_DIR / "sample_typescript.ts"
    doc = await code_pipeline.analyze_code(fixture_path, file_id="ts_01", original_filename="sample_typescript.ts")

    assert doc.language == "ts"
    symbol_names = [s.name for s in doc.symbols]
    assert "UserProfile" in symbol_names
    assert "StatusType" in symbol_names
    assert "AuthenticationManager" in symbol_names
    assert "formatAddress" in symbol_names

    dep_names = [dep.name for dep in doc.dependencies]
    assert "rxjs" in dep_names or "axios" in dep_names


async def test_react_jsx_tsx_parsers():
    """Test React JSX and TSX parser extraction."""
    jsx_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_react.jsx", file_id="jsx_01", original_filename="sample_react.jsx")
    assert jsx_doc.language == "jsx"
    assert any(s.name == "CounterWidget" for s in jsx_doc.symbols)

    tsx_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_react.tsx", file_id="tsx_01", original_filename="sample_react.tsx")
    assert tsx_doc.language == "tsx"
    assert any(s.name == "ButtonCard" for s in tsx_doc.symbols)
    assert any(s.name == "ButtonCardProps" for s in tsx_doc.symbols)


async def test_web_html_css_parsers():
    """Test HTML and CSS parsers."""
    html_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_page.html", file_id="html_01", original_filename="sample_page.html")
    assert html_doc.language == "html"
    assert len(html_doc.symbols) > 0
    # Notice inline script warning
    assert any(d.rule_id == "HTML-INLINE-SCRIPT" for d in html_doc.diagnostics)

    css_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_styles.css", file_id="css_01", original_filename="sample_styles.css")
    assert css_doc.language == "css"
    assert len(css_doc.symbols) > 0


async def test_java_parser():
    """Test Java parser extracting package, class, methods, imports."""
    fixture_path = FIXTURES_DIR / "sample_java.java"
    doc = await code_pipeline.analyze_code(fixture_path, file_id="java_01", original_filename="sample_java.java")

    assert doc.language == "java"
    symbol_names = [s.name for s in doc.symbols]
    assert "DocumentService" in symbol_names
    assert "processDocuments" in symbol_names
    assert any(imp.module_name == "org.slf4j.Logger" for imp in doc.imports)


async def test_c_cpp_parsers():
    """Test C and C++ parsers including legacy unsafe C detection."""
    c_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_c.c", file_id="c_01", original_filename="sample_c.c")
    assert c_doc.language == "c"
    assert any(s.name == "PacketHeader" for s in c_doc.symbols)
    assert any(s.name == "copy_buffer_unsafe" for s in c_doc.symbols)
    assert any("STRCPY" in d.rule_id for d in c_doc.diagnostics)

    cpp_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_cpp.cpp", file_id="cpp_01", original_filename="sample_cpp.cpp")
    assert cpp_doc.language == "cpp"
    assert any(s.name == "TensorNode" for s in cpp_doc.symbols)


async def test_go_rust_php_parsers():
    """Test Go, Rust, and PHP parsers."""
    go_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_go.go", file_id="go_01", original_filename="sample_go.go")
    assert go_doc.language == "go"
    assert any(s.name == "ServerConfig" for s in go_doc.symbols)
    assert any(s.name == "StartServer" for s in go_doc.symbols)

    rs_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_rust.rs", file_id="rs_01", original_filename="sample_rust.rs")
    assert rs_doc.language == "rs"
    assert any(s.name == "PipelineConfig" for s in rs_doc.symbols)
    assert any(s.name == "Processable" for s in rs_doc.symbols)
    assert any(d.rule_id == "RUST-UNSAFE-BLOCK" for d in rs_doc.diagnostics)

    php_doc = await code_pipeline.analyze_code(FIXTURES_DIR / "sample_php.php", file_id="php_01", original_filename="sample_php.php")
    assert php_doc.language == "php"
    assert any(s.name == "UserManager" for s in php_doc.symbols)
    assert any(s.name == "findUserById" for s in php_doc.symbols)


async def test_sql_parser():
    """Test SQL parser table, columns, and foreign key relationship extraction via SQLGlot."""
    fixture_path = FIXTURES_DIR / "sample_schema.sql"
    doc = await code_pipeline.analyze_code(fixture_path, file_id="sql_01", original_filename="sample_schema.sql")

    assert doc.language == "sql"
    symbol_names = [s.name for s in doc.symbols]
    assert "users" in symbol_names
    assert "orders" in symbol_names

    # Check foreign key relationships
    assert any(
        dep.dependency_type == "foreign_key_table" and dep.name.lower() == "users"
        for dep in doc.dependencies
    )


async def test_code_generators():
    """Test JSON, Markdown, and PlainText generators."""
    fixture_path = FIXTURES_DIR / "sample_python.py"
    doc = await code_pipeline.analyze_code(fixture_path, file_id="gen_01", original_filename="sample_python.py")

    json_out = CodeJSONGenerator().generate(doc)
    assert '"language": "py"' in json_out
    assert '"UserAccount"' in json_out

    md_out = CodeMarkdownGenerator().generate(doc)
    assert "# Code Intelligence Report" in md_out
    assert "UserAccount" in md_out

    txt_out = CodePlainTextGenerator().generate(doc)
    assert "DocuMind Code Intelligence Summary" in txt_out
    assert "SYMBOLS:" in txt_out or "Symbols:" in txt_out or "Language: PY" in txt_out
