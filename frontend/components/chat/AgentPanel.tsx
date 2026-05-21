// components/chat/AgentPanel.tsx
// Drop-in replacement / companion to ChatPanel.tsx
// Shows which agent responded, with routing confidence + status badge.

"use client";

import { useRef, useEffect, KeyboardEvent } from "react";
import { useAgent, AgentType, AgentMessage } from "@/hooks/useAgent";

// ── Helpers ────────────────────────────────────────────────────────────────────

const AGENT_OPTIONS: {
  value: AgentType | null;
  label: string;
  description: string;
}[] = [
  { value: null, label: "🔀 Auto", description: "Let the router decide" },
  {
    value: "operational",
    label: "⚙️ Operational",
    description: "CPU, memory, Prometheus",
  },
  {
    value: "security",
    label: "🔒 Security",
    description: "Ports, SSH, processes",
  },
  { value: "finops", label: "💰 FinOps", description: "Azure costs & budgets" },
];

function statusColor(status?: string): string {
  switch (status) {
    case "critical":
      return "#f87171";
    case "warning":
      return "#facc15";
    case "ok":
      return "#34d399";
    default:
      return "#6b7280";
  }
}

function statusDot(status?: string) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        backgroundColor: statusColor(status),
        marginRight: 6,
        flexShrink: 0,
      }}
    />
  );
}

function AgentBadge({ msg }: { msg: AgentMessage }) {
  if (msg.role !== "agent" || !msg.agent) return null;
  const conf = msg.intentConfidence
    ? Math.round(msg.intentConfidence * 100)
    : null;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        marginBottom: 6,
        flexWrap: "wrap",
      }}
    >
      <span
        style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: 11,
          color: "#34d399",
          background: "rgba(52,211,153,0.1)",
          border: "1px solid rgba(52,211,153,0.25)",
          borderRadius: 4,
          padding: "2px 8px",
        }}
      >
        {msg.agentLabel}
      </span>

      {statusDot(msg.overallStatus)}
      <span
        style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: 10,
          color: statusColor(msg.overallStatus),
        }}
      >
        {(msg.overallStatus ?? "unknown").toUpperCase()}
      </span>

      {conf !== null && (
        <span
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 10,
            color: "#6b7280",
          }}
        >
          routing {conf}% confidence
        </span>
      )}

      {msg.data?.data_mode === "mock" && (
        <span
          style={{
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 10,
            color: "#facc15",
            background: "rgba(250,204,21,0.1)",
            border: "1px solid rgba(250,204,21,0.2)",
            borderRadius: 4,
            padding: "1px 6px",
          }}
        >
          MOCK DATA
        </span>
      )}
    </div>
  );
}

function MessageBubble({ msg }: { msg: AgentMessage }) {
  const isUser = msg.role === "user";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        marginBottom: 16,
      }}
    >
      <AgentBadge msg={msg} />
      <div
        style={{
          maxWidth: "82%",
          background: isUser
            ? "rgba(52,211,153,0.12)"
            : "rgba(255,255,255,0.04)",
          border: `1px solid ${isUser ? "rgba(52,211,153,0.3)" : "rgba(255,255,255,0.08)"}`,
          borderRadius: isUser ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
          padding: "10px 14px",
          color: isUser ? "#d1fae5" : "#e2e8f0",
          fontFamily: "JetBrains Mono, monospace",
          fontSize: 13,
          lineHeight: 1.65,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {msg.content}
      </div>
      <span
        style={{
          fontFamily: "JetBrains Mono, monospace",
          fontSize: 10,
          color: "#374151",
          marginTop: 4,
        }}
      >
        {new Date(msg.timestamp).toLocaleTimeString()}
      </span>
    </div>
  );
}

// ── Main panel ─────────────────────────────────────────────────────────────────

