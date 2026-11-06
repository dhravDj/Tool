"""Base interface for all language-specific code parsers."""

from abc import ABC, abstractmethod
from typing import Any

from app.modules.code_intelligence.schemas.code_document import (
    CodeDependency,
    CodeDiagnostic,
    CodeImport,
    CodeMetrics,
    CodeSymbol,
    SyntaxValidationResult,
)


class BaseLanguageParser(ABC):
    """Abstract base class for language parsers exposing uniform code intelligence capabilities."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Language identifier (e.g. 'py', 'js', 'ts', 'sql')."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """List of handled file extensions without dots."""
        pass

    def can_parse(self, filename: str, content: str = "") -> bool:
        """Check whether this parser is suitable for the given filename or content signature."""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        return ext in self.supported_extensions

    @abstractmethod
    def parse(
        self,
        content: str,
        filename: str = "",
        options: dict[str, Any] | None = None,
    ) -> tuple[
        list[CodeSymbol],
        list[CodeImport],
        list[CodeDependency],
        CodeMetrics,
        list[CodeDiagnostic],
        SyntaxValidationResult,
    ]:
        """Parse source code content and extract symbols, imports, dependencies, metrics, diagnostics, and syntax validation."""
        pass

    def calculate_basic_line_metrics(self, content: str) -> tuple[int, int, int, int]:
        """Utility to calculate (total_lines, code_lines, comment_lines, blank_lines) with language-agnostic line splitting."""
        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        return total_lines, 0, 0, blank_lines
