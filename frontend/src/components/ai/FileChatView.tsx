import React, { useEffect, useRef, useState } from "react";
import {
  Bot,
  Clock,
  Cpu,
  Send,
  Sparkles,
  Trash2,
  User,
} from "lucide-react";
import { CitationViewer } from "./CitationViewer";
import { api } from "@/services/api";
import { ChatMessage, ChatResponse } from "@/types/api";

interface FileChatViewProps {
  selectedFileId?: string;
  selectedFilename?: string;
}

export const FileChatView: React.FC<FileChatViewProps> = ({
  selectedFileId,
  selectedFilename,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [provider, setProvider] = useState("sovereign");
  const [scope, setScope] = useState<"single" | "all">(selectedFileId ? "single" : "all");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedFileId) {
      setScope("single");
    }
  }, [selectedFileId]);

  useEffect(() => {
    if (typeof messagesEndRef.current?.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      message_id: `user_${Date.now()}`,
      conversation_id: conversationId || "",
      role: "user",
      content: text,
      citations: [],
      retrieved_chunk_ids: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response: ChatResponse = await api.chatAI({
        message: text,
        conversation_id: conversationId,
        scope_type: scope === "single" && selectedFileId ? "single_file" : "all_accessible",
        file_ids: scope === "single" && selectedFileId ? [selectedFileId] : undefined,
        provider: provider,
        allow_cloud: false,
      });

      setConversationId(response.conversation_id);
      setMessages((prev) => [...prev, response.message]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        message_id: `err_${Date.now()}`,
        conversation_id: conversationId || "",
        role: "assistant",
        content: `Error: ${err?.message || "Failed to generate answer. Please ensure files are indexed."}`,
        citations: [],
        retrieved_chunk_ids: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setConversationId(null);
  };

  const suggestions = selectedFileId
    ? [
        "Summarize this file with key takeaways",
        "What are the most important numbers or dates mentioned?",
        "What are the main risks, findings, or conclusions?",
      ]
    : [
        "What documents are indexed in my workspace?",
        "Compare revenue and performance across files",
        "Find any mentions of security or compliance",
      ];

  return (
    <div className="flex flex-col h-[700px] bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      {/* Top Controls Header */}
      <div className="p-3.5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/40 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              Cross-Modal File Intelligence
              <span className="text-[11px] font-normal px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-mono">
                100% Grounded
              </span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {scope === "single" && selectedFilename
                ? `Active Target: ${selectedFilename}`
                : "Active Scope: All Ingested Workspace Files"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {selectedFileId && (
            <div className="flex items-center bg-slate-200 dark:bg-slate-800 rounded-lg p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setScope("single")}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  scope === "single"
                    ? "bg-white dark:bg-slate-700 shadow-xs font-medium text-slate-900 dark:text-slate-100"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                This File
              </button>
              <button
                type="button"
                onClick={() => setScope("all")}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  scope === "all"
                    ? "bg-white dark:bg-slate-700 shadow-xs font-medium text-slate-900 dark:text-slate-100"
                    : "text-slate-600 dark:text-slate-400"
                }`}
              >
                All Files
              </button>
            </div>
          )}

          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 focus:outline-hidden"
          >
            <option value="sovereign">Sovereign LLM (Local Deterministic)</option>
            <option value="ollama">Ollama (Local Llama 3.2)</option>
            <option value="gemini">Google Gemini (Cloud Opt-In)</option>
          </select>

          {messages.length > 0 && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20"
              title="Clear chat history"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 dark:text-slate-400">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-blue-600 dark:text-blue-400 mb-3 shadow-inner">
              <Bot className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">
              Ask anything about your files
            </h4>
            <p className="text-xs max-w-sm mb-4">
              Answers are strictly grounded in your indexed documents, spreadsheets, slides, audio, video, code, and archives.
            </p>
            <div className="flex flex-col gap-2 w-full max-w-md">
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(s)}
                  className="text-xs text-left px-3.5 py-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 hover:bg-blue-50 dark:hover:bg-blue-950/30 hover:border-blue-200 dark:hover:border-blue-800 text-slate-700 dark:text-slate-300 transition-colors"
                >
                  &ldquo;{s}&rdquo;
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => {
            const isUser = m.role === "user";
            return (
              <div
                key={m.message_id}
                className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/60 flex items-center justify-center text-blue-600 dark:text-blue-300 shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                    isUser
                      ? "bg-blue-600 text-white rounded-br-xs shadow-xs"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-xs border border-slate-200/80 dark:border-slate-700/80"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{m.content}</div>

                  {!isUser && m.citations && m.citations.length > 0 && (
                    <CitationViewer citations={m.citations} />
                  )}

                  {!isUser && (m.provider || m.latency_ms) && (
                    <div className="mt-2.5 pt-2 border-t border-slate-200 dark:border-slate-700/60 flex items-center gap-3 text-[10px] text-slate-400">
                      {m.provider && (
                        <span className="flex items-center gap-1">
                          <Cpu className="w-3 h-3" />
                          {m.provider}
                        </span>
                      )}
                      {m.latency_ms && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {m.latency_ms}ms
                        </span>
                      )}
                    </div>
                  )}
                </div>
                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}
        {isLoading && (
          <div className="flex gap-3 items-center text-slate-400 text-xs py-2">
            <div className="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/60 flex items-center justify-center text-blue-600 dark:text-blue-300 shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" />
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.4s]" />
              <span className="ml-2 text-slate-500">Searching chunks & synthesizing grounded answer...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              scope === "single" && selectedFilename
                ? `Ask anything about ${selectedFilename}...`
                : "Ask about any indexed file in your workspace..."
            }
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-xs"
            title="Send query"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
