import { severityColor, severityLabel } from "@/lib/severity";

type Props = {
  label: string;
  value: number | null;
  unit?: string;
};

export default function StatCard({ label, value, unit = "%" }: Props) {
  const color = value !== null ? severityColor(value) : "#6b7280";
  const badge = value !== null ? severityLabel(value) : "---";

  return (
    <div className="stat-card">
      <div className="stat-header">
        <span className="stat-label">{label}</span>
        <span
          className="stat-badge"
          style={{ color, borderColor: color, background: `${color}18` }}
        >
          {badge}
        </span>
      </div>
      <div className="stat-value" style={{ color }}>
        {value !== null ? `${value}${unit}` : "—"}
      </div>
      <div className="stat-bar-track">
        <div
          className="stat-bar-fill"
          style={{ width: `${value ?? 0}%`, background: color }}
        />
      </div>
    </div>
  );
}
