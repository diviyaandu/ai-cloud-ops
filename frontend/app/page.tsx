"use client";

import { useState } from "react";
import { useCloudResources } from "@/hooks/useCloudResources";

import Header from "@/components/layout/Header";
import CloudStatCard from "@/components/dashboard/CloudStatCard";
import MetricsChart from "@/components/dashboard/MetricsChart";
import AlertsPanel from "@/components/dashboard/AlertsPanel";
import AnalysisPanel from "@/components/dashboard/AnalysisPanel";
import AgentPanel from "@/components/chat/AgentPanel";

export default function Home() {
  const { data, loading } = useCloudResources();
  const [groqCalls, setGroqCalls] = useState(0);

  // Derive a simple overall health pill from unhealthy count (extend later)
  const health = data ? "LIVE" : "LOADING";
  const color = data ? "#34d399" : "#4b5563";

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;700;800&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #080b0f; color: #c9d1d9; font-family: 'JetBrains Mono', monospace; min-height: 100vh; }
        .dashboard { max-width: 1400px; margin: 0 auto; padding: 28px 24px 48px; }
        .header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid #1e2a38; }
        .header-title { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800; color: #e6edf3; letter-spacing: -0.5px; }
        .header-sub { font-size: 11px; color: #4a5568; margin-top: 4px; letter-spacing: 0.06em; text-transform: uppercase; }
        .header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
        .health-pill { display: flex; align-items: center; gap: 7px; padding: 5px 13px; border-radius: 100px; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; border: 1px solid; }
        .health-dot { width: 6px; height: 6px; border-radius: 50%; animation: pulse 2s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.75); } }
        .tick-counter { font-size: 10px; color: #374151; letter-spacing: 0.04em; }

        /* ── Cloud resource cards row ────────────────────────────────── */
        .cloud-cards-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 12px;
          margin-bottom: 16px;
        }
        @media (max-width: 1100px) { .cloud-cards-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 700px)  { .cloud-cards-grid { grid-template-columns: repeat(2, 1fr); } }

        /* mode badge */
        .mode-badge {
          display: inline-flex; align-items: center; gap: 5px;
          font-size: 9px; font-weight: 700; letter-spacing: 0.1em;
          text-transform: uppercase; color: #34d399;
          background: rgba(52,211,153,0.06); border: 1px solid rgba(52,211,153,0.15);
          border-radius: 4px; padding: 2px 8px; margin-bottom: 12px;
        }
        .mode-dot { width: 5px; height: 5px; border-radius: 50%; background: #34d399; animation: pulse 2s ease-in-out infinite; }

        /* ── Main grid (chart + alerts + analysis + agent) ───────────── */
        .main-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
        .span-3 { grid-column: span 3; }
        .span-2 { grid-column: span 2; }
        .span-1 { grid-column: span 1; }
        @media (max-width: 960px) { .main-grid { grid-template-columns: 1fr 1fr; } .span-3, .span-2 { grid-column: span 2; } }
        @media (max-width: 620px) { .main-grid { grid-template-columns: 1fr; } .span-3, .span-2, .span-1 { grid-column: span 1; } }

        .panel { background: #0d1117; border: 1px solid #1e2a38; border-radius: 10px; padding: 20px; position: relative; overflow: hidden; }
        .panel::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, #2dd4bf22, transparent); }
        .panel-title { font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700; color: #4b5563; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 16px; }
        .stat-card { background: #0d1117; border: 1px solid #1e2a38; border-radius: 10px; padding: 18px 20px; position: relative; overflow: hidden; }
        .stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, #2dd4bf22, transparent); }
        .stat-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
        .stat-label { font-size: 10px; font-weight: 700; color: #4b5563; letter-spacing: 0.12em; text-transform: uppercase; }
        .stat-badge { font-size: 9px; font-weight: 700; padding: 2px 7px; border-radius: 4px; border: 1px solid; letter-spacing: 0.08em; }
        .stat-value { font-family: 'Syne', sans-serif; font-size: 38px; font-weight: 800; line-height: 1; margin-bottom: 14px; letter-spacing: -1px; }
        .stat-bar-track { height: 3px; background: #1e2a38; border-radius: 2px; overflow: hidden; }
        .stat-bar-fill { height: 100%; border-radius: 2px; transition: width 0.6s ease, background 0.3s; }
        .chart-tooltip { background: #0d1117; border: 1px solid #2a3748; border-radius: 8px; padding: 10px 14px; font-size: 11px; line-height: 1.7; }
        .tooltip-time { color: #4b5563; font-size: 10px; margin-bottom: 4px; letter-spacing: 0.06em; }
        .alert-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 14px; border-radius: 7px; border: 1px solid; margin-bottom: 8px; font-size: 12px; line-height: 1.5; }
        .alert-dot { width: 6px; height: 6px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
        .alert-none { color: #34d399; font-size: 12px; display: flex; align-items: center; gap: 8px; }
        .analysis-text { font-size: 12px; color: #9ca3af; line-height: 1.9; white-space: pre-wrap; }
        .analysis-loading { display: flex; gap: 4px; align-items: center; color: #4b5563; font-size: 12px; }
        .dot-anim span { display: inline-block; animation: blink 1.2s infinite; animation-fill-mode: both; }
        .dot-anim span:nth-child(2) { animation-delay: 0.2s; }
        .dot-anim span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }

        /* ── Agent panel styles ──────────────────────────────────────── */
        .agent-panel { background: #0d1117; border: 1px solid #1e2a38; border-radius: 10px; position: relative; overflow: hidden; display: flex; flex-direction: column; min-height: 420px; }
        .agent-panel::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, #34d39922, transparent); pointer-events: none; }
        .agent-header { display: flex; align-items: center; gap: 10px; padding: 14px 20px; border-bottom: 1px solid #1e2a38; background: rgba(255,255,255,0.01); flex-wrap: wrap; }
        .agent-header-title { font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700; color: #4b5563; letter-spacing: 0.12em; text-transform: uppercase; }
        .agent-selector { display: flex; gap: 4px; margin-left: auto; flex-wrap: wrap; }
        .agent-btn { font-family: 'JetBrains Mono', monospace; font-size: 10px; padding: 3px 9px; border-radius: 4px; border: 1px solid; cursor: pointer; transition: all 0.15s; background: transparent; }
        .agent-btn.active { border-color: #34d399; background: rgba(52,211,153,0.12); color: #34d399; }
        .agent-btn.inactive { border-color: #1e2a38; color: #4b5563; }
        .agent-btn.inactive:hover { border-color: #374151; color: #6b7280; }
        .agent-clear { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #2d3748; background: transparent; border: none; cursor: pointer; padding: 2px 6px; letter-spacing: 0.04em; }
        .agent-clear:hover { color: #4b5563; }
        .agent-log { flex: 1; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; scrollbar-width: thin; scrollbar-color: #1e2a38 transparent; }
        .agent-log::-webkit-scrollbar { width: 4px; }
        .agent-log::-webkit-scrollbar-thumb { background: #1e2a38; border-radius: 2px; }
        .agent-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: #2d3748; font-size: 12px; text-align: center; padding: 32px; }
        .agent-empty-icon { font-size: 24px; opacity: 0.5; }
        .agent-empty-hint { font-size: 10px; color: #1f2937; margin-top: 4px; }
        .agent-msg { display: flex; flex-direction: column; margin-bottom: 16px; }
        .agent-msg.user { align-items: flex-end; }
        .agent-msg.response { align-items: flex-start; }
        .agent-meta { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; flex-wrap: wrap; }
        .agent-label-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(52,211,153,0.3); background: rgba(52,211,153,0.08); color: #34d399; letter-spacing: 0.06em; font-family: 'JetBrains Mono', monospace; }
        .agent-status-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
        .agent-status-text { font-size: 10px; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.06em; }
        .agent-confidence { font-size: 10px; color: #2d3748; font-family: 'JetBrains Mono', monospace; }
        .agent-mock-tag { font-size: 9px; padding: 1px 6px; border-radius: 3px; border: 1px solid rgba(250,204,21,0.2); background: rgba(250,204,21,0.06); color: #facc15; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.06em; }
        .agent-bubble { max-width: 85%; padding: 10px 14px; font-size: 12px; line-height: 1.7; white-space: pre-wrap; word-break: break-word; color: #9ca3af; }
        .agent-bubble.user { background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.2); border-radius: 10px 10px 2px 10px; color: #d1fae5; }
        .agent-bubble.response { background: rgba(255,255,255,0.02); border: 1px solid #1e2a38; border-radius: 10px 10px 10px 2px; }
        .agent-ts { font-size: 9px; color: #1f2937; margin-top: 4px; font-family: 'JetBrains Mono', monospace; }
        .agent-thinking { display: flex; align-items: center; gap: 8px; color: #2d3748; font-size: 11px; margin-bottom: 12px; }
        .agent-thinking-dot { width: 6px; height: 6px; border-radius: 50%; background: #34d399; animation: pulse 1.2s ease-in-out infinite; flex-shrink: 0; }
        .agent-error { font-size: 11px; color: #f87171; background: rgba(248,113,113,0.06); border: 1px solid rgba(248,113,113,0.15); border-radius: 6px; padding: 8px 12px; margin-bottom: 8px; }
        .agent-input-row { display: flex; gap: 8px; padding: 12px 20px; border-top: 1px solid #1e2a38; align-items: flex-end; }
        .agent-textarea { flex: 1; background: #080b0f; border: 1px solid #1e2a38; border-radius: 6px; padding: 8px 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #c9d1d9; outline: none; resize: none; line-height: 1.5; transition: border-color 0.2s; }
        .agent-textarea::placeholder { color: #374151; }
        .agent-textarea:focus { border-color: #34d39944; }
        .agent-send { background: rgba(52,211,153,0.15); border: 1px solid rgba(52,211,153,0.35); color: #34d399; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; padding: 8px 14px; border-radius: 6px; cursor: pointer; letter-spacing: 0.06em; transition: background 0.2s; white-space: nowrap; }
        .agent-send:hover { background: rgba(52,211,153,0.25); }
        .agent-send:disabled { opacity: 0.35; cursor: not-allowed; }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1e2a38; border-radius: 2px; }
      `}</style>

      <div className="dashboard">
        <Header
          health={health}
          healthColor={color}
          tick={0}
          groqCalls={groqCalls}
        />

        {/* ── Cloud resource inventory cards ─────────────────────────── */}
        {data && (
          <div className="mode-badge">
            <span className="mode-dot" />
            {data.mode === "live" ? "Live · Azure Resource Graph" : "Mock data"}
          </div>
        )}

        <div className="cloud-cards-grid">
          <CloudStatCard
            label="Total Resources"
            value={data?.total ?? null}
            icon="◈"
            accent="#2dd4bf"
            loading={loading}
          />
          <CloudStatCard
            label="Virtual Machines"
            value={data?.virtual_machines ?? null}
            icon="⬡"
            accent="#60a5fa"
            loading={loading}
          />
          <CloudStatCard
            label="AKS Clusters"
            value={data?.aks_clusters ?? null}
            icon="⬡"
            accent="#a78bfa"
            loading={loading}
          />
          <CloudStatCard
            label="App Services"
            value={data?.app_services ?? null}
            icon="◇"
            accent="#34d399"
            loading={loading}
          />
          <CloudStatCard
            label="Storage Accounts"
            value={data?.storage_accounts ?? null}
            icon="▦"
            accent="#facc15"
            loading={loading}
          />
        </div>

        {/* ── Rest of dashboard ──────────────────────────────────────── */}
        <div className="main-grid">
          <MetricsChart history={[]} />
          <AlertsPanel rawAlerts={[]} />
          <AnalysisPanel onGroqCall={setGroqCalls} />
          <div className="span-2 agent-panel">
            <AgentPanel />
          </div>
        </div>
      </div>
    </>
  );
}
