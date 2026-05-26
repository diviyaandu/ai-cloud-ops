type Props = {
  label: string;
  value: number | null;
  icon: string; // e.g. "⬡", "▦", plain text icon
  accent?: string; // hex color
  loading?: boolean;
};

const DEFAULT_ACCENT = "#2dd4bf";

export default function CloudStatCard({
  label,
  value,
  icon,
  accent = DEFAULT_ACCENT,
  loading = false,
}: Props) {
  return (
    <div className="stat-card">
      <div className="stat-header">
        <span className="stat-label">{label}</span>
        <span
          className="stat-badge"
          style={{
            color: accent,
            borderColor: accent,
            background: `${accent}18`,
          }}
        >
          AZURE
        </span>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          gap: "10px",
          marginBottom: "14px",
        }}
      >
        <div
          className="stat-value"
          style={{ color: loading ? "#374151" : accent, marginBottom: 0 }}
        >
          {loading ? "—" : (value ?? "—")}
        </div>
        <span style={{ fontSize: "20px", marginBottom: "6px", opacity: 0.5 }}>
          {icon}
        </span>
      </div>

      {/* Decorative bar — proportional to count, capped at 100 for display */}
      <div className="stat-bar-track">
        <div
          className="stat-bar-fill"
          style={{
            width:
              loading || value === null
                ? "0%"
                : `${Math.min((value / 20) * 100, 100)}%`,
            background: accent,
            transition: "width 0.8s ease",
          }}
        />
      </div>
    </div>
  );
}
