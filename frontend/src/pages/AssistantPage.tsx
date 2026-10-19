import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  ChevronDown,
  ChevronRight,
  Bot,
  User,
  Sparkles,
  Cpu,
  Settings,
  X,
  CheckCircle,
  AlertCircle,
  Key,
} from "lucide-react";
import { api } from "../api/client";
import type { ChatMessage, ChatStatusResponse } from "../api/types";

const SUGGESTIONS = [
  "Why is customer 104 in this cluster?",
  "Show segments overview and average balance",
  "Show at-risk customers needing retention in cluster 1",
  "How was the data prepared for clustering?",
];

const renderFormattedContent = (content: string) => {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} style={{ margin: "6px 0", paddingLeft: "20px" }}>
          {currentList}
        </ul>
      );
      currentList = [];
    }
  };

  const formatInline = (str: string): React.ReactNode => {
    const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code
            key={i}
            style={{
              fontFamily: "var(--font-mono)",
              backgroundColor: "var(--bg-subtle)",
              padding: "1px 4px",
              borderRadius: "3px",
              fontSize: "12px",
            }}
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      elements.push(<div key={`br-${index}`} style={{ height: "4px" }} />);
      return;
    }

    if (trimmed.startsWith("### ")) {
      flushList();
      elements.push(
        <h4 key={index} style={{ margin: "8px 0 4px", fontSize: "14px", fontWeight: 600 }}>
          {formatInline(trimmed.slice(4))}
        </h4>
      );
    } else if (trimmed.startsWith("## ")) {
      flushList();
      elements.push(
        <h3 key={index} style={{ margin: "10px 0 4px", fontSize: "15px", fontWeight: 600 }}>
          {formatInline(trimmed.slice(3))}
        </h3>
      );
    } else if (trimmed.startsWith("- ") || trimmed.startsWith("• ") || trimmed.startsWith("* ")) {
      currentList.push(
        <li key={`li-${index}`} style={{ marginBottom: "3px" }}>
          {formatInline(trimmed.slice(2))}
        </li>
      );
    } else {
      flushList();
      elements.push(
        <p key={index} style={{ margin: "4px 0", lineHeight: 1.5 }}>
          {formatInline(trimmed)}
        </p>
      );
    }
  });

  flushList();
  return elements;
};

