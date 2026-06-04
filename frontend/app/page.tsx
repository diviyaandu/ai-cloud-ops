"use client";

import "@/styles/global.css";
import "@/styles/layout.css";
import "@/styles/cards.css";
import "@/styles/dashboard.css";
import "@/styles/filters.css";
import "@/styles/chat.css";
import "@/styles/alerts.css";
import "@/styles/analysis.css";

import { useState, useEffect } from "react";
import {
  useCloudResources,
  useTagValues,
  useFilteredResources,
} from "@/hooks/useCloudResources";
import CloudIntelligence from "@/components/dashboard/CloudIntelligence";
import AlertsPanel from "@/components/dashboard/AlertsPanel";
import AnalysisPanel from "@/components/dashboard/AnalysisPanel";
import AgentPanel from "@/components/chat/AgentPanel";

// ─── Groq Stats ───────────────────────────────────────────────────────────────
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

// ─── Helpers ──────────────────────────────────────────────────────────────────
const TYPE_ACCENTS: Record<string, string> = {
  "microsoft.compute/virtualmachines": "#60a5fa",
  "microsoft.containerservice/managedclusters": "#34d399",
  "microsoft.web/sites": "#fb923c",
  "microsoft.storage/storageaccounts": "#facc15",
  "microsoft.cognitiveservices/accounts": "#a78bfa",
};
const DEFAULT_ACCENT = "#2dd4bf";

function labelFor(type: string): string {
  const short = type.split("/").pop() ?? type;
  return short.replace(/([a-z])([A-Z])/g, "$1 $2");
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

// ─── Sidebar Nav Button ───────────────────────────────────────────────────────
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

// ─── Tag Filter Bar ───────────────────────────────────────────────────────────
function TagFilterBar({
  tagValues,
  activeFilters,
  onFilter,
  onClear,
}: {
  tagValues: Record<string, string[]>;
  activeFilters: Record<string, string>;
  onFilter: (key: string, value: string) => void;
  onClear: () => void;
}) {
  const keys = ["Project", "Environment", "Owner", "Application"];
  const hasActive = Object.values(activeFilters).some(Boolean);
  return (
    <div className="tag-filter-bar">
      {keys.map((k) => (
        <select
          key={k}
          value={activeFilters[k] || ""}
          onChange={(e) => onFilter(k, e.target.value)}
          className="tag-select"
        >
          <option value="">{k}</option>
          {(tagValues[k] || []).map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      ))}
      {hasActive && (
        <button className="tag-clear" onClick={onClear}>
          ✕ Clear
        </button>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Home() {
  const { data, loading, error } = useCloudResources();
  const groqCalls = useGroqStats();
  const [activeNav, setActiveNav] = useState<NavItem>("overview");
  const isLive = data?.mode === "live";

  // Tag filters
  const [tagFilters, setTagFilters] = useState<Record<string, string>>({});
  const tagValues = useTagValues();
  const { data: filteredData } = useFilteredResources(tagFilters);

  // Resource type search + multi-select
  const allTypes: string[] = (data?.raw_by_type ?? []).map((r) => r.type);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (data?.raw_by_type) setSelected(new Set(allTypes));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const filteredTypes = (data?.raw_by_type ?? []).filter((r) => {
    const matchesSearch = r.type.toLowerCase().includes(search.toLowerCase());
    const matchesSelected = selected.size === 0 || selected.has(r.type);
    return matchesSearch && matchesSelected;
  });

  const allSelected = selected.size === allTypes.length;

  return (
    <>
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
          {/* ── Overview ── */}
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

              {/* Resource Inventory */}
              <p className="section-lbl">Resource Inventory</p>

              {/* Search + type chips */}
              <div className="ri-toolbar">
                <input
                  className="ri-search"
                  placeholder="Search resource types…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <div className="ri-multiselect">
                  <button
                    className="ri-btn"
                    onClick={() =>
                      setSelected(allSelected ? new Set() : new Set(allTypes))
                    }
                  >
                    {allSelected ? "Deselect All" : "Select All"}
                  </button>
                  {allTypes.map((t) => (
                    <button
                      key={t}
                      className={`ri-chip ${selected.has(t) ? "ri-chip--on" : ""}`}
                      onClick={() => {
                        const next = new Set(selected);
                        next.has(t) ? next.delete(t) : next.add(t);
                        setSelected(next);
                      }}
                    >
                      {labelFor(t)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="rc-grid">
                {/* Total — always visible */}
                <ResourceCard
                  key="total"
                  index={0}
                  label="Total Resources"
                  sublabel="subscription"
                  value={data?.total ?? null}
                  accent="#2dd4bf"
                  icon="◈"
                  loading={loading}
                  region="all regions"
                />
                {/* Dynamic cards — one per resource type */}
                {filteredTypes.map((r, i) => (
                  <ResourceCard
                    key={r.type}
                    index={i + 1}
                    label={labelFor(r.type)}
                    sublabel={r.type.split("/")[0].replace("microsoft.", "")}
                    value={r.count}
                    accent={
                      TYPE_ACCENTS[r.type.toLowerCase()] ?? DEFAULT_ACCENT
                    }
                    icon="◇"
                    loading={loading}
                    region={r.regions?.join(" · ")}
                  />
                ))}
              </div>

              {/* Tag Filters */}
              <TagFilterBar
                tagValues={tagValues}
                activeFilters={tagFilters}
                onFilter={(k, v) => setTagFilters((f) => ({ ...f, [k]: v }))}
                onClear={() => setTagFilters({})}
              />
              {filteredData && (
                <div className="filter-results">
                  <span>{filteredData.total} resources matched</span>
                </div>
              )}

              {/* Monitoring */}
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

          {/* ── AI Copilot ── */}
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

          {/* ── Analysis ── */}
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

          {/* ── Alerts ── */}
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
