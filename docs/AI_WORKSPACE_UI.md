# DocuMind AI — AI Workspace & Hybrid Search UI (Phase 13)

## 1. Overview

The AI capabilities implemented in Phase 11 are surfaced through dedicated UI interfaces designed for transparency, citations, and model flexibility:

1. **AI Conversational Workspace** (`frontend/src/components/ai/AIWorkspace.tsx`, route `/ai`)
2. **Knowledge Search** (`frontend/src/pages/KnowledgeSearchPage.tsx`, route `/search`)
3. **AI Settings & Consent Panel** (`frontend/src/components/ai/AISettingsView.tsx`, accessible in `/settings`)

---

## 2. AI Workspace Interface

The AI Workspace provides an enterprise conversational knowledge assistant grounded in user files:

### 2.1 Multi-Model Provider Selector
Users can toggle between supported LLM providers:
- **OpenAI**: GPT-4o, GPT-4o-mini
- **Anthropic**: Claude 3.5 Sonnet, Claude 3.5 Haiku
- **Google Gemini**: Gemini 1.5 Pro, Gemini 1.5 Flash
- **Local / Self-Hosted**: Ollama, vLLM, HuggingFace embeddings

### 2.2 Grounding Scope Control
Users can switch conversational context between:
- **Global Knowledge Base**: Indexes and retrieves evidence across all processed files in the library.
- **Specific File Scope**: Confines grounding to a single file (pre-selected when opened from the Universal File Inspector).

### 2.3 Transparent Citation Rendering
Responses from the LLM are rendered with interactive citation markers (e.g. `[1]`, `[2]`). Clicking a marker opens a drawer showing:
- Source file name and format badge.
- Exact extracted text snippet / bounding box.
- Reciprocal Rank Fusion relevance score.
- Deep link to view the file in the Universal File Inspector.

---

## 3. Hybrid Search Interface (`/search`)

The Knowledge Search view provides a search engine interface powered by hybrid retrieval:
- **BM25 Lexical Matching**: Precision matching for exact keywords, code identifiers, filenames, and numbers.
- **Dense Vector Cosine Similarity**: Semantic understanding across conceptual inquiries.
- **Reciprocal Rank Fusion (RRF)**: Merges ranked lists into a unified score with zero manual tuning.
- **Interactive Result Cards**: Highlighting matched phrases, source document metadata, and direct download links.

---

## 4. Privacy & Consent Governance

In compliance with enterprise privacy standards:
- External model API calls require explicit tenant opt-in.
- Prompts never leak PII or cross tenant isolation boundaries.
- Local embeddings and vector storage ensure data stays within the platform perimeter.
