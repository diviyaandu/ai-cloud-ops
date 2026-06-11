"use client";

import LiveClock from "@/components/layout/LiveClock";
import StatusPill from "@/components/layout/StatusPill";
import { useGroqStats } from "@/hooks/useGroqStats";
import type { CloudResources } from "@/types/cloud";

interface TopbarProps {
  data: CloudResources | null;
  loading: boolean;
  onRefresh: () => void;
}

export default function Topbar({ data, loading, onRefresh }: TopbarProps) {
  const groqCalls = useGroqStats();
  const isLive = data?.mode === "live";

  return (
    <header className="topbar">
      <div className="topbar-brand">
        <div className="topbar-logo">⬡</div>
        <div>
          <div className="topbar-title">AI Cloud Ops</div>
          <div className="topbar-sub">Azure · LangGraph · Groq</div>
        </div>
      </div>
      <div className="topbar-right">
        <div className="topbar-stat">
          <span className="topbar-stat-key">Groq calls</span>
          <span className="topbar-stat-val">{groqCalls}</span>
        </div>
        <div className="topbar-divider" />
        <div className="topbar-stat">
          <span className="topbar-stat-key">Resources</span>
          <span className="topbar-stat-val">
            {loading ? "—" : (data?.total ?? "—")}
          </span>
        </div>
        <div className="topbar-divider" />
        <LiveClock />
        <div className="topbar-divider" />
        <button
          onClick={onRefresh}
          disabled={loading}
          style={{
            fontSize: 11,
            padding: "3px 10px",
            borderRadius: 4,
            background: loading ? "#ffffff08" : "#ffffff10",
            border: "1px solid #ffffff18",
            color: loading ? "#4b5563" : "#9ca3af",
            cursor: loading ? "not-allowed" : "pointer",
            letterSpacing: "0.05em",
          }}
        >
          {loading ? "↻ …" : "↻ Refresh"}
        </button>
        <div className="topbar-divider" />
        <StatusPill live={isLive} loading={loading} />
      </div>
    </header>
  );
}
