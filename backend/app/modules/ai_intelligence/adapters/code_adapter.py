"""Code Content Adapter (Phase 9: PY, JS, TS, HTML, CSS, SQL, JAVA, C, CPP, GO, RUST, RS, SH, etc.)."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from app.modules.ai_intelligence.adapters.base import BaseContentAdapter, compute_content_hash
from app.modules.ai_intelligence.schemas.knowledge import (
    ContentBlock,
    KnowledgeDocument,
    SourceReference,
)


class CodeContentAdapter(BaseContentAdapter):
    """Adapts Phase 9 CodeDocument into KnowledgeDocument."""

    def normalize(
        self,
        file_id: str,
        filename: str,
        data: dict[str, Any] | BaseModel,
        parent_archive_id: str | None = None,
    ) -> KnowledgeDocument:
        code_dict = data.model_dump() if isinstance(data, BaseModel) else data
        language = code_dict.get("language") or "unknown"
        content_blocks: list[ContentBlock] = []
        source_refs: list[SourceReference] = []
        seen_citations: set[str] = set()
        full_text_parts: list[str] = []

        symbols = code_dict.get("symbols", [])
        source_code = code_dict.get("source_code") or ""
        lines = source_code.splitlines() if source_code else []

        # 1. AST Symbols (functions, classes, methods)
        for idx, sym in enumerate(symbols):
            sym_name = sym.get("name", f"symbol_{idx}")
            sym_kind = sym.get("kind", "symbol")
            start_line = int(sym.get("start_line", 1) or 1)
            end_line = int(sym.get("end_line", start_line) or start_line)
            docstring = sym.get("docstring") or ""
            signature = sym.get("signature") or ""

            # Extract actual snippet if source code lines exist
            if lines and 1 <= start_line <= len(lines):
                end_idx = min(end_line, len(lines))
                snippet = "\n".join(lines[start_line - 1 : end_idx])
            else:
                snippet = f"{sym_kind} {sym_name} {signature}".strip()
                if docstring:
                    snippet += f"\nDescription: {docstring}"

            if not snippet.strip():
                continue

            citation = f"{filename} — Lines {start_line}–{end_line} ({sym_kind}: {sym_name})"
            full_text_parts.append(snippet)

            src_ref = SourceReference(
                source_file_id=file_id,
                original_filename=filename,
                source_type="code",
                formatted_citation=citation,
                line_start=start_line,
                line_end=end_line,
                metadata={"symbol_name": sym_name, "symbol_type": sym_kind},
            )
            if citation not in seen_citations:
                source_refs.append(src_ref)
                seen_citations.add(citation)

            content_blocks.append(
                ContentBlock(
                    block_id=f"code_{file_id[:8]}_sym_{idx}_{sym_name}",
                    content=snippet,
                    block_type="code",
                    source_reference=src_ref,
                    token_estimate=max(1, len(snippet.split())),
                    metadata={
                        "language": language,
                        "symbol_name": sym_name,
                        "symbol_kind": sym_kind,
                        "start_line": start_line,
                        "end_line": end_line,
                    },
                )
            )

        # 2. Imports and dependencies
        imports = code_dict.get("imports", [])
        if imports:
            import_lines = []
            for imp in imports:
                mod = imp.get("module") or imp.get("name") or ""
                names = imp.get("imported_names") or []
                if names:
                    import_lines.append(f"from {mod} import {', '.join(names)}")
                elif mod:
                    import_lines.append(f"import {mod}")
            if import_lines:
                imports_text = "\n".join(import_lines)
                citation = f"{filename} — Imports"
                full_text_parts.append(imports_text)

                src_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="code",
                    formatted_citation=citation,
                    line_start=1,
                    line_end=min(len(import_lines), 50),
                    metadata={"section": "imports"},
                )
                if citation not in seen_citations:
                    source_refs.append(src_ref)
                    seen_citations.add(citation)

                content_blocks.append(
                    ContentBlock(
                        block_id=f"code_{file_id[:8]}_imports",
                        content=imports_text,
                        block_type="code",
                        source_reference=src_ref,
                        token_estimate=max(1, len(imports_text.split())),
                        metadata={"language": language, "type": "imports"},
                    )
                )

        # 3. Fallback: If no symbols were extracted, chunk the source code by line windows (e.g. 50 lines)
        if not content_blocks and source_code.strip():
            window_size = 60
            for start_idx in range(0, len(lines), window_size):
                chunk_lines = lines[start_idx : start_idx + window_size]
                chunk_text = "\n".join(chunk_lines)
                if not chunk_text.strip():
                    continue

                line_start = start_idx + 1
                line_end = start_idx + len(chunk_lines)
                citation = f"{filename} — Lines {line_start}–{line_end}"
                full_text_parts.append(chunk_text)

                src_ref = SourceReference(
                    source_file_id=file_id,
                    original_filename=filename,
                    source_type="code",
                    formatted_citation=citation,
                    line_start=line_start,
                    line_end=line_end,
                )
                if citation not in seen_citations:
                    source_refs.append(src_ref)
                    seen_citations.add(citation)

                content_blocks.append(
                    ContentBlock(
                        block_id=f"code_{file_id[:8]}_lines_{line_start}_{line_end}",
                        content=chunk_text,
                        block_type="code",
                        source_reference=src_ref,
                        token_estimate=max(1, len(chunk_text.split())),
                        metadata={"language": language, "line_start": line_start, "line_end": line_end},
                    )
                )

        # 4. Metrics overview block
        metrics = code_dict.get("metrics") or {}
        tot_lines = metrics.get("total_lines") or len(lines)
        code_lines = metrics.get("code_lines") or tot_lines
        overview_text = (
            f"Code File: {filename} (Language: {language}, Total Lines: {tot_lines}, "
            f"Code Lines: {code_lines}, Symbols: {len(symbols)})"
        )
        full_text_parts.append(overview_text)

        src_ref = SourceReference(
            source_file_id=file_id,
            original_filename=filename,
            source_type="code",
            formatted_citation=f"{filename} — Overview",
        )
        source_refs.append(src_ref)
        content_blocks.append(
            ContentBlock(
                block_id=f"code_{file_id[:8]}_meta",
                content=overview_text,
                block_type="metadata",
                source_reference=src_ref,
                token_estimate=max(1, len(overview_text.split())),
                metadata={"metrics": metrics, "language": language},
            )
        )

        combined_text = "\n".join(full_text_parts)
        content_hash = compute_content_hash(combined_text)

        return KnowledgeDocument(
            knowledge_document_id=f"kd_code_{file_id[:8]}",
            source_file_id=file_id,
            parent_archive_id=parent_archive_id,
            source_type="code",
            content_type=language,
            title=filename,
            content_blocks=content_blocks,
            metadata={
                "language": language,
                "total_lines": tot_lines,
                "symbol_count": len(symbols),
                "metrics": metrics,
            },
            source_references=source_refs,
            extraction_status="completed",
            language=language,
            content_hash=content_hash,
            processing_version="1.0.0",
            created_at=datetime.now(UTC).isoformat(),
        )
