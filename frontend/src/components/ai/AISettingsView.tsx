import React, { useEffect, useState } from "react";
import {
  Activity,
  Cloud,
  Cpu,
  Eye,
  EyeOff,
  Save,
  Server,
  Shield,
} from "lucide-react";
import { api } from "@/services/api";

export const AISettingsView: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [cloudConsent, setCloudConsent] = useState(false);
  const [geminiKey, setGeminiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const [sRes, tRes] = await Promise.all([
        api.getAISettings(),
        api.getAITelemetry(),
      ]);
      setSettings(sRes);
      setTelemetry(tRes);
      setCloudConsent(Boolean(sRes.cloud_consent_given));
      setOllamaUrl(
        typeof sRes.ollama_base_url === "string"
          ? sRes.ollama_base_url
          : "http://localhost:11434"
      );
    } catch (e) {
      console.error("Failed to load AI settings:", e);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setStatusMessage(null);
    try {
      await api.updateAISettings({
        cloud_consent_given: cloudConsent,
        gemini_api_key: geminiKey.trim() || undefined,
        ollama_base_url: ollamaUrl.trim() || undefined,
      });
      setStatusMessage("Settings updated successfully.");
      await loadSettings();
    } catch (e: any) {
      setStatusMessage(`Error saving settings: ${e?.message || e}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Privacy & Sovereignty Card */}
      <div className="p-5 rounded-xl border border-blue-200 dark:border-blue-900/60 bg-blue-50/40 dark:bg-blue-950/20">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-blue-600 text-white shrink-0 mt-0.5">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-blue-950 dark:text-blue-200">
              Default Sovereign Architecture & Privacy Guarantee
            </h3>
            <p className="text-xs text-blue-800/80 dark:text-blue-300/80 mt-1 leading-relaxed">
              DocuMind AI defaults to the 100% offline <strong>documind-sovereign-llm-v1</strong> engine and local 384-dimensional vector embeddings.
              Your files, extracted tables, AST symbols, transcripts, and metadata never leave this machine unless you explicitly opt in to cloud providers below.
            </p>
          </div>
        </div>
      </div>

      {/* Provider Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Local Sovereign Provider */}
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-500" />
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Sovereign Engine (Default)
              </h4>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
              Active &amp; Ready
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 leading-relaxed">
            Deterministic grounded retrieval and LLM synthesis with guaranteed zero hallucination and strict source citation grounding.
          </p>
          <div className="text-xs font-mono bg-slate-50 dark:bg-slate-800 p-2.5 rounded-lg border border-slate-200 dark:border-slate-700 space-y-1">
            <div><strong>Model:</strong> documind-sovereign-llm-v1</div>
            <div><strong>Embedder:</strong> documind-fast-embed-384</div>
            <div><strong>Network:</strong> 0 external connections (Air-Gapped)</div>
          </div>
        </div>

        {/* Ollama Local Daemon */}
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-purple-500" />
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Ollama Local Daemon
              </h4>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300">
              Local Integration
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
            Connects to your local Ollama instance for models like Llama 3.2, Mistral, or Qwen.
          </p>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            Daemon URL
          </label>
          <input
            type="text"
            value={ollamaUrl}
            onChange={(e) => setOllamaUrl(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-mono text-slate-800 dark:text-slate-200 focus:outline-hidden"
          />
        </div>

        {/* Google Gemini Cloud (Opt-In) */}
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs md:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Cloud className="w-4 h-4 text-blue-500" />
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Google Gemini Cloud (Opt-In Only)
              </h4>
            </div>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {cloudConsent ? "Consent Granted" : "Consent Required"}
            </span>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 leading-relaxed">
            Allows routing queries to Gemini 2.5 Flash for high-capacity reasoning across large documents. Requires explicit consent and a personal API key.
          </p>

          <div className="space-y-4">
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={cloudConsent}
                onChange={(e) => setCloudConsent(e.target.checked)}
                className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-xs text-slate-700 dark:text-slate-300 leading-normal">
                I explicitly consent to transmitting document snippets and user prompts to Google Cloud Gemini API.
              </span>
            </label>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Gemini API Key
              </label>
              <div className="relative">
                <input
                  type={showKey ? "text" : "password"}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder={settings?.has_gemini_key ? "••••••••••••••••••••••••••••••••" : "Enter API key"}
                  className="w-full px-3 py-2 pr-10 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-mono text-slate-800 dark:text-slate-200 focus:outline-hidden"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-between pt-2">
        {statusMessage && (
          <span className="text-xs text-slate-600 dark:text-slate-400">
            {statusMessage}
          </span>
        )}
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving}
          className="ml-auto flex items-center gap-1.5 px-5 py-2.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50 transition-all shadow-xs"
        >
          <Save className="w-4 h-4" />
          {isSaving ? "Saving..." : "Save AI Configurations"}
        </button>
      </div>

      {/* Telemetry Stats */}
      {telemetry && (
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-blue-500" />
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
              Inference Telemetry & Token Usage
            </h4>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <div className="text-xs text-slate-500 dark:text-slate-400">Total Tokens Processed</div>
              <div className="text-lg font-bold text-slate-800 dark:text-slate-100 mt-1 font-mono">
                {telemetry.total_tokens_used?.toLocaleString() || 0}
              </div>
            </div>
            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <div className="text-xs text-slate-500 dark:text-slate-400">Inference Invocations</div>
              <div className="text-lg font-bold text-slate-800 dark:text-slate-100 mt-1 font-mono">
                {telemetry.total_inference_calls || 0}
              </div>
            </div>
            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <div className="text-xs text-slate-500 dark:text-slate-400">Average Turn Latency</div>
              <div className="text-lg font-bold text-slate-800 dark:text-slate-100 mt-1 font-mono">
                {telemetry.average_latency_ms || 0}ms
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
