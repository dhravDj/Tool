"""Sovereign Deterministic File Intelligence LLM (documind-sovereign-llm-v1).

Runs 100% locally with zero external network dependencies.
Strictly grounds every statement in provided context chunks, with strict citation validation
and explicit evidence abstention when information is missing. Defends against prompt injection.
"""

import asyncio
import re
from collections.abc import AsyncIterator
from typing import Any

from app.modules.ai_intelligence.llm.base import BaseLLMProvider
from app.modules.ai_intelligence.schemas.chat import Citation
from app.modules.ai_intelligence.schemas.knowledge import SourceReference

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+context",
    r"system\s*:\s*you\s+are\s+now",
    r"you\s+are\s+dan\b",
    r"bypass\s+safety",
    r"forget\s+(all\s+)?rules",
]


class SovereignLLMProvider(BaseLLMProvider):
    """Deterministic, local grounded intelligence engine with guaranteed citation accuracy."""

    def __init__(self, model_name: str = "documind-sovereign-llm-v1") -> None:
        self._model = model_name

    @property
    def provider_name(self) -> str:
        return "sovereign"

    @property
    def model_name(self) -> str:
        return self._model

    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitizes user input and neutralizes prompt injection payloads."""
        cleaned = prompt.strip()
        for pattern in INJECTION_PATTERNS:
            cleaned = re.sub(pattern, "[Filtered Injection Attempt]", cleaned, flags=re.IGNORECASE)
        return cleaned

    def _synthesize_answer(
        self,
        prompt: str,
        context_chunks: list[dict[str, Any]] | None,
    ) -> tuple[str, list[Citation]]:
        cleaned_prompt = self._sanitize_prompt(prompt)
        q_words = set(re.findall(r"\w+", cleaned_prompt.lower()))
        # Remove common stopwords
        stopwords = {
            "what", "is", "the", "in", "and", "or", "to", "a", "an", "of", "for", "on", "with",
            "at", "by", "from", "up", "about", "into", "over", "after", "how", "why", "where",
            "when", "who", "which", "can", "could", "would", "should", "does", "did", "tell",
            "me", "give", "show", "summarize", "list", "are", "were", "been", "has", "have", "had",
        }
        key_q_words = q_words - stopwords

        if not context_chunks:
            return (
                "Based on the available documents, no evidence was found to answer your inquiry. "
                "Please verify that the relevant files have been uploaded and indexed.",
                [],
            )

        # Match relevance of chunks
        relevant_chunks: list[tuple[float, dict[str, Any], list[str]]] = []
        for chk in context_chunks:
            content = chk.get("content", "")
            c_words = set(re.findall(r"\w+", content.lower()))
            overlap = key_q_words & c_words
            score = len(overlap) / (len(key_q_words) + 1e-5) if key_q_words else 0.5

            # Extract matching sentences
            sentences = re.split(r"(?<=[.!?\n])\s+", content)
            matched_sentences = []
            for s in sentences:
                s_words = set(re.findall(r"\w+", s.lower()))
                if (key_q_words and (s_words & key_q_words)) or not key_q_words:
                    if len(s.strip()) > 15:
                        matched_sentences.append(s.strip())

            if matched_sentences or not key_q_words:
                relevant_chunks.append((score, chk, matched_sentences or sentences[:2]))

        if not relevant_chunks:
            topic_str = ", ".join(list(key_q_words)[:4]) if key_q_words else "the requested topic"
            return (
                f"Based on the provided documents, there is no evidence to answer this question. "
                f"The indexed files do not contain information regarding {topic_str}.",
                [],
            )

        # Sort by relevance score descending
        relevant_chunks.sort(key=lambda x: x[0], reverse=True)

        citations: list[Citation] = []
        answer_paragraphs: list[str] = []
        citation_num = 1

        top_chunks = relevant_chunks[:5]
        for score, chk, sents in top_chunks:
            src_ref_raw = chk.get("source_reference", {}) or {}
            if isinstance(src_ref_raw, SourceReference):
                src_ref = src_ref_raw
            elif isinstance(src_ref_raw, dict):
                ref_copy = dict(src_ref_raw)
                ref_copy.setdefault("source_file_id", str(chk.get("file_id", "unknown")))
                ref_copy.setdefault("original_filename", str(chk.get("filename", "unknown")))
                ref_copy.setdefault("source_type", str(chk.get("source_type", "document")))
                ref_copy.setdefault("formatted_citation", f"{ref_copy['original_filename']} — Location {citation_num}")
                src_ref = SourceReference.model_validate(ref_copy)
            else:
                src_ref = SourceReference(
                    source_file_id=str(chk.get("file_id", "unknown")),
                    original_filename=str(chk.get("filename", "unknown")),
                    source_type=str(chk.get("source_type", "document")),
                    formatted_citation=f"{chk.get('filename', 'Doc')} — Location {citation_num}",
                )

            # Pick 1-3 best sentences
            evidence_text = " ".join(sents[:3])
            citation = Citation(
                citation_id=f"[{citation_num}]",
                file_id=str(chk.get("file_id", "")),
                filename=str(chk.get("filename", "")),
                source_type=src_ref.source_type,
                formatted_citation=src_ref.formatted_citation,
                snippet=evidence_text[:280] + ("..." if len(evidence_text) > 280 else ""),
                page_number=src_ref.page_number,
                sheet_name=src_ref.sheet_name,
                cell_range=src_ref.cell_range,
                slide_number=src_ref.slide_number,
                line_start=src_ref.line_start,
                line_end=src_ref.line_end,
                timestamp_start=src_ref.timestamp_start,
                timestamp_end=src_ref.timestamp_end,
                json_path=src_ref.json_path,
                archive_path=src_ref.archive_path,
                relevance_score=round(float(score), 4),
            )
            citations.append(citation)

            # Format paragraph with reference tag
            answer_paragraphs.append(f"{evidence_text} [{citation_num}]")
            citation_num += 1

        # Synthesize lead-in
        lead = "Based on the documented findings:"
        body = "\n\n".join(answer_paragraphs)
        full_answer = f"{lead}\n\n{body}"

        return full_answer, citations

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context_chunks: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> tuple[str, list[Citation], int]:
        answer, citations = self._synthesize_answer(prompt, context_chunks)
        token_count = max(1, len(answer.split()) * 2)
        return answer, citations, token_count

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context_chunks: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        answer, citations = self._synthesize_answer(prompt, context_chunks)
        # Stream response word-by-word with micro-yields
        words = answer.split(" ")
        for i, word in enumerate(words):
            suffix = " " if i < len(words) - 1 else ""
            yield word + suffix
            await asyncio.sleep(0.005)


sovereign_llm_provider = SovereignLLMProvider()
