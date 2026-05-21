import type { Metrics, ChatMessage } from "@/types/metrics";

const BASE = "http://127.0.0.1:8000";

export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(`${BASE}/metrics`);
  if (!res.ok) throw new Error(`Metrics fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchAnalysis(): Promise<{
  analysis: string;
  groq_calls_total: number;
}> {
  const res = await fetch(`${BASE}/analyze?force=true`);
  if (!res.ok) throw new Error(`Analysis fetch failed: ${res.status}`);
  return res.json();
}

export async function sendChatMessage(
  message: string,
  history: ChatMessage[],
): Promise<{ response: string; groq_calls_total: number }> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      history: history.map((m) => ({
        role: m.role === "ai" ? "assistant" : "user",
        text: m.text,
      })),
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail || `HTTP ${res.status}`);
  }
  return res.json();
}
