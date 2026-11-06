"""Google Gemini Cloud LLM Provider with strict privacy consent enforcement."""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.modules.ai_intelligence.llm.base import BaseLLMProvider
from app.modules.ai_intelligence.schemas.chat import Citation
from app.modules.ai_intelligence.schemas.knowledge import SourceReference

logger = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider. Requires explicit user consent and API key."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.5-flash",
        user_consent: bool = False,
    ) -> None:
        self._api_key = api_key
        self._model = model_name
        self._user_consent = user_consent

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def _verify_consent_and_key(self) -> None:
        if not self._user_consent:
            raise PermissionError(
                "Explicit user consent is required before transmitting file content or queries to cloud AI services."
            )
        if not self._api_key or not self._api_key.strip():
            raise ValueError("A valid Google Gemini API key is required.")

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
            f"Instructions: Answer using ONLY the provided context. Cite sources with [1], [2], etc. "
            f"If the context does not contain enough information, state that clearly."
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
        self._verify_consent_and_key()
        augmented_prompt = self._build_context_prompt(prompt, context_chunks)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": augmented_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return "No response generated.", [], 0
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
                citations = self._extract_citations(text, context_chunks)
                token_count = data.get("usageMetadata", {}).get("totalTokenCount", max(1, len(text.split()) * 2))
                return text, citations, token_count
        except Exception as e:
            logger.error(f"Gemini generateContent error: {e}")
            raise RuntimeError(f"Gemini API error: {e}") from e

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context_chunks: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        self._verify_consent_and_key()
        augmented_prompt = self._build_context_prompt(prompt, context_chunks)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:streamGenerateContent?alt=sse&key={self._api_key}"
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": augmented_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=45.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    json_str = line[6:]
                    try:
                        data = json.loads(json_str)
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for p in parts:
                                txt = p.get("text", "")
                                if txt:
                                    yield txt
                    except Exception:
                        pass
