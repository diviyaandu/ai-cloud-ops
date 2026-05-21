// hooks/useAgent.ts
// Manages calls to /agent, tracks which agent responded, and conversation history.

import { useState, useCallback, useRef } from "react";

export type AgentType = "operational" | "security" | "finops" | "general";

export interface AgentMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  agent?: AgentType;
  agentLabel?: string;
  intent?: string;
  intentConfidence?: number;
  overallStatus?: string;
  data?: Record<string, unknown>;
  timestamp: number;
}

interface AgentRequest {
  message: string;
  history: { role: string; content: string }[];
  force_agent?: AgentType | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function useAgent() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forcedAgent, setForcedAgent] = useState<AgentType | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;
      setError(null);

      const userMsg: AgentMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      // Build history for the API (last 10 turns, alternating roles)
      const history = messages.slice(-10).map((m) => ({
        role: m.role === "user" ? "user" : "assistant",
        content: m.content,
      }));

      const payload: AgentRequest = {
        message: text,
        history,
        force_agent: forcedAgent ?? null,
      };

      abortRef.current = new AbortController();

      try {
        const res = await fetch(`${API_BASE}/agent`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: abortRef.current.signal,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail ?? `HTTP ${res.status}`);
        }

        const data = await res.json();

        const agentMsg: AgentMessage = {
          id: crypto.randomUUID(),
          role: "agent",
          content: data.answer,
          agent: data.agent,
          agentLabel: data.agent_label,
          intent: data.intent,
          intentConfidence: data.intent_confidence,
          overallStatus: data.overall_status,
          data: data.data,
          timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, agentMsg]);
      } catch (e: unknown) {
        if (e instanceof Error && e.name === "AbortError") return;
        const msg = e instanceof Error ? e.message : "Unknown error";
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [loading, messages, forcedAgent],
  );

  const clearMessages = useCallback(() => setMessages([]), []);

  return {
    messages,
    loading,
    error,
    forcedAgent,
    setForcedAgent,
    sendMessage,
    clearMessages,
  };
}
