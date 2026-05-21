import { parseAlertSeverity } from "@/lib/severity";
import type { Alert } from "@/types/metrics";

type Props = { rawAlerts: string[] };

const SEVERITY_COLOR: Record<Alert["severity"], string> = {
  high: "#f87171",
  medium: "#facc15",
  low: "#34d399",
};

export default function AlertsPanel({ rawAlerts }: Props) {
  const alerts: Alert[] = rawAlerts.map((text) => ({
    text,
    severity: parseAlertSeverity(text),
  }));

  return (
    <div className="panel span-1">
      <p className="panel-title">Active Alerts</p>
      {alerts.length === 0 ? (
        <div className="alert-none">
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: "#34d399",
              display: "inline-block",
            }}
          />
          All systems nominal
        </div>
      ) : (
        alerts.map((a, i) => {
          const c = SEVERITY_COLOR[a.severity];
          return (
            <div
              key={i}
              className="alert-item"
              style={{
                borderColor: `${c}40`,
                background: `${c}0a`,
                color: "#9ca3af",
              }}
            >
              <span className="alert-dot" style={{ background: c }} />
              <span>{a.text}</span>
            </div>
          );
        })
      )}
    </div>
  );
}
