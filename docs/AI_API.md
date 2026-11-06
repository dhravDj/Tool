# Universal AI Intelligence REST API Specification (Phase 11)

All endpoints are mounted under the base path `/api/v1/ai`.

## 1. Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/capabilities` | Returns supported providers, models, modalities, and features |
| `GET` | `/providers` | Lists active AI providers and connectivity status |
| `POST` | `/index/{file_id}` | Normalizes, chunks, embeds, and indexes a file |
| `GET` | `/index/{file_id}/status` | Checks indexing status and chunk count of a file |
| `POST` | `/search` | Executes keyword, vector, or hybrid search with filters |
| `POST` | `/chat` | Single/multi-turn grounded RAG chat with verified citations |
| `POST` | `/chat/stream` | Server-Sent Events (SSE) token and citation streaming |
| `GET` | `/conversations` | Lists stored multi-turn conversation sessions |
| `GET` | `/conversations/{id}` | Retrieves full message history and citations of a conversation |
| `DELETE` | `/conversations/{id}` | Deletes a conversation session and message records |
| `POST` | `/summarize` | Generates 7 styles of citation-grounded file summaries |
| `POST` | `/compare` | Multi-file comparison matrix and contradiction detector |
| `POST` | `/extract-structured` | Extracts validated JSON schema entities with citations |
| `GET` | `/settings` | Returns active provider configurations and cloud consents |
| `PUT` | `/settings` | Updates active provider, model selections, and cloud consents |

---

## 2. Selected Request & Response Schemas

### `POST /api/v1/ai/index/{file_id}`
Triggers knowledge extraction, normalization across modalities, modular chunking, and vector embedding.

**Query Parameters:**
- `force` (bool, optional, default: false): Reindex even if previously indexed.
- `embedder` (string, optional, default: "sovereign"): Embedding provider to use (`sovereign`, `ollama`, `gemini`).

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "file_id": "7cdf420a-a117-451b-8585-1c103d10ac8e",
    "document_id": "kd_doc_7cdf420a",
    "source_type": "document",
    "total_blocks": 4,
    "total_chunks": 2,
    "status": "indexed"
  },
  "error": null
}
```

---

### `POST /api/v1/ai/search`
Searches knowledge chunks across all indexed files using BM25, Cosine Semantic Vector, or Hybrid Reciprocal Rank Fusion (RRF).

**Request Body:**
```json
{
  "query": "annual net revenue and gross margin",
  "search_mode": "hybrid",
  "top_k": 5,
  "filters": {
    "file_ids": ["7cdf420a-a117-451b-8585-1c103d10ac8e"],
    "source_types": ["document", "spreadsheet"]
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "query": "annual net revenue and gross margin",
    "search_mode": "hybrid",
    "total_hits": 1,
    "hits": [
      {
        "chunk_id": "chunk_kd_doc_7cdf420a_0",
        "file_id": "7cdf420a-a117-451b-8585-1c103d10ac8e",
        "filename": "orion_report.txt",
        "source_type": "document",
        "content": "Project Orion Financial Report 2026. Total company revenue reached $15.5 million with a gross margin of 68%.",
        "score": 0.01639,
        "citation": {
          "citation_id": "[1]",
          "file_id": "7cdf420a-a117-451b-8585-1c103d10ac8e",
          "filename": "orion_report.txt",
          "source_type": "document",
          "formatted_citation": "orion_report.txt — Page 1",
          "snippet": "Project Orion Financial Report 2026...",
          "page_number": 1
        }
      }
    ],
    "execution_time_ms": 1.42
  }
}
```

---

### `POST /api/v1/ai/chat`
Performs single-turn or multi-turn grounded RAG chat. Returns strict provenance citations.

**Request Body:**
```json
{
  "message": "What was the company's net revenue and margin in 2026?",
  "conversation_id": null,
  "file_ids": ["7cdf420a-a117-451b-8585-1c103d10ac8e"],
  "provider": "sovereign",
  "temperature": 0.1
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "conversation_id": "426be640-ee98-444b-9721-a39281e8cb85",
    "message": {
      "role": "assistant",
      "content": "Based on the documented findings:\n\nProject Orion Financial Report 2026. Total company revenue reached $15.5 million with a gross margin of 68%. [1]"
    },
    "citations": [
      {
        "citation_id": "[1]",
        "file_id": "7cdf420a-a117-451b-8585-1c103d10ac8e",
        "filename": "orion_report.txt",
        "source_type": "document",
        "formatted_citation": "orion_report.txt — Page 1",
        "snippet": "Project Orion Financial Report 2026. Total company revenue reached $15.5 million with a gross margin of 68%.",
        "page_number": 1
      }
    ],
    "model_name": "documind-sovereign-llm-v1",
    "provider": "sovereign",
    "tokens_used": 42,
    "latency_ms": 3.8
  }
}
```

---

### `POST /api/v1/ai/compare`
Compares two or more files across dimensions, constructs a comparative matrix, and detects conflicting assertions.

**Request Body:**
```json
{
  "file_ids": [
    "7cdf420a-a117-451b-8585-1c103d10ac8e",
    "8ab3120b-2234-451b-9090-2c103d10ac9f"
  ],
  "comparison_aspects": ["revenue", "costs", "margins"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "compared_files": ["orion_report.txt", "audit_reconciliation.pdf"],
    "comparison_matrix": {
      "revenue": {
        "orion_report.txt": "$15.5 million",
        "audit_reconciliation.pdf": "$12.8 million"
      }
    },
    "contradictions": [
      {
        "topic": "revenue",
        "file_a": "orion_report.txt",
        "assertion_a": "Total company revenue reached $15.5 million",
        "citation_a": "orion_report.txt — Page 1",
        "file_b": "audit_reconciliation.pdf",
        "assertion_b": "Recalculated revenue was $12.8 million",
        "citation_b": "audit_reconciliation.pdf — Page 4"
      }
    ],
    "synthesis": "Discrepancy identified between reported revenue ($15.5M) and reconciled audit ($12.8M)."
  }
}
```
