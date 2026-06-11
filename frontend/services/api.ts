import type { Metrics, ChatMessage } from "@/types/metrics";

const BASE = "http://127.0.0.1:8000";

function detailMessage(err: unknown, fallback: string) {
  if (err && typeof err === "object" && "detail" in err) {
    const detail = (err as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

export type AzureSessionStatus = {
  connected: boolean;
  source: "session" | "env" | "none";
  subscription_id: string | null;
  expires_at: string | null;
};

export type AzureConnectPayload = {
  subscription_id: string;
  tenant_id: string;
  client_id: string;
  client_secret: string;
};

export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(`${BASE}/metrics`);
  if (!res.ok) throw new Error(`Metrics fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchAzureSessionStatus(): Promise<AzureSessionStatus> {
  const res = await fetch(`${BASE}/session/status`);
  if (!res.ok) throw new Error(`Session status failed: ${res.status}`);
  return res.json();
}

export async function connectAzureSession(
  payload: AzureConnectPayload,
): Promise<AzureSessionStatus> {
  const res = await fetch(`${BASE}/session/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(detailMessage(err, `HTTP ${res.status}`));
  }
  return res.json();
}

export async function disconnectAzureSession(): Promise<AzureSessionStatus> {
  const res = await fetch(`${BASE}/session/disconnect`, { method: "POST" });
  if (!res.ok) throw new Error(`Session disconnect failed: ${res.status}`);
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
    throw new Error(detailMessage(err, `HTTP ${res.status}`));
  }
  return res.json();
}
