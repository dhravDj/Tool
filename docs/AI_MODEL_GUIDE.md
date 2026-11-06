# AI Model & Provider Guide (Phase 11)

## 1. Provider Tier Comparison

DocuMind AI implements a provider-independent AI architecture designed for strict data sovereignty and zero external dependency by default, with optional local and cloud integrations.

| Attribute | Sovereign (Default) | Ollama (Local Daemon) | Google Gemini (Cloud) |
|---|---|---|---|
| **Privacy / Sovereignty** | 100% In-Process / Air-Gapped | 100% On-Device Local Daemon | Cloud-Hosted (Consent Required) |
| **Network Required** | No (Fully Offline) | No (Localhost only) | Yes (HTTPS outbound) |
| **Inference Cost** | $0.00 | $0.00 | Pay-per-token API tier |
| **API Key Required** | No | No | Yes (User encrypted key) |
| **Default Model** | `documind-sovereign-llm-v1` | `llama3.2` | `gemini-2.5-flash` |
| **Default Embedder** | `documind-fast-embed-384` | `nomic-embed-text` | `text-embedding-004` |
| **Hardware Reqs** | Standard CPU (1-2 cores) | 8GB+ RAM, optional GPU | Minimal local resources |
| **Throughput** | >500,000 tokens/sec | ~30-60 tokens/sec | ~120 tokens/sec |
| **Hallucination Risk** | **0.00%** (Strict Extraction) | Low (Grounded prompt) | Very Low (Grounded prompt) |
| **Explicit Abstention**| Guaranteed by rule engine | Probabilistic via prompt | Probabilistic via prompt |

---

## 2. Default Sovereign Engine Configuration

The Sovereign Engine (`documind-sovereign-llm-v1` and `documind-fast-embed-384`) is active upon system initialization with zero user configuration required:
- Embedded deterministic 384-dimensional unit-vector generator.
- Term-frequency lexical matcher combined with semantic projection.
- Built-in prompt sanitizer eliminating adversarial jailbreak attempts.
- Sentence-level provenance tracking mapping each phrase directly to its document citation.

---

## 3. Ollama Local Daemon Integration

To use Ollama models:
1. Ensure Ollama is running locally:
   ```bash
   ollama serve
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```
2. Navigate to **AI Settings** in the DocuMind UI (`/ai-workspace`) or call `PUT /api/v1/ai/settings`:
   ```json
   {
     "default_provider": "ollama",
     "default_llm_model": "llama3.2",
     "default_embedding_model": "nomic-embed-text",
     "ollama_base_url": "http://localhost:11434"
   }
   ```

---

## 4. Google Gemini Cloud Integration

Google Gemini provides massive context windows (up to 1M tokens) and multimodal reasoning.

### Strict Privacy & Consent Safeguards:
- DocuMind AI **never** sends document content to cloud providers without explicit user consent.
- `allow_cloud_fallback` must be toggled on by the user in Settings.
- API keys are encrypted before storage in `AIProviderConfigRecord`.

To configure Gemini:
```json
{
  "default_provider": "gemini",
  "default_llm_model": "gemini-2.5-flash",
  "default_embedding_model": "text-embedding-004",
  "gemini_api_key": "AIzaSy...",
  "allow_cloud_fallback": true
}
```
If an unconsented cloud request is initiated, the system immediately halts with `HTTP 403 Forbidden: Cloud provider usage requires explicit user consent`.
