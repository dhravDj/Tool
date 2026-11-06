"""Language parser registry managing all language-specific parsers."""

from typing import Any

from app.modules.code_intelligence.parsers.base import BaseLanguageParser
from app.modules.code_intelligence.parsers.c_cpp_parser import CCppParser
from app.modules.code_intelligence.parsers.go_parser import GoParser
from app.modules.code_intelligence.parsers.java_parser import JavaParser
from app.modules.code_intelligence.parsers.js_ts_parser import JavaScriptTypeScriptParser
from app.modules.code_intelligence.parsers.php_parser import PHPParser
from app.modules.code_intelligence.parsers.python_parser import PythonParser
from app.modules.code_intelligence.parsers.rust_parser import RustParser
from app.modules.code_intelligence.parsers.sql_parser import SQLParser
from app.modules.code_intelligence.parsers.web_parsers import CSSParser, HTMLParser


class LanguageParserRegistry:
    """Registry coordinating parser dispatch for all 14 supported programming languages."""

    def __init__(self) -> None:
        self.parsers: list[BaseLanguageParser] = [
            PythonParser(),
            JavaScriptTypeScriptParser(),
            SQLParser(),
            CCppParser(),
            JavaParser(),
            GoParser(),
            RustParser(),
            PHPParser(),
            HTMLParser(),
            CSSParser(),
        ]
        self._parsers_by_ext: dict[str, BaseLanguageParser] = {}
        for p in self.parsers:
            for ext in p.supported_extensions:
                self._parsers_by_ext[ext.lower()] = p

    def get_parser_for_filename(self, filename: str) -> BaseLanguageParser | None:
        """Find matching parser by file extension."""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        return self._parsers_by_ext.get(ext)

    def get_parser_for_language(self, language: str) -> BaseLanguageParser | None:
        """Find matching parser by language ID."""
        clean_lang = language.lower().strip()
        for p in self.parsers:
            if p.language == clean_lang or clean_lang in p.supported_extensions:
                return p
        return None

    def list_supported_languages(self) -> list[dict[str, Any]]:
        """List all supported programming language specs."""
        specs = []
        for p in self.parsers:
            specs.append(
                {
                    "language": p.language,
                    "supported_extensions": p.supported_extensions,
                    "class": p.__class__.__name__,
                }
            )
        return specs


language_parser_registry = LanguageParserRegistry()