export default function AgentPanel() {
  const {
    messages,
    loading,
    error,
    forcedAgent,
    setForcedAgent,
    sendMessage,
    clearMessages,
  } = useAgent();

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const val = inputRef.current?.value.trim() ?? "";
      if (val) {
        sendMessage(val);
        inputRef.current!.value = "";
      }
    }
  }

  function handleSend() {
    const val = inputRef.current?.value.trim() ?? "";
    if (val) {
      sendMessage(val);
      inputRef.current!.value = "";
    }
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "#080b0f",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 8,
        overflow: "hidden",
        fontFamily: "JetBrains Mono, monospace",
      }}
    >
      {/* ── Header ── */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          display: "flex",
          alignItems: "center",
          gap: 12,
          background: "rgba(255,255,255,0.02)",
          flexWrap: "wrap",
        }}
      >
        <span
          style={{
            color: "#34d399",
            fontWeight: 700,
            fontSize: 13,
            letterSpacing: "0.08em",
          }}
        >
          AGENT CHAT
        </span>

        {/* Agent selector */}
        <div
          style={{
            display: "flex",
            gap: 4,
            flexWrap: "wrap",
            marginLeft: "auto",
          }}
        >
          {AGENT_OPTIONS.map((opt) => (
            <button
              key={String(opt.value)}
              title={opt.description}
              onClick={() => setForcedAgent(opt.value)}
              style={{
                fontFamily: "JetBrains Mono, monospace",
                fontSize: 11,
                padding: "3px 10px",
                borderRadius: 4,
                border: "1px solid",
                cursor: "pointer",
                transition: "all 0.15s",
                borderColor:
                  forcedAgent === opt.value
                    ? "#34d399"
                    : "rgba(255,255,255,0.12)",
                background:
                  forcedAgent === opt.value
                    ? "rgba(52,211,153,0.15)"
                    : "transparent",
                color: forcedAgent === opt.value ? "#34d399" : "#6b7280",
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            style={{
              fontFamily: "JetBrains Mono, monospace",
              fontSize: 10,
              color: "#374151",
              background: "transparent",
              border: "none",
              cursor: "pointer",
              padding: "2px 6px",
            }}
          >
            CLEAR
          </button>
        )}
      </div>

      {/* ── Message list ── */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              color: "#374151",
              fontSize: 12,
              gap: 8,
              textAlign: "center",
            }}
          >
            <span style={{ fontSize: 28 }}>🤖</span>
            <span>
              Ask about system health, security posture, or cloud costs.
            </span>
            <span style={{ fontSize: 11, color: "#1f2937" }}>
              The router will dispatch to the right agent automatically.
            </span>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}

        {loading && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "#34d399",
              fontSize: 12,
              marginBottom: 8,
            }}
          >
            <span className="thinking-dot" />
            <span style={{ color: "#4b5563" }}>
              routing → fetching live data…
            </span>
          </div>
        )}

        {error && (
          <div
            style={{
              color: "#f87171",
              fontSize: 12,
              background: "rgba(248,113,113,0.08)",
              border: "1px solid rgba(248,113,113,0.2)",
              borderRadius: 6,
              padding: "8px 12px",
              marginBottom: 8,
            }}
          >
            ⚠ {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input ── */}
      <div
        style={{
          padding: "12px 16px",
          borderTop: "1px solid rgba(255,255,255,0.06)",
          display: "flex",
          gap: 8,
          alignItems: "flex-end",
        }}
      >
        <textarea
          ref={inputRef}
          rows={2}
          placeholder="Ask about metrics, security, or costs… (Enter to send)"
          onKeyDown={handleKeyDown}
          style={{
            flex: 1,
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 6,
            color: "#e2e8f0",
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 12,
            padding: "8px 12px",
            resize: "none",
            outline: "none",
            lineHeight: 1.5,
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading}
          style={{
            background: loading
              ? "rgba(52,211,153,0.2)"
              : "rgba(52,211,153,0.85)",
            color: "#080b0f",
            border: "none",
            borderRadius: 6,
            padding: "8px 16px",
            fontFamily: "JetBrains Mono, monospace",
            fontWeight: 700,
            fontSize: 12,
            cursor: loading ? "not-allowed" : "pointer",
            letterSpacing: "0.05em",
            transition: "background 0.15s",
            whiteSpace: "nowrap",
          }}
        >
          {loading ? "…" : "SEND ▶"}
        </button>
      </div>

      <style>{`
        .thinking-dot {
          width: 8px; height: 8px; border-radius: 50%;
          background: #34d399;
          animation: pulse 1.2s ease-in-out infinite;
          flex-shrink: 0;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.3; transform: scale(0.8); }
        }
        textarea::placeholder { color: #374151; }
      `}</style>
    </div>
  );
}
