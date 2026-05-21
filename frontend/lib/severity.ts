import type { AlertSeverity } from "@/types/metrics";

export function severityColor(v: number): string {
  if (v > 80) return "#f87171";
  if (v > 60) return "#facc15";
  return "#34d399";
}

export function severityLabel(v: number): string {
  if (v > 80) return "CRIT";
  if (v > 60) return "WARN";
  return "OK";
}

export function parseAlertSeverity(text: string): AlertSeverity {
  const t = text.toLowerCase();
  if (t.includes("high") || t.includes("critical") || t.includes(">80"))
    return "high";
  if (t.includes("medium") || t.includes(">60")) return "medium";
  return "low";
}

export function overallHealth(
  cpu: number,
  memory: number,
  disk: number,
): string {
  if (cpu > 80 || memory > 80 || disk > 80) return "DEGRADED";
  if (cpu > 60 || memory > 60 || disk > 60) return "WARNING";
  return "NOMINAL";
}

export function healthColor(status: string): string {
  if (status === "DEGRADED") return "#f87171";
  if (status === "WARNING") return "#facc15";
  if (status === "NOMINAL") return "#34d399";
  return "#6b7280";
}