export const AssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I am your retail banking intelligence assistant. I can analyze customer segments, explain individual customer cluster assignments, identify at-risk customers needing retention, provide exploratory data metrics, and explain our ML feature engineering pipeline.\n\nYou can ask me questions about customer segments, retention risks, feature preprocessing, or why a specific customer was assigned to their cluster.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [expandedPlanIds, setExpandedPlanIds] = useState<Record<string, boolean>>({});

  // LLM Status and Configuration State
  const [llmStatus, setLlmStatus] = useState<ChatStatusResponse | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [keyActionLoading, setKeyActionLoading] = useState(false);
  const [keyActionFeedback, setKeyActionFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchStatus = async () => {
    try {
      const status = await api.getChatStatus();
      setLlmStatus(status);
    } catch {
      // Backend status endpoint unreachable or older version
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const togglePlan = (msgId: string) => {
    setExpandedPlanIds((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKeyInput.trim()) return;

    setKeyActionLoading(true);
    setKeyActionFeedback(null);
    try {
      const res = await api.setChatKey(apiKeyInput.trim());
      setKeyActionFeedback({ type: "success", text: res.message });
      setApiKeyInput("");
      await fetchStatus();
    } catch (err: any) {
      setKeyActionFeedback({ type: "error", text: err.message || "Failed to verify API key." });
    } finally {
      setKeyActionLoading(false);
    }
  };

  const handleClearKey = async () => {
    setKeyActionLoading(true);
    setKeyActionFeedback(null);
    try {
      const res = await api.clearChatKey();
      setKeyActionFeedback({ type: "success", text: res.message });
      await fetchStatus();
    } catch (err: any) {
      setKeyActionFeedback({ type: "error", text: err.message || "Failed to clear key." });
    } finally {
      setKeyActionLoading(false);
    }
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || inputQuery).trim();
    if (!textToSend || isLoading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const res = await api.chat(textToSend);
      const assistantMsg: ChatMessage = {
        id: String(Date.now() + 1),
        role: "assistant",
        content: res.response,
        execution_plan: res.execution_plan,
        results: res.results,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: String(Date.now() + 1),
        role: "assistant",
        content: "The assistant could not reach the server. Please check your connection and retry.",
        execution_plan: ["Network or server error occurred", "Displayed fallback notice"],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 120px)", minHeight: "550px" }}>
      {/* Page Header with LLM Status and Settings Pill */}
      <div
        className="page-header"
        style={{
          marginBottom: "16px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "16px",
        }}
      >
        <div>
          <h1 className="page-title">Ask the assistant</h1>
          <p className="page-desc">
            Query customer attributes, cluster rationale, and retention strategies using natural language. Each answer discloses the agent execution plan.
          </p>
        </div>

        {/* Engine Status & Config Button */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
          {llmStatus?.configured ? (
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 10px",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-surface)",
                border: "1px solid var(--border)",
                fontSize: "12px",
                color: "var(--text-main)",
                fontWeight: 500,
              }}
            >
              <Sparkles size={13} style={{ color: "var(--accent)" }} />
              <span>Groq LLaMA 3.1 Active</span>
            </div>
          ) : (
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 10px",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "var(--bg-subtle)",
                border: "1px solid var(--border)",
                fontSize: "12px",
                color: "var(--text-muted)",
              }}
            >
              <Cpu size={13} />
              <span>Local Analytical Agent</span>
            </div>
          )}

          <button
            type="button"
            onClick={() => {
              setIsSettingsOpen(!isSettingsOpen);
              setKeyActionFeedback(null);
            }}
            className="btn btn-secondary"
            style={{ padding: "4px 10px", fontSize: "12px", display: "flex", alignItems: "center", gap: "5px" }}
          >
            <Settings size={13} />
            <span>LLM Settings</span>
          </button>
        </div>
      </div>

      {/* Collapsible LLM Key Configuration Panel */}
      {isSettingsOpen && (
        <div
          className="card"
          style={{
            marginBottom: "16px",
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            padding: "16px 20px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Key size={16} style={{ color: "var(--accent)" }} />
              <h3 style={{ fontSize: "14px", fontWeight: 600, margin: 0 }}>Groq LLM Configuration</h3>
            </div>
            <button
              onClick={() => setIsSettingsOpen(false)}
              style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: "2px" }}
            >
              <X size={16} />
            </button>
          </div>

          <p style={{ fontSize: "12.5px", color: "var(--text-muted)", marginBottom: "12px", lineHeight: 1.5 }}>
            Groq provides ultra-fast LLM inference (Llama 3.1 8B Instant). You can get a free API key with no credit card required at{" "}
            <a
              href="https://console.groq.com/keys"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "var(--accent)", textDecoration: "underline" }}
            >
              console.groq.com/keys
            </a>
            . When configured, Groq synthesizes conversational responses using live tool data. If left blank, the assistant runs in local deterministic mode.
          </p>

          <form onSubmit={handleSaveKey} style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
            <input
              type="password"
              placeholder="Enter Groq API Key (gsk_...)"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              disabled={keyActionLoading}
              className="form-input"
              style={{ flex: 1, minWidth: "260px", fontFamily: "var(--font-mono)", fontSize: "12.5px" }}
            />
            <button
              type="submit"
              disabled={!apiKeyInput.trim() || keyActionLoading}
              className="btn btn-primary"
              style={{ padding: "6px 14px", fontSize: "12.5px" }}
            >
              {keyActionLoading ? "Verifying..." : "Save & Verify Key"}
            </button>
            {llmStatus?.configured && (
              <button
                type="button"
                onClick={handleClearKey}
                disabled={keyActionLoading}
                className="btn btn-secondary"
                style={{ padding: "6px 14px", fontSize: "12.5px", color: "var(--status-danger)" }}
              >
                Clear Key
              </button>
            )}
          </form>

          {keyActionFeedback && (
            <div
              style={{
                marginTop: "10px",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "12px",
                color: keyActionFeedback.type === "success" ? "var(--status-success)" : "var(--status-danger)",
              }}
            >
              {keyActionFeedback.type === "success" ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
              <span>{keyActionFeedback.text}</span>
            </div>
          )}
        </div>
      )}

      {/* Chat Messages Panel */}
      <div
        className="card"
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          padding: "0",
          overflow: "hidden",
        }}
      >
        {/* Messages Stream */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {messages.map((msg) => {
            const isUser = msg.role === "user";
            const isPlanOpen = expandedPlanIds[msg.id];

            return (
              <div
                key={msg.id}
                style={{
                  display: "flex",
                  gap: "10px",
                  maxWidth: isUser ? "75%" : "85%",
                  alignSelf: isUser ? "flex-end" : "flex-start",
                  flexDirection: isUser ? "row-reverse" : "row",
                }}
              >
                {/* Avatar Icon */}
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "50%",
                    backgroundColor: isUser ? "var(--accent)" : "var(--bg-subtle)",
                    color: isUser ? "#ffffff" : "var(--accent)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    border: "1px solid var(--border)",
                  }}
                >
                  {isUser ? <User size={15} /> : <Bot size={15} />}
                </div>

                {/* Message Bubble */}
                <div
                  style={{
                    backgroundColor: isUser ? "var(--accent-subtle)" : "var(--bg-surface)",
                    color: "var(--text-main)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)",
                    padding: "12px 16px",
                    fontSize: "13.5px",
                    lineHeight: 1.5,
                  }}
                >
                  <div>{renderFormattedContent(msg.content)}</div>

                  {/* Collapsible 'How I got this' Section */}
                  {msg.execution_plan && msg.execution_plan.length > 0 && (
                    <div style={{ marginTop: "10px", borderTop: "1px solid var(--border)", paddingTop: "8px" }}>
                      <button
                        onClick={() => togglePlan(msg.id)}
                        style={{
                          background: "none",
                          border: "none",
                          color: "var(--text-muted)",
                          fontSize: "12px",
                          fontWeight: 500,
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                          padding: "2px 0",
                        }}
                      >
                        {isPlanOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        <span>How I got this ({msg.execution_plan.length} steps)</span>
                      </button>

                      {isPlanOpen && (
                        <div
                          style={{
                            marginTop: "6px",
                            backgroundColor: "var(--bg-subtle)",
                            borderRadius: "var(--radius-sm)",
                            padding: "8px 10px",
                            fontSize: "11.5px",
                            fontFamily: "var(--font-mono)",
                            color: "var(--text-muted)",
                            display: "flex",
                            flexDirection: "column",
                            gap: "4px",
                          }}
                        >
                          {msg.execution_plan.map((step, idx) => (
                            <div key={idx}>
                              {idx + 1}. {step}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <div
                    style={{
                      fontSize: "10.5px",
                      color: "var(--text-faint)",
                      textAlign: isUser ? "right" : "left",
                      marginTop: "6px",
                    }}
                  >
                    {msg.timestamp}
                  </div>
                </div>
              </div>
            );
          })}

          {isLoading && (
            <div style={{ display: "flex", gap: "10px", alignSelf: "flex-start" }}>
              <div
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "50%",
                  backgroundColor: "var(--bg-subtle)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  border: "1px solid var(--border)",
                }}
              >
                <Bot size={15} style={{ color: "var(--accent)" }} />
              </div>
              <div
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-md)",
                  padding: "10px 14px",
                  fontSize: "13px",
                  color: "var(--text-muted)",
                }}
              >
                Analyzing data and formulating answer...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestions Strip */}
        <div
          style={{
            padding: "8px 16px",
            backgroundColor: "var(--bg-subtle)",
            borderTop: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            overflowX: "auto",
          }}
        >
          <span style={{ fontSize: "11px", color: "var(--text-muted)", flexShrink: 0 }}>
            Sample queries:
          </span>
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSend(s)}
              disabled={isLoading}
              style={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-sm)",
                padding: "3px 8px",
                fontSize: "11.5px",
                color: "var(--text-main)",
                cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          style={{
            padding: "12px 16px",
            borderTop: "1px solid var(--border)",
            display: "flex",
            gap: "8px",
            backgroundColor: "var(--bg-surface)",
          }}
        >
          <input
            type="text"
            placeholder="Ask about segments, customer retention, or individual customer IDs..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isLoading}
            className="form-input"
            style={{ flex: 1 }}
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="btn btn-primary"
            style={{ padding: "8px 16px" }}
          >
            <Send size={15} />
            Send
          </button>
        </form>
      </div>
    </div>
  );
};
