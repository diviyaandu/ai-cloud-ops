"use client";

import { useState, useEffect, useRef } from "react";
import { useCloudResources } from "@/hooks/useCloudResources";
import CloudIntelligence from "@/components/dashboard/CloudIntelligence";
import AlertsPanel from "@/components/dashboard/AlertsPanel";
import AnalysisPanel from "@/components/dashboard/AnalysisPanel";
import AgentPanel from "@/components/chat/AgentPanel";

function useGroqStats() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    const poll = () =>
      fetch("http://127.0.0.1:8000/stats")
        .then((r) => r.json())
        .then((d) => setCount(d.groq_call_count ?? 0))
        .catch(() => {});
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, []);
  return count;
}

// ─── Types ────────────────────────────────────────────────────────────────────
type NavItem = "overview" | "agent" | "analysis" | "alerts";

interface ResourceCardProps {
  label: string;
  sublabel: string;
  value: number | null;
  accent: string;
  icon: string;
  loading: boolean;
  region?: string;
  index: number;
}

// ─── Resource Card ────────────────────────────────────────────────────────────
function ResourceCard({
  label,
  sublabel,
  value,
  accent,
  icon,
  loading,
  region,
  index,
}: ResourceCardProps) {
  const isZero = value === 0;

  return (
    <div
      className="rc"
      style={
        {
          "--accent": accent,
          "--delay": `${index * 60}ms`,
        } as React.CSSProperties
      }
    >
      {/* corner pip */}
      <span className="rc-corner" />

      <div className="rc-header">
        <span className="rc-icon" aria-hidden>
          {icon}
        </span>
        {region && <span className="rc-region">{region}</span>}
      </div>

      <div className="rc-value-wrap">
        {loading ? (
          <span className="rc-skeleton" />
        ) : value === null ? (
          <span className="rc-null">—</span>
        ) : (
          <span
            className="rc-value"
            style={{ color: isZero ? "var(--muted)" : "var(--fg)" }}
          >
            {value}
          </span>
        )}
      </div>

      <div className="rc-footer">
        <span className="rc-label">{label}</span>
        <span className="rc-sub">{sublabel}</span>
      </div>

      <div className="rc-bar">
        <span
          className="rc-bar-fill"
          style={{
            width: loading || value === null ? "0%" : isZero ? "4%" : "38%",
          }}
        />
      </div>
    </div>
  );
}

// ─── Sidebar Nav Item ─────────────────────────────────────────────────────────
function NavBtn({
  id,
  label,
  icon,
  active,
  badge,
  onClick,
}: {
  id: NavItem;
  label: string;
  icon: string;
  active: boolean;
  badge?: number;
  onClick: () => void;
}) {
  return (
    <button
      className={`nav-btn ${active ? "nav-btn--active" : ""}`}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
    >
      <span className="nav-icon" aria-hidden>
        {icon}
      </span>
      <span className="nav-label">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="nav-badge">{badge}</span>
      )}
    </button>
  );
}

