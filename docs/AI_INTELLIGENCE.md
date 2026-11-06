# Phase 11: Universal AI Intelligence Engine Architecture

## 1. Overview
The **Universal AI Intelligence Engine** transforms DocuMind AI from a file extraction and processing platform into an AI-powered knowledge and file intelligence platform. It unifies all previous modalities (Phases 1–10: Documents, Images, Spreadsheets, Presentations, Audio, Video, Code, Structured Data, Archives) into a normalized knowledge representation that enables:

- **Modality-Agnostic Knowledge Representation**: Normalizes extraction artifacts from all 9 modalities into canonical `KnowledgeDocument`, `ContentBlock`, and `SourceReference` structures.
- **Modular Semantic Chunking**: Chunking engine aware of structure, tokens, tables, slides, code boundaries, audio/video timestamps, and JSON paths. Guarantees citation boundaries are never lost across chunks.
- **Provider-Independent Embedding & Model Router**: Deterministic local 384-dimensional embedder (`documind-fast-embed-384`), local Ollama (`nomic-embed-text`), and cloud Google Gemini (`text-embedding-004`).
- **Hybrid Search Engine (BM25 + Dense Vector + RRF)**: Combines keyword term-frequency ranking and dense cosine similarity using Reciprocal Rank Fusion ($k=60$). Fully functional even when offline without LLM connectivity.
- **Zero-Hallucination Sovereign RAG**: Grounded generation engine with strict provenance enforcement, multi-source citations, prompt injection filtering, and explicit evidence abstention when context is insufficient.
- **Multi-Type AI Summarization**: Seven purpose-built summary styles (short, detailed, executive, bullet, technical, section-wise, key findings).
- **Cross-File Comparative Intelligence**: Alignment matrices, side-by-side metric comparison, and automatic contradiction detection across conflicting documents.
- **Typed Structured Extraction**: Validated entity, date, metric, and relationship extraction with citations.

---

## 2. Universal Content Normalization Architecture

```
                                  Extraction Artifacts (Phases 1–10)
                                                 │
          ┌──────────────┬──────────────┬────────┼──────────────┬──────────────┐
          ▼              ▼              ▼        ▼              ▼              ▼
     Documents        Images       Sheets     Slides        Audio / Video    Code / Data
      (PDF, DOCX)   (OCR/Vision)    (XLSX)    (PPTX)         (Whisper/FF)    (AST, JSON)
          │              │              │        │              │              │
          └──────────────┴──────────────┼────────┴──────────────┴──────────────┘
                                        ▼
                            ContentAdapterRegistry
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                 KnowledgeDocument             SourceReference
               - knowledge_document_id       - source_file_id
               - source_type                 - original_filename
               - content_type                - formatted_citation
               - content_blocks:             - page_number
                 * block_id                  - sheet_name / cell_range
                 * content                   - slide_number
                 * block_type                - timestamp_start / end
                 * source_reference          - line_start / line_end
                 * token_estimate            - json_path / archive_path
```

### Modality Adapters
1. **DocumentContentAdapter**: Adapts Phase 3 canonical documents with page numbers, paragraph indices, and bounding boxes.
2. **ImageContentAdapter**: Adapts Phase 4 OCR tokens, image classifications, and visual scene descriptions.
3. **SpreadsheetContentAdapter**: Preserves sheet names, cell ranges (e.g. `Cells B2:F12`), row formulas, and table structures.
4. **PresentationContentAdapter**: Preserves slide indices, speaker notes, and presentation shapes.
5. **AudioContentAdapter**: Preserves speaker IDs and precise timestamp intervals (`00:02:14–00:02:31`).
6. **VideoContentAdapter**: Preserves scene timestamps, visual descriptions, and transcribed speech segments.
7. **CodeContentAdapter**: Preserves line numbers (`Lines 25–42`), functions, classes, and AST diagnostic symbols.
8. **StructuredDataContentAdapter**: Preserves JSON paths (`$.database.credentials.host`), table records, and schema profiles.
9. **ArchiveContentAdapter**: Preserves archive relative entry paths (`docs/architecture/spec.md`) and unpacked hierarchies.

---

## 3. Modular Chunking Engine

The chunking engine (`ChunkingEngine`) partitions `ContentBlock` sequences into searchable, bounded `KnowledgeChunk` fragments.

### Core Invariants:
- **Token Budget**: Target 400 tokens, hard limit 600 tokens, 60 token sliding overlap.
- **Provenance Preservation**: Chunks inherit exact `SourceReference` locators from their constituent blocks.
- **Locator Boundary Protection**: Blocks originating from different physical pages, different spreadsheet sheets, different presentation slides, or different source files are **never** merged into the same chunk.
- **Table & Code Integrity**: Tabular rows and code blocks preserve semantic structure with language and sheet context headers.

---

## 4. Embedding Engine & Search Pipeline

### Embedding Options
- **Sovereign Embedder**: Fast, deterministic local embedder producing 384-dimensional unit-normalized vectors ($L_2 = 1.0 \pm 10^{-4}$) at $>40,000$ tokens/sec on CPU. Zero network calls or external dependencies.
- **Ollama Embedder**: Local LLM daemon integration via REST (`/api/embeddings`) supporting `nomic-embed-text`, `bge-m3`, `all-minilm`.
- **Google Gemini Embedder**: Cloud vector generation (`text-embedding-004`) requiring explicit user consent in compliance with data privacy policies.

### Hybrid Retrieval & Reciprocal Rank Fusion (RRF)
```
                      User Search Query
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       Keyword Engine (BM25)       Dense Vector Engine (NumPy)
       - Token matching            - Cosine similarity
       - Term frequency weighting  - Batch dot product
               │                             │
        Ranked List 1                 Ranked List 2
               │                             │
               └──────────────┬──────────────┘
                              ▼
                  Reciprocal Rank Fusion
               RRF_Score = ∑ 1.0 / (60 + rank)
                              │
                              ▼
                   Top-K Grounded Chunks
```

Search operations operate independently from LLM generation. When an LLM is offline or unconfigured, hybrid search remains 100% operational.

---

## 5. Sovereign RAG & Grounded Synthesis

The Sovereign LLM engine (`documind-sovereign-llm-v1`) provides offline, hallucination-free generation:

- **Strict Evidence Grounding**: The engine extracts verbatim and closely aligned sentences from retrieved evidence chunks.
- **Prompt Injection Defense**: Sanitizes adversarial system prompts, role switching, jailbreak vectors, and context overriding attempts before synthesis.
- **Explicit Evidence Abstention**: If retrieved chunks do not contain verified answers or relevance scores fall below confidence thresholds, the system explicitly abstains:
  > *"Based on the provided documents, there is no evidence to answer this question. The indexed documents do not contain information regarding [Topic]."*
- **Exact Provenance Citations**: Every generated finding or assertion is linked to an exact `Citation` record containing file name, page number, slide number, cell range, timestamp, line number, or JSON path. Citations are never fabricated or guessed.
