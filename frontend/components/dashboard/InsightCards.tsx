"use client";

import type { CloudSummary } from "@/hooks/useCloudResources";

type Props = { data: CloudSummary | null; loading: boolean };

function fmt(n: number | null | undefined, decimals = 0): string {
  if (n == null) return "—";
  return n.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function statusColor(s: string) {
  if (s === "critical") return "#f87171";
  if (s === "warning")  return "#fbbf24";
  return "#34d399";
}

function Skel() {
  return (
    <span style={{
      display: "block", width: "60%", height: 28, borderRadius: 4,
      background: "linear-gradient(90deg,#141c26 25%,#1e2a38 50%,#141c26 75%)",
      backgroundSize: "200% 100%", animation: "shimmer 1.6s infinite",
    }} />
  );
}

type CardProps = {
  label: string;
  value: React.ReactNode;
  sub: string;
  accent: string;
  icon: string;
  loading: boolean;
  badge?: string;
  badgeColor?: string;
};

function InsightCard({ label, value, sub, accent, icon, loading, badge, badgeColor }: CardProps) {
  return (
    <div className="ic" style={{ "--ic-accent": accent } as React.CSSProperties}>
      <div className="ic-top">
        <span className="ic-icon">{icon}</span>
        {badge && (
          <span className="ic-badge" style={{ color: badgeColor ?? accent, borderColor: (badgeColor ?? accent) + "44", background: (badgeColor ?? accent) + "12" }}>
            {badge}
          </span>
        )}
      </div>
      <div className="ic-value">
        {loading ? <Skel /> : value}
      </div>
      <div className="ic-label">{label}</div>
      <div className="ic-sub">{sub}</div>
      <div className="ic-bar"><span className="ic-bar-fill" /></div>
    </div>
  );
}

export default function InsightCards({ data, loading }: Props) {
  const spend    = data?.spend;
  const health   = data?.health;
  const security = data?.security;
  const logs     = data?.logs;
  const advisor  = data?.advisor;

  return (
    <div className="ic-grid">
      {/* Predicted spend */}
      <InsightCard
        label="Predicted Spend"
        value={
          <span>
            <span style={{ fontSize: 11, color: "var(--fg-dim)", marginRight: 2 }}>$</span>
            {fmt(spend?.forecast_eom_usd)}
          </span>
        }
        sub={`$${fmt(spend?.spent_usd)} spent · $${fmt(spend?.budget_usd)} budget`}
        accent="#a78bfa"
        icon="◈"
        loading={loading}
        badge={spend?.percent_used != null ? `${fmt(spend.percent_used, 1)}% used` : undefined}
        badgeColor={statusColor(spend?.status ?? "ok")}
      />

      {/* Budget remaining */}
      <InsightCard
        label="Budget Remaining"
        value={
          <span>
            <span style={{ fontSize: 11, color: "var(--fg-dim)", marginRight: 2 }}>$</span>
            {fmt(
              spend?.budget_usd != null && spend?.spent_usd != null
                ? spend.budget_usd - spend.spent_usd
                : null
            )}
          </span>
        }
        sub="this month"
        accent="#60a5fa"
        icon="◇"
        loading={loading}
        badge={spend?.status}
        badgeColor={statusColor(spend?.status ?? "ok")}
      />

      {/* Unhealthy resources */}
      <InsightCard
        label="Unhealthy Resources"
        value={<span>{fmt(health?.unhealthy_total)}</span>}
        sub={`${health?.critical ?? 0} critical · ${health?.warning ?? 0} warning`}
        accent={statusColor(health?.status ?? "ok")}
        icon="⚠"
        loading={loading}
        badge={health?.status}
        badgeColor={statusColor(health?.status ?? "ok")}
      />

      {/* Security */}
      <InsightCard
        label="Governance Risks"
        value={<span>{fmt(security?.untagged_total)}</span>}
        sub={`untagged · ${security?.recent_changes ?? 0} recent changes`}
        accent="#fb923c"
        icon="🔒"
        loading={loading}
        badge={security?.status}
        badgeColor={statusColor(security?.status ?? "ok")}
      />

      {/* Log health */}
      <InsightCard
        label="Log Errors (24h)"
        value={<span>{fmt((logs?.errors_24h ?? 0) + (logs?.failed_ops_24h ?? 0))}</span>}
        sub={`${logs?.errors_24h ?? 0} errors · ${logs?.failed_ops_24h ?? 0} failed ops`}
        accent={statusColor(logs?.status ?? "ok")}
        icon="◎"
        loading={loading}
        badge={logs?.status}
        badgeColor={statusColor(logs?.status ?? "ok")}
      />

      {/* Advisor savings */}
      <InsightCard
        label="Advisor Savings"
        value={
          <span>
            <span style={{ fontSize: 11, color: "var(--fg-dim)", marginRight: 2 }}>$</span>
            {fmt(advisor?.potential_savings)}
          </span>
        }
        sub={`${advisor?.total ?? 0} recommendation${(advisor?.total ?? 0) !== 1 ? "s" : ""}`}
        accent="#34d399"
        icon="💡"
        loading={loading}
        badge={advisor?.total ? "review" : "clean"}
        badgeColor={advisor?.total ? "#fbbf24" : "#34d399"}
      />
    </div>
  );
}

// CSS to add to dashboard.css:
// .ic-grid, .ic, .ic-top, .ic-icon, .ic-badge, .ic-value, .ic-label, .ic-sub, .ic-bar, .ic-bar-fill