// ─── Clock ────────────────────────────────────────────────────────────────────
function LiveClock() {
  const [time, setTime] = useState("");
  useEffect(() => {
    const tick = () =>
      setTime(
        new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
          timeZone: "UTC",
        }),
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="clock">{time}</span>;
}

// ─── Status Pill ──────────────────────────────────────────────────────────────
function StatusPill({ live, loading }: { live: boolean; loading: boolean }) {
  if (loading)
    return (
      <span className="pill pill--connecting">
        <span className="pill-dot" />
        CONNECTING
      </span>
    );
  return (
    <span className={`pill ${live ? "pill--live" : "pill--offline"}`}>
      <span className={`pill-dot ${live ? "pill-dot--pulse" : ""}`} />
      {live ? "LIVE · AZURE" : "OFFLINE"}
    </span>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Home() {
  const { data, loading, error } = useCloudResources();
  const groqCalls = useGroqStats();
  const [activeNav, setActiveNav] = useState<NavItem>("overview");
  const isLive = data?.mode === "live";

  // Cognitive Services count if returned by the API (future-proof)
  const cognitiveCount =
    ((data as Record<string, unknown> | null)?.cognitive_services as
      | number
      | null) ?? null;

  const resourceCards: Omit<ResourceCardProps, "index">[] = [
    {
      label: "Total Resources",
      sublabel: "subscription",
      value: data?.total ?? null,
      accent: "#2dd4bf",
      icon: "◈",
      loading,
      region: "eastus",
    },
    {
      label: "Cognitive Services",
      sublabel: "AI · ml workloads",
      value: cognitiveCount,
      accent: "#a78bfa",
      icon: "⬡",
      loading,
      region: "eastus · eastus2",
    },
    {
      label: "Storage Accounts",
      sublabel: "blob · file · queue",
      value: data?.storage_accounts ?? null,
      accent: "#facc15",
      icon: "▦",
      loading,
      region: "eastus",
    },
    {
      label: "Virtual Machines",
      sublabel: "compute · iaas",
      value: data?.virtual_machines ?? null,
      accent: "#60a5fa",
      icon: "▣",
      loading,
    },
    {
      label: "AKS Clusters",
      sublabel: "kubernetes",
      value: data?.aks_clusters ?? null,
      accent: "#34d399",
      icon: "⬡",
      loading,
    },
    {
      label: "App Services",
      sublabel: "paas · web apps",
      value: data?.app_services ?? null,
      accent: "#fb923c",
      icon: "◇",
      loading,
    },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,700;1,400&family=Syne:wght@600;700;800&display=swap');

        /* ── Reset ───────────────────────────────────────────────────────── */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        button { font-family: inherit; cursor: pointer; }

        /* ── Design tokens ───────────────────────────────────────────────── */
        :root {
          --bg-root:    #070a0e;
          --bg-panel:   #0b1018;
          --bg-raised:  #0f1520;
          --bg-hover:   #141c26;
          --border:     #141c26;
          --border-mid: #1e2a38;
          --fg:         #d4dde8;
          --fg-mid:     #7a8fa6;
          --fg-dim:     #3d5066;
          --muted:      #2d3d52;
          --accent:     #2dd4bf;
          --green:      #34d399;
          --yellow:     #facc15;
          --red:        #f87171;
          --blue:       #60a5fa;
          --purple:     #a78bfa;
          --orange:     #fb923c;

          --sidebar-w:  200px;
          --header-h:   52px;
          --font-mono:  'JetBrains Mono', monospace;
          --font-disp:  'Syne', sans-serif;
          --radius-sm:  6px;
          --radius-md:  9px;
        }

        /* ── Base ────────────────────────────────────────────────────────── */
        body {
          background: var(--bg-root);
          color: var(--fg-mid);
          font-family: var(--font-mono);
          min-height: 100vh;
          /* scanline texture */
          background-image: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255,255,255,0.009) 2px,
            rgba(255,255,255,0.009) 4px
          );
        }

        /* ── App shell ───────────────────────────────────────────────────── */
        .app {
          display: grid;
          grid-template-rows: var(--header-h) 1fr;
          grid-template-columns: var(--sidebar-w) 1fr;
          grid-template-areas:
            "topbar topbar"
            "sidebar main";
          min-height: 100vh;
        }

        /* ── Topbar ──────────────────────────────────────────────────────── */
        .topbar {
          grid-area: topbar;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 20px 0 0;
          border-bottom: 1px solid var(--border);
          background: rgba(7,10,14,0.9);
          backdrop-filter: blur(8px);
          position: sticky;
          top: 0;
          z-index: 50;
        }
        .topbar-brand {
          display: flex;
          align-items: center;
          gap: 0;
          width: var(--sidebar-w);
          padding: 0 16px;
          height: 100%;
          border-right: 1px solid var(--border);
        }
        .topbar-logo {
          width: 28px; height: 28px;
          border: 1px solid rgba(45,212,191,0.2);
          border-radius: 7px;
          background: #0d1520;
          display: flex; align-items: center; justify-content: center;
          font-size: 13px;
          flex-shrink: 0;
          margin-right: 10px;
        }
        .topbar-title {
          font-family: var(--font-disp);
          font-size: 14px;
          font-weight: 800;
          color: var(--fg);
          letter-spacing: -0.3px;
          white-space: nowrap;
        }
        .topbar-sub {
          font-size: 8px;
          color: var(--muted);
          letter-spacing: 0.1em;
          text-transform: uppercase;
          margin-top: 2px;
        }
        .topbar-right {
          display: flex;
          align-items: center;
          gap: 20px;
        }
        .topbar-stat {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
        }
        .topbar-stat-key {
          font-size: 8px;
          color: var(--muted);
          letter-spacing: 0.1em;
          text-transform: uppercase;
        }
        .topbar-stat-val {
          font-family: var(--font-disp);
          font-size: 16px;
          font-weight: 700;
          color: var(--fg);
          line-height: 1.1;
        }
        .topbar-divider {
          width: 1px; height: 24px;
          background: var(--border);
        }
        .clock {
          font-family: var(--font-mono);
          font-size: 12px;
          font-weight: 700;
          color: var(--fg-dim);
          letter-spacing: 0.08em;
          font-variant-numeric: tabular-nums;
        }

        /* ── Sidebar ─────────────────────────────────────────────────────── */
        .sidebar {
          grid-area: sidebar;
          border-right: 1px solid var(--border);
          padding: 20px 12px;
          display: flex;
          flex-direction: column;
          gap: 3px;
          position: sticky;
          top: var(--header-h);
          height: calc(100vh - var(--header-h));
          overflow-y: auto;
        }
        .sidebar-section {
          font-size: 8px;
          font-weight: 700;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--fg-dim);
          padding: 0 8px;
          margin: 14px 0 6px;
        }
        .sidebar-section:first-child { margin-top: 0; }

        /* ── Nav Button ──────────────────────────────────────────────────── */
        .nav-btn {
          display: flex;
          align-items: center;
          gap: 9px;
          width: 100%;
          padding: 8px 10px;
          border-radius: var(--radius-sm);
          border: 1px solid transparent;
          background: transparent;
          color: var(--muted);
          font-size: 11px;
          font-weight: 500;
          text-align: left;
          transition: all 0.15s;
          letter-spacing: 0.02em;
          position: relative;
        }
        .nav-btn:hover {
          background: var(--bg-hover);
          color: var(--fg-mid);
          border-color: var(--border);
        }
        .nav-btn--active {
          background: rgba(45,212,191,0.07);
          border-color: rgba(45,212,191,0.2);
          color: var(--accent);
        }
        .nav-btn--active .nav-icon { opacity: 1; }
        .nav-icon {
          font-size: 11px;
          opacity: 0.6;
          flex-shrink: 0;
          width: 14px;
          text-align: center;
        }
        .nav-label { flex: 1; }
        .nav-badge {
          font-size: 8px;
          font-weight: 700;
          padding: 1px 5px;
          border-radius: 100px;
          background: rgba(248,113,113,0.12);
          color: var(--red);
          border: 1px solid rgba(248,113,113,0.2);
        }

        /* Sidebar bottom info */
        .sidebar-footer {
          margin-top: auto;
          padding-top: 16px;
          border-top: 1px solid var(--border);
          font-size: 8px;
          color: var(--fg-dim);
          line-height: 2;
          padding-left: 10px;
        }
        .sidebar-footer b { color: var(--muted); font-weight: 500; }

        /* ── Main content ────────────────────────────────────────────────── */
        .main {
          grid-area: main;
          padding: 24px 24px 48px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 0;
        }

        /* ── Page header inside main ─────────────────────────────────────── */
        .page-head {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 20px;
        }
        .page-title {
          font-family: var(--font-disp);
          font-size: 22px;
          font-weight: 800;
          color: var(--fg);
          letter-spacing: -0.5px;
          line-height: 1;
        }
        .page-title-sub {
          font-size: 10px;
          color: var(--fg-dim);
          margin-top: 5px;
          letter-spacing: 0.05em;
        }

        /* ── Status pill ─────────────────────────────────────────────────── */
        .pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 5px 11px 5px 9px;
          border-radius: 100px;
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.1em;
          border: 1px solid;
        }
        .pill--live {
          color: var(--green);
          border-color: rgba(52,211,153,0.25);
          background: rgba(52,211,153,0.06);
        }
        .pill--offline {
          color: var(--fg-dim);
          border-color: var(--border);
          background: transparent;
        }
        .pill--connecting {
          color: var(--muted);
          border-color: var(--border-mid);
          background: transparent;
        }
        .pill-dot {
          width: 5px; height: 5px;
          border-radius: 50%;
          background: currentColor;
          flex-shrink: 0;
        }
        .pill-dot--pulse { animation: pulse 2s ease-in-out infinite; }
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.6)} }

        /* ── Resource card grid ──────────────────────────────────────────── */
        .rc-grid {
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          gap: 10px;
          margin-bottom: 24px;
        }
        @media (max-width: 1280px) { .rc-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 800px)  { .rc-grid { grid-template-columns: repeat(2, 1fr); } }

        /* ── Resource card ───────────────────────────────────────────────── */
        .rc {
          background: var(--bg-panel);
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          padding: 14px 15px 11px;
          position: relative;
          overflow: hidden;
          transition: border-color 0.2s, transform 0.15s;
          animation: fadeUp 0.4s ease both;
          animation-delay: var(--delay, 0ms);
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .rc:hover {
          border-color: var(--border-mid);
          transform: translateY(-1px);
        }
        /* top glow line */
        .rc::before {
          content: '';
          position: absolute; top: 0; left: 0; right: 0; height: 1px;
          background: linear-gradient(90deg, transparent, var(--accent) 40%, transparent);
          opacity: 0.35;
        }
        /* corner accent pip */
        .rc-corner {
          position: absolute;
          top: 10px; right: 10px;
          width: 4px; height: 4px;
          border-radius: 50%;
          background: var(--accent);
          opacity: 0.3;
        }
        .rc-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .rc-icon {
          font-size: 12px;
          color: var(--accent);
          line-height: 1;
        }
        .rc-region {
          font-size: 7.5px;
          color: var(--fg-dim);
          letter-spacing: 0.08em;
          text-transform: uppercase;
          max-width: 80px;
          text-align: right;
          line-height: 1.3;
        }
        .rc-value-wrap {
          margin-bottom: 12px;
          min-height: 34px;
          display: flex;
          align-items: center;
        }
        .rc-value {
          font-family: var(--font-disp);
          font-size: 32px;
          font-weight: 800;
          letter-spacing: -1px;
          line-height: 1;
          transition: color 0.3s;
        }
        .rc-null {
          font-family: var(--font-disp);
          font-size: 32px;
          font-weight: 800;
          color: var(--border-mid);
        }
        .rc-skeleton {
          display: inline-block;
          width: 36px; height: 26px;
          border-radius: 4px;
          background: linear-gradient(90deg, #141c26 25%, #1e2a38 50%, #141c26 75%);
          background-size: 200% 100%;
          animation: shimmer 1.6s infinite;
        }
        @keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
        .rc-footer {
          display: flex;
          flex-direction: column;
          gap: 2px;
          margin-bottom: 10px;
        }
        .rc-label {
          font-size: 9.5px;
          font-weight: 700;
          color: var(--fg-mid);
          letter-spacing: 0.04em;
        }
        .rc-sub {
          font-size: 8px;
          color: var(--fg-dim);
          letter-spacing: 0.06em;
        }
        .rc-bar {
          height: 2px;
          background: var(--border);
          border-radius: 1px;
          overflow: hidden;
        }
        .rc-bar-fill {
          display: block;
          height: 100%;
          background: var(--accent);
          border-radius: 1px;
          transition: width 0.8s ease;
          opacity: 0.6;
        }

        /* ── Section label ───────────────────────────────────────────────── */
        .section-lbl {
          font-size: 8.5px;
          font-weight: 700;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--fg-dim);
          margin-bottom: 10px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .section-lbl::after {
          content: '';
          flex: 1;
          height: 1px;
          background: var(--border);
        }

        /* ── Panel ───────────────────────────────────────────────────────── */
        .panel {
          background: var(--bg-panel);
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          position: relative;
          overflow: hidden;
        }
        .panel::before {
          content: '';
          position: absolute; top: 0; left: 0; right: 0; height: 1px;
          background: linear-gradient(90deg, transparent, rgba(45,212,191,0.12), transparent);
          pointer-events: none;
        }
        .panel-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid var(--border);
          background: rgba(255,255,255,0.01);
        }
        .panel-title {
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--fg-dim);
        }
        .panel-body { padding: 16px; }

        /* ── Content grid (chart + alerts side-by-side) ──────────────────── */
        .content-grid {
          display: grid;
          grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
          gap: 12px;
          margin-bottom: 24px;
        }
        @media (max-width: 1000px) { .content-grid { grid-template-columns: 1fr; } }

        .left-col { display: flex; flex-direction: column; gap: 12px; }
        .right-col { display: flex; flex-direction: column; gap: 12px; }

        /* ── Agent panel container ───────────────────────────────────────── */
        .agent-wrap {
          background: var(--bg-panel);
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          overflow: hidden;
          min-height: 520px;
          max-height: 680px;
          display: flex;
          flex-direction: column;
          position: relative;
        }
        .agent-wrap::before {
          content: '';
          position: absolute; top: 0; left: 0; right: 0; height: 1px;
          background: linear-gradient(90deg, transparent, rgba(52,211,153,0.2), transparent);
          pointer-events: none;
        }

        /* ── Analysis panel container (full width) ───────────────────────── */
        .analysis-wrap {
          background: var(--bg-panel);
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          overflow: hidden;
          margin-bottom: 24px;
          position: relative;
        }
        .analysis-wrap::before {
          content: '';
          position: absolute; top: 0; left: 0; right: 0; height: 1px;
          background: linear-gradient(90deg, transparent, rgba(45,212,191,0.12), transparent);
          pointer-events: none;
        }

        /* ── Recharts overrides ──────────────────────────────────────────── */
        .recharts-cartesian-axis-tick-value {
          font-size: 9px !important;
          fill: var(--muted) !important;
          font-family: var(--font-mono) !important;
        }
        .recharts-legend-item-text { font-size: 9px !important; color: var(--muted) !important; }
        .recharts-cartesian-grid line { stroke: #0f1922 !important; }
        .recharts-tooltip-wrapper .chart-tooltip {
          background: var(--bg-raised) !important;
          border: 1px solid var(--border-mid) !important;
          border-radius: var(--radius-md) !important;
          padding: 9px 13px !important;
          font-size: 10px !important;
        }

        /* ── AgentPanel pass-through ─────────────────────────────────────── */
        .agent-panel { background: transparent !important; border: none !important; border-radius: 0 !important; flex: 1; overflow: hidden; }
        .agent-header { display:flex; align-items:center; gap:9px; padding:12px 18px; border-bottom:1px solid var(--border); background:rgba(255,255,255,0.01); flex-wrap:wrap; }
        .agent-header-title { font-family:var(--font-mono); font-size:9px; font-weight:700; color:var(--fg-dim); letter-spacing:0.14em; text-transform:uppercase; }
        .agent-selector { display:flex; gap:4px; margin-left:auto; flex-wrap:wrap; }
        .agent-btn { font-family:var(--font-mono); font-size:9px; padding:3px 8px; border-radius:4px; border:1px solid; cursor:pointer; transition:all 0.15s; background:transparent; }
        .agent-btn.active  { border-color:var(--green); background:rgba(52,211,153,.1); color:var(--green); }
        .agent-btn.inactive{ border-color:var(--border); color:var(--muted); }
        .agent-btn.inactive:hover { border-color:var(--border-mid); color:var(--fg-dim); }
        .agent-clear { font-family:var(--font-mono); font-size:9px; color:var(--border-mid); background:transparent; border:none; cursor:pointer; padding:2px 6px; letter-spacing:.04em; }
        .agent-clear:hover { color:var(--muted); }
        .agent-log { flex:1; overflow-y:auto; padding:14px 18px; display:flex; flex-direction:column; scrollbar-width:thin; scrollbar-color:var(--border) transparent; }
        .agent-log::-webkit-scrollbar { width:3px; }
        .agent-log::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }
        .agent-empty { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:7px; color:var(--border-mid); font-size:11px; text-align:center; padding:32px; }
        .agent-empty-icon { font-size:20px; opacity:.4; }
        .agent-empty-hint { font-size:9px; color:var(--border); margin-top:4px; }
        .agent-msg { display:flex; flex-direction:column; margin-bottom:14px; }
        .agent-msg.user { align-items:flex-end; }
        .agent-msg.response { align-items:flex-start; }
        .agent-meta { display:flex; align-items:center; gap:5px; margin-bottom:4px; flex-wrap:wrap; }
        .agent-label-badge { font-size:9px; font-weight:700; padding:2px 7px; border-radius:4px; border:1px solid rgba(52,211,153,.25); background:rgba(52,211,153,.07); color:var(--green); letter-spacing:.06em; font-family:var(--font-mono); }
        .agent-status-dot { width:5px; height:5px; border-radius:50%; flex-shrink:0; }
        .agent-status-text { font-size:9px; font-family:var(--font-mono); letter-spacing:.06em; }
        .agent-confidence { font-size:9px; color:var(--border-mid); font-family:var(--font-mono); }
        .agent-mock-tag { font-size:8px; padding:1px 5px; border-radius:3px; border:1px solid rgba(250,204,21,.18); background:rgba(250,204,21,.05); color:var(--yellow); font-family:var(--font-mono); letter-spacing:.06em; }
        .agent-bubble { max-width:82%; padding:9px 13px; font-size:11px; line-height:1.75; white-space:pre-wrap; word-break:break-word; color:var(--fg-mid); }
        .agent-bubble.user { background:rgba(52,211,153,.07); border:1px solid rgba(52,211,153,.18); border-radius:9px 9px 2px 9px; color:#c8eedd; }
        .agent-bubble.response { background:rgba(255,255,255,.015); border:1px solid var(--border); border-radius:9px 9px 9px 2px; }
        .agent-ts { font-size:8px; color:var(--border-mid); margin-top:3px; font-family:var(--font-mono); }
        .agent-thinking { display:flex; align-items:center; gap:7px; color:var(--border-mid); font-size:10px; margin-bottom:10px; }
        .agent-thinking-dot { width:5px; height:5px; border-radius:50%; background:var(--green); animation:pulse 1.2s ease-in-out infinite; flex-shrink:0; }
        .agent-error { font-size:10px; color:var(--red); background:rgba(248,113,113,.05); border:1px solid rgba(248,113,113,.12); border-radius:5px; padding:7px 11px; margin-bottom:7px; }
        .agent-input-row { display:flex; gap:8px; padding:10px 18px 14px; border-top:1px solid var(--border); align-items:flex-end; }
        .agent-textarea { flex:1; background:var(--bg-root); border:1px solid var(--border); border-radius:6px; padding:8px 12px; font-family:var(--font-mono); font-size:11px; color:var(--fg); outline:none; resize:none; line-height:1.5; transition:border-color .2s; }
        .agent-textarea::placeholder { color:var(--border-mid); }
        .agent-textarea:focus { border-color:rgba(52,211,153,0.2); }
        .agent-send { background:rgba(52,211,153,.1); border:1px solid rgba(52,211,153,.25); color:var(--green); font-family:var(--font-mono); font-size:10px; font-weight:700; padding:8px 14px; border-radius:6px; cursor:pointer; letter-spacing:.06em; transition:background .2s; white-space:nowrap; }
        .agent-send:hover { background:rgba(52,211,153,.18); }
        .agent-send:disabled { opacity:.3; cursor:not-allowed; }

        /* ── AlertsPanel pass-through ────────────────────────────────────── */
        .alert-item { display:flex; align-items:flex-start; gap:9px; padding:9px 12px; border-radius:6px; border:1px solid; margin-bottom:7px; font-size:11px; line-height:1.5; }
        .alert-dot { width:5px; height:5px; border-radius:50%; margin-top:3px; flex-shrink:0; }
        .alert-none { color:var(--green); font-size:11px; display:flex; align-items:center; gap:7px; }

        /* ── AnalysisPanel pass-through ──────────────────────────────────── */
        .analysis-text { font-size:11px; color:var(--fg-mid); line-height:1.9; white-space:pre-wrap; }
        .analysis-loading { display:flex; gap:4px; align-items:center; color:var(--muted); font-size:11px; }
        .dot-anim span { display:inline-block; animation:blink 1.2s infinite; animation-fill-mode:both; }
        .dot-anim span:nth-child(2){animation-delay:.2s}
        .dot-anim span:nth-child(3){animation-delay:.4s}
        @keyframes blink{0%,80%,100%{opacity:.2}40%{opacity:1}}

        /* ── Scrollbar global ────────────────────────────────────────────── */
        ::-webkit-scrollbar { width:3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

        /* ── View transitions ────────────────────────────────────────────── */
        .view { animation: viewIn 0.2s ease; }
        @keyframes viewIn { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }

        /* ── Empty state inside alerts panel ─────────────────────────────── */
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 40px 20px;
          color: var(--border-mid);
          text-align: center;
        }
        .empty-state-icon { font-size: 22px; opacity: 0.4; }
        .empty-state-text { font-size: 11px; color: var(--muted); }
        .empty-state-sub { font-size: 9px; color: var(--fg-dim); margin-top: 2px; }
      `}</style>

      <div className="app">
        {/* ── TOPBAR ──────────────────────────────────────────────────────── */}
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
            <StatusPill live={isLive} loading={loading} />
          </div>
        </header>

        {/* ── SIDEBAR ─────────────────────────────────────────────────────── */}
        <nav className="sidebar">
          <span className="sidebar-section">Views</span>
          <NavBtn
            id="overview"
            label="Overview"
            icon="◈"
            active={activeNav === "overview"}
            onClick={() => setActiveNav("overview")}
          />
          <NavBtn
            id="agent"
            label="AI Copilot"
            icon="⬡"
            active={activeNav === "agent"}
            onClick={() => setActiveNav("agent")}
          />
          <NavBtn
            id="analysis"
            label="Analysis"
            icon="◇"
            active={activeNav === "analysis"}
            onClick={() => setActiveNav("analysis")}
          />
          <NavBtn
            id="alerts"
            label="Alerts"
            icon="▲"
            active={activeNav === "alerts"}
            badge={0}
            onClick={() => setActiveNav("alerts")}
          />

          <span className="sidebar-section">Subscription</span>

          <div className="sidebar-footer">
            <div>
              <b>Sub</b> d91323a4
            </div>
            <div>
              <b>RG</b> rg-finops-prod
            </div>
            <div>
              <b>Region</b> eastus
            </div>
            <div>
              <b>Model</b> llama-3.1-8b
            </div>
            <div>
              <b>Mode</b>{" "}
              {loading ? "…" : data?.mode === "live" ? "live" : "mock"}
            </div>
          </div>
        </nav>

        {/* ── MAIN ─────────────────────────────────────────────────────────── */}
        <main className="main">
          {/* Overview */}
          {activeNav === "overview" && (
            <div className="view">
              <div className="page-head">
                <div>
                  <div className="page-title">Resource Overview</div>
                  <div className="page-title-sub">
                    Azure subscription · live inventory
                  </div>
                </div>
                <StatusPill live={isLive} loading={loading} />
              </div>

              {/* Resource inventory cards */}
              <p className="section-lbl">Resource Inventory</p>
              <div className="rc-grid">
                {resourceCards.map((card, i) => (
                  <ResourceCard key={card.label} {...card} index={i} />
                ))}
              </div>

              {/* Chart + Alerts */}
              <p className="section-lbl">Monitoring</p>
              <div className="content-grid">
                <div className="left-col">
                  <div className="panel">
                    <CloudIntelligence
                      data={data}
                      loading={loading}
                      error={error}
                    />
                  </div>
                </div>

                <div className="right-col">
                  <div className="panel" style={{ flex: 1 }}>
                    <div className="panel-head">
                      <span className="panel-title">Active Alerts</span>
                    </div>
                    <div className="panel-body">
                      <AlertsPanel rawAlerts={[]} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Copilot */}
          {activeNav === "agent" && (
            <div className="view">
              <div className="page-head">
                <div>
                  <div className="page-title">AI Copilot</div>
                  <div className="page-title-sub">
                    Multi-agent · Router → Operational / Security / FinOps
                  </div>
                </div>
              </div>
              <div className="agent-wrap">
                <AgentPanel />
              </div>
            </div>
          )}

          {/* Analysis */}
          {activeNav === "analysis" && (
            <div className="view">
              <div className="page-head">
                <div>
                  <div className="page-title">AI Incident Analysis</div>
                  <div className="page-title-sub">
                    Groq llama-3.1-8b · on-demand
                  </div>
                </div>
              </div>
              <div className="analysis-wrap">
                <AnalysisPanel />
              </div>
            </div>
          )}

          {/* Alerts */}
          {activeNav === "alerts" && (
            <div className="view">
              <div className="page-head">
                <div>
                  <div className="page-title">Active Alerts</div>
                  <div className="page-title-sub">
                    Prometheus alertmanager · real-time
                  </div>
                </div>
              </div>
              <div className="panel">
                <div className="panel-head">
                  <span className="panel-title">Alert Feed</span>
                </div>
                <div className="panel-body">
                  <AlertsPanel rawAlerts={[]} />
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
