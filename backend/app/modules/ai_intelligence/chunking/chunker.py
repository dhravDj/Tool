"""Modular Chunking Engine for Cross-Format Content.

Supports structure-aware, table-aware, code-aware, and timestamp-aware
token-bounded chunking with precise source references.
"""

import hashlib
import re
from typing import Any

from app.modules.ai_intelligence.schemas.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    SourceReference,
)


def _approx_token_count(text: str) -> int:
    """Fast approximation of token count based on whitespace and punctuation tokens."""
    if not text:
        return 0
    # Average ~0.75 words per token (1 word ~ 1.33 tokens)
    words = len(text.split())
    return max(1, int(words * 1.3))


def _split_into_token_windows(text: str, max_tokens: int = 500, overlap_tokens: int = 50) -> list[str]:
    """Splits a long text string into overlapping token windows along sentence or line boundaries."""
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        s_tokens = _approx_token_count(sentence)
        if current_tokens + s_tokens > max_tokens and current_sentences:
            chunks.append(" ".join(current_sentences).strip())
            # Retain overlap sentences
            overlap_sentences: list[str] = []
            overlap_count = 0
            for s in reversed(current_sentences):
                st = _approx_token_count(s)
                if overlap_count + st <= overlap_tokens:
                    overlap_sentences.insert(0, s)
                    overlap_count += st
                else:
                    break
            current_sentences = overlap_sentences
            current_tokens = overlap_count

        current_sentences.append(sentence)
        current_tokens += s_tokens

    if current_sentences:
        chunks.append(" ".join(current_sentences).strip())

    return chunks if chunks else [text]


class ChunkingEngine:
    """Splits a KnowledgeDocument's semantic blocks into searchable KnowledgeChunks."""

    def __init__(
        self,
        target_chunk_tokens: int = 400,
        max_chunk_tokens: int = 600,
        overlap_tokens: int = 60,
    ) -> None:
        self.target_chunk_tokens = target_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_document(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        """Processes all content blocks in the document and produces indexed KnowledgeChunks."""
        chunks: list[KnowledgeChunk] = []
        chunk_idx = 0

        # Group sequential small blocks of same source/page where applicable
        current_text_buf: list[str] = []
        current_tokens = 0
        current_ref: SourceReference | None = None
        current_block_type: str = "text"
        current_meta: dict[str, Any] = {}

        def flush_buffer() -> None:
            nonlocal chunk_idx, current_text_buf, current_tokens, current_ref, current_block_type, current_meta
            if not current_text_buf or current_ref is None:
                return

            full_chunk_text = "\n\n".join(current_text_buf).strip()
            if not full_chunk_text:
                current_text_buf = []
                current_tokens = 0
                return

            ch_hash = hashlib.sha256(full_chunk_text.encode("utf-8")).hexdigest()
            chunk_id = f"chk_{document.source_file_id[:8]}_{chunk_idx:04d}"

            chunks.append(
                KnowledgeChunk(
                    chunk_id=chunk_id,
                    knowledge_document_id=document.knowledge_document_id,
                    source_file_id=document.source_file_id,
                    chunk_index=chunk_idx,
                    content=full_chunk_text,
                    token_count=current_tokens,
                    source_reference=current_ref,
                    embedding_status="pending",
                    content_hash=ch_hash,
                    metadata={
                        **current_meta,
                        "block_type": current_block_type,
                        "title": document.title,
                        "source_type": document.source_type,
                    },
                )
            )
            chunk_idx += 1
            current_text_buf = []
            current_tokens = 0

        for block in document.content_blocks:
            b_tokens = block.token_estimate or _approx_token_count(block.content)
            b_type = block.block_type

            # If the block itself is already very large (exceeds max_chunk_tokens)
            if b_tokens > self.max_chunk_tokens:
                # Flush existing buffer first
                flush_buffer()

                # Split this large block into sub-chunks
                sub_chunks = _split_into_token_windows(
                    block.content,
                    max_tokens=self.target_chunk_tokens,
                    overlap_tokens=self.overlap_tokens,
                )
                for sub_idx, sub_text in enumerate(sub_chunks):
                    sub_hash = hashlib.sha256(sub_text.encode("utf-8")).hexdigest()
                    c_id = f"chk_{document.source_file_id[:8]}_{chunk_idx:04d}"
                    sub_t_count = _approx_token_count(sub_text)

                    # Augment citation if multi-part
                    augmented_ref = block.source_reference.model_copy()
                    if len(sub_chunks) > 1:
                        augmented_ref.formatted_citation = (
                            f"{block.source_reference.formatted_citation} (Part {sub_idx + 1}/{len(sub_chunks)})"
                        )

                    chunks.append(
                        KnowledgeChunk(
                            chunk_id=c_id,
                            knowledge_document_id=document.knowledge_document_id,
                            source_file_id=document.source_file_id,
                            chunk_index=chunk_idx,
                            content=sub_text,
                            token_count=sub_t_count,
                            source_reference=augmented_ref,
                            embedding_status="pending",
                            content_hash=sub_hash,
                            metadata={
                                **block.metadata,
                                "block_type": b_type,
                                "title": document.title,
                                "source_type": document.source_type,
                                "split_part": sub_idx + 1,
                            },
                        )
                    )
                    chunk_idx += 1
                continue

            # Check if block can be combined with current buffer
            # Do NOT combine across pages, slides, sheets, or different structural types
            locators_match = False
            if current_ref is not None:
                if current_ref.page_number is not None and block.source_reference.page_number is not None:
                    locators_match = (current_ref.page_number == block.source_reference.page_number)
                elif current_ref.slide_number is not None and block.source_reference.slide_number is not None:
                    locators_match = (current_ref.slide_number == block.source_reference.slide_number)
                elif current_ref.sheet_name is not None and block.source_reference.sheet_name is not None:
                    locators_match = (current_ref.sheet_name == block.source_reference.sheet_name)
                elif (
                    current_ref.page_number is None
                    and current_ref.slide_number is None
                    and current_ref.sheet_name is None
                ):
                    locators_match = True

            is_compatible = (
                current_ref is not None
                and current_block_type == b_type
                and locators_match
                and (current_tokens + b_tokens <= self.target_chunk_tokens)
            )

            if is_compatible:
                current_text_buf.append(block.content)
                current_tokens += b_tokens
            else:
                flush_buffer()
                current_text_buf = [block.content]
                current_tokens = b_tokens
                current_ref = block.source_reference
                current_block_type = b_type
                current_meta = block.metadata

        flush_buffer()
        return chunks


chunking_engine = ChunkingEngine()
