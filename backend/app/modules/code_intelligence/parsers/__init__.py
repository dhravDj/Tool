"""Code intelligence parsers package."""

from app.modules.code_intelligence.parsers.base import BaseLanguageParser
from app.modules.code_intelligence.parsers.c_cpp_parser import CCppParser
from app.modules.code_intelligence.parsers.go_parser import GoParser
from app.modules.code_intelligence.parsers.java_parser import JavaParser
from app.modules.code_intelligence.parsers.js_ts_parser import JavaScriptTypeScriptParser
from app.modules.code_intelligence.parsers.php_parser import PHPParser
from app.modules.code_intelligence.parsers.python_parser import PythonParser
from app.modules.code_intelligence.parsers.registry import (
    LanguageParserRegistry,
    language_parser_registry,
)
from app.modules.code_intelligence.parsers.rust_parser import RustParser
from app.modules.code_intelligence.parsers.sql_parser import SQLParser
from app.modules.code_intelligence.parsers.web_parsers import CSSParser, HTMLParser

__all__ = [
    "BaseLanguageParser",
    "CCppParser",
    "CSSParser",
    "GoParser",
    "HTMLParser",
    "JavaParser",
    "JavaScriptTypeScriptParser",
    "LanguageParserRegistry",
    "PHPParser",
    "PythonParser",
    "RustParser",
    "SQLParser",
    "language_parser_registry",
]
