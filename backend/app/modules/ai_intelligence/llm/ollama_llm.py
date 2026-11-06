"""Ollama Local LLM Provider for DocuMind AI (Phase 11)."""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.modules.ai_intelligence.llm.base import BaseLLMProvider
from app.modules.ai_intelligence.llm.sovereign_llm import sovereign_llm_provider
from app.modules.ai_intelligence.schemas.chat import Citation
from app.modules.ai_intelligence.schemas.knowledge import SourceReference

logger = logging.getLogger(__name__)


class OllamaLLMProvider(BaseLLMProvider):
    """Local Ollama-backed LLM provider (e.g. llama3.2, mistral, qwen2.5)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3.2",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model_name

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def _build_context_prompt(self, prompt: str, context_chunks: list[dict[str, Any]] | None) -> str:
        if not context_chunks:
            return prompt

        context_lines = []
        for i, chk in enumerate(context_chunks, start=1):
            src_ref = chk.get("source_reference", {})
            loc = src_ref.get("formatted_citation") or f"Source {i}"
            content = chk.get("content", "")
            context_lines.append(f"[{i}] ({loc}):\n{content}")

        context_str = "\n\n".join(context_lines)
        return (
            f"Context Information from Documents:\n{context_str}\n\n"
            f"User Question: {prompt}\n\n"
            f"Instructions: Answer the question using ONLY the provided context. "
            f"Cite sources using [1], [2], etc. If the context does not contain enough information, "
            f"state clearly that the documents do not have sufficient evidence."
        )

    def _extract_citations(
        self,
        text: str,
        context_chunks: list[dict[str, Any]] | None,
    ) -> list[Citation]:
        if not context_chunks:
            return []

        citations: list[Citation] = []
        for i, chk in enumerate(context_chunks, start=1):
            # If cited in text e.g. [1] or if top evidence
            tag = f"[{i}]"
            if tag in text or i <= 3:
                src_ref_raw = chk.get("source_reference", {}) or {}
                if isinstance(src_ref_raw, SourceReference):
                    src_ref = src_ref_raw
                elif isinstance(src_ref_raw, dict):
                    ref_copy = dict(src_ref_raw)
                    ref_copy.setdefault("source_file_id", str(chk.get("file_id", "unknown")))
                    ref_copy.setdefault("original_filename", str(chk.get("filename", "unknown")))
                    ref_copy.setdefault("source_type", str(chk.get("source_type", "document")))
                    ref_copy.setdefault("formatted_citation", f"{ref_copy['original_filename']} — [{i}]")
                    src_ref = SourceReference.model_validate(ref_copy)
                else:
                    src_ref = SourceReference(
                        source_file_id=str(chk.get("file_id", "unknown")),
                        original_filename=str(chk.get("filename", "unknown")),
                        source_type=str(chk.get("source_type", "document")),
                        formatted_citation=f"{chk.get('filename', 'Doc')} — [{i}]",
                    )
                citations.append(
                    Citation(
                        citation_id=f"[{i}]",
                        file_id=str(chk.get("file_id", "")),
                        filename=str(chk.get("filename", "")),
                        source_type=src_ref.source_type,
                        formatted_citation=src_ref.formatted_citation,
                        snippet=chk.get("content", "")[:280],
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
                    )
                )
        return citations

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context_chunks: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> tuple[str, list[Citation], int]:
        augmented_prompt = self._build_context_prompt(prompt, context_chunks)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": augmented_prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self._base_url}/api/chat", json=payload)
                res.raise_for_status()
                data = res.json()
                content = data.get("message", {}).get("content", "")
                token_count = data.get("eval_count", max(1, len(content.split()) * 2))
                citations = self._extract_citations(content, context_chunks)
                return content, citations, token_count
        except Exception as e:
            logger.warning(f"Ollama chat generation failed ({e}), falling back to Sovereign provider.")
            return await sovereign_llm_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                context_chunks=context_chunks,
                temperature=temperature,
                max_tokens=max_tokens,
            )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context_chunks: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        augmented_prompt = self._build_context_prompt(prompt, context_chunks)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": augmented_prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk_obj = json.loads(line)
                        piece = chunk_obj.get("message", {}).get("content", "")
                        if piece:
                            yield piece
        except Exception as e:
            logger.warning(f"Ollama stream failed ({e}), falling back to Sovereign stream.")
            async for token in sovereign_llm_provider.generate_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                context_chunks=context_chunks,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield token
