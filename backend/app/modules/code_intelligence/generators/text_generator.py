"""Plain text summary generator for Code Intelligence documents."""

from app.modules.code_intelligence.schemas.code_document import CodeDocument


class CodePlainTextGenerator:
    """Generates a concise plain text summary of analyzed code."""

    def generate(self, doc: CodeDocument) -> str:
        lines = [
            f"DocuMind Code Intelligence Summary: {doc.file_metadata.get('filename', 'Source Code')}",
            f"Language: {doc.language.upper()} | Syntax Valid: {doc.syntax_validation.is_valid}",
            f"Lines: {doc.metrics.total_lines} total, {doc.metrics.code_lines} code, {doc.metrics.comment_lines} comments, {doc.metrics.blank_lines} blank",
            f"Complexity: {doc.metrics.cyclomatic_complexity} | Nesting: {doc.metrics.nesting_depth}",
            f"Symbols: {len(doc.symbols)} ({doc.metrics.function_count} functions, {doc.metrics.class_count} classes)",
            f"Imports: {len(doc.imports)} | Dependencies: {len(doc.dependencies)}",
            f"Diagnostics: {len(doc.diagnostics)} findings",
        ]
        if doc.symbols:
            lines.append("\nKey Symbols:")
            for s in doc.symbols[:10]:
                lines.append(f"  - [{s.symbol_type}] {s.name} (L{s.start_line})")
        if doc.diagnostics:
            lines.append("\nDiagnostics:")
            for d in doc.diagnostics[:5]:
                lines.append(f"  - [{d.severity.upper()}] L{d.start_line}: {d.message}")
        return "\n".join(lines)
