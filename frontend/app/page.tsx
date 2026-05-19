"use client";

import { useEffect, useState, useRef } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const MAX_HISTORY = 20;

type MetricPoint = { t: string; cpu: number; memory: number; disk: number };
type Alert = { text: string; severity: "high" | "medium" | "low" };

function severityColor(v: number): string {
  if (v > 80) return "#f87171";
  if (v > 60) return "#facc15";
  return "#34d399";
}

function severityLabel(v: number): string {
  if (v > 80) return "CRIT";
  if (v > 60) return "WARN";
  return "OK";
}

function parseAlertSeverity(text: string): Alert["severity"] {
  const t = text.toLowerCase();
  if (t.includes("high") || t.includes("critical") || t.includes(">80"))
    return "high";
  if (t.includes("medium") || t.includes(">60")) return "medium";
  return "low";
}

function StatCard({
  label,
  value,
  unit = "%",
}: {
  label: string;
  value: number | null;
  unit?: string;
}) {
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

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-time">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.stroke }}>
          {p.name.toUpperCase()}: {p.value}%
        </p>
      ))}
    </div>
  );
}

export default function Home() {
  const [metrics, setMetrics] = useState<any>(null);
  const [history, setHistory] = useState<MetricPoint[]>([]);
  const [analysis, setAnalysis] = useState("");
  const [analysisLoading, setAnalysisLoading] = useState(true);

  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<
    { role: "user" | "ai"; text: string }[]
  >([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [tick, setTick] = useState(0);

  useEffect(() => {
    const fetchMetrics = () => {
      fetch("http://127.0.0.1:8000/metrics")
        .then((r) => r.json())
        .then((data) => {
          setMetrics(data);
          const now = new Date();
          const label = `${now.getHours().toString().padStart(2, "0")}:${now
            .getMinutes()
            .toString()
            .padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`;
          setHistory((prev) => [
            ...prev.slice(-(MAX_HISTORY - 1)),
            { t: label, cpu: data.cpu, memory: data.memory, disk: data.disk },
          ]);
          setTick((n) => n + 1);
        })
        .catch(() => {});
    };
    fetchMetrics();
    const id = setInterval(fetchMetrics, 3000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const fetchAnalysis = () => {
      setAnalysisLoading(true);
      fetch("http://127.0.0.1:8000/analyze")
        .then((r) => r.json())
        .then((data) => {
          setAnalysis(data.analysis);
          setAnalysisLoading(false);
        })
        .catch(() => setAnalysisLoading(false));
    };
    fetchAnalysis();
    const id = setInterval(fetchAnalysis, 10000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const sendChat = async () => {
    const msg = chatInput.trim();
    if (!msg || chatLoading) return;
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", text: msg }]);
    setChatLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      setChatMessages((prev) => [
        ...prev,
        { role: "ai", text: data.response || data.reply || "No response." },
      ]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: "ai", text: "Failed to reach the backend." },
      ]);
    }
    setChatLoading(false);
  };

  const alerts: Alert[] = (metrics?.alerts ?? []).map((t: string) => ({
    text: t,
    severity: parseAlertSeverity(t),
  }));

  const overallHealth = metrics
    ? metrics.cpu > 80 || metrics.memory > 80 || metrics.disk > 80
      ? "DEGRADED"
      : metrics.cpu > 60 || metrics.memory > 60 || metrics.disk > 60
        ? "WARNING"
        : "NOMINAL"
    : "UNKNOWN";

  const healthColor =
    overallHealth === "DEGRADED"
      ? "#f87171"
      : overallHealth === "WARNING"
        ? "#facc15"
        : overallHealth === "NOMINAL"
          ? "#34d399"
          : "#6b7280";

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;700;800&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          background: #080b0f;
          color: #c9d1d9;
          font-family: 'JetBrains Mono', monospace;
          min-height: 100vh;
        }

        .dashboard {
          max-width: 1280px;
          margin: 0 auto;
          padding: 28px 24px 48px;
        }

        /* ── Header ── */
        .header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 32px;
          padding-bottom: 20px;
          border-bottom: 1px solid #1e2a38;
        }
        .header-title {
          font-family: 'Syne', sans-serif;
          font-size: 28px;
          font-weight: 800;
          color: #e6edf3;
          letter-spacing: -0.5px;
        }
        .header-sub {
          font-size: 11px;
          color: #4a5568;
          margin-top: 4px;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }
        .header-right {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 6px;
        }
        .health-pill {
          display: flex;
          align-items: center;
          gap: 7px;
          padding: 5px 13px;
          border-radius: 100px;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.1em;
          border: 1px solid;
        }
        .health-dot {
          width: 6px; height: 6px;
          border-radius: 50%;
          animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.75); }
        }
        .tick-counter {
          font-size: 10px;
          color: #374151;
          letter-spacing: 0.04em;
        }

        /* ── Grid layout ── */
        .main-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          grid-template-rows: auto;
          gap: 16px;
        }
        .span-3 { grid-column: span 3; }
        .span-2 { grid-column: span 2; }
        .span-1 { grid-column: span 1; }

        @media (max-width: 960px) {
          .main-grid { grid-template-columns: 1fr 1fr; }
          .span-3 { grid-column: span 2; }
          .span-2 { grid-column: span 2; }
        }
        @media (max-width: 620px) {
          .main-grid { grid-template-columns: 1fr; }
          .span-3, .span-2 { grid-column: span 1; }
        }

        /* ── Panel ── */
        .panel {
          background: #0d1117;
          border: 1px solid #1e2a38;
          border-radius: 10px;
          padding: 20px;
          position: relative;
          overflow: hidden;
        }
        .panel::before {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 1px;
          background: linear-gradient(90deg, transparent, #2dd4bf22, transparent);
        }
        .panel-title {
          font-family: 'Syne', sans-serif;
          font-size: 12px;
          font-weight: 700;
          color: #4b5563;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          margin-bottom: 16px;
        }

        /* ── Stat card ── */
        .stat-card {
          background: #0d1117;
          border: 1px solid #1e2a38;
          border-radius: 10px;
          padding: 18px 20px;
          position: relative;
          overflow: hidden;
        }
        .stat-card::before {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 1px;
          background: linear-gradient(90deg, transparent, #2dd4bf22, transparent);
        }
        .stat-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .stat-label {
          font-size: 10px;
          font-weight: 700;
          color: #4b5563;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }
        .stat-badge {
          font-size: 9px;
          font-weight: 700;
          padding: 2px 7px;
          border-radius: 4px;
          border: 1px solid;
          letter-spacing: 0.08em;
        }
        .stat-value {
          font-family: 'Syne', sans-serif;
          font-size: 38px;
          font-weight: 800;
          line-height: 1;
          margin-bottom: 14px;
          letter-spacing: -1px;
        }
        .stat-bar-track {
          height: 3px;
          background: #1e2a38;
          border-radius: 2px;
          overflow: hidden;
        }
        .stat-bar-fill {
          height: 100%;
          border-radius: 2px;
          transition: width 0.6s ease, background 0.3s;
        }

        /* ── Chart ── */
        .chart-tooltip {
          background: #0d1117;
          border: 1px solid #2a3748;
          border-radius: 8px;
          padding: 10px 14px;
          font-size: 11px;
          line-height: 1.7;
        }
        .tooltip-time {
          color: #4b5563;
          font-size: 10px;
          margin-bottom: 4px;
          letter-spacing: 0.06em;
        }

        /* ── Alerts ── */
        .alert-item {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 10px 14px;
          border-radius: 7px;
          border: 1px solid;
          margin-bottom: 8px;
          font-size: 12px;
          line-height: 1.5;
        }
        .alert-dot {
          width: 6px; height: 6px;
          border-radius: 50%;
          margin-top: 4px;
          flex-shrink: 0;
        }
        .alert-none {
          color: #34d399;
          font-size: 12px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        /* ── AI Analysis ── */
        .analysis-text {
          font-size: 12px;
          color: #9ca3af;
          line-height: 1.9;
          white-space: pre-wrap;
        }
        .analysis-loading {
          display: flex;
          gap: 4px;
          align-items: center;
          color: #4b5563;
          font-size: 12px;
        }
        .dot-anim span {
          display: inline-block;
          animation: blink 1.2s infinite;
          animation-fill-mode: both;
        }
        .dot-anim span:nth-child(2) { animation-delay: 0.2s; }
        .dot-anim span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }

        /* ── Chat ── */
        .chat-log {
          height: 220px;
          overflow-y: auto;
          margin-bottom: 12px;
          padding-right: 4px;
          scrollbar-width: thin;
          scrollbar-color: #1e2a38 transparent;
        }
        .chat-log::-webkit-scrollbar { width: 4px; }
        .chat-log::-webkit-scrollbar-thumb { background: #1e2a38; border-radius: 2px; }
        .chat-msg {
          margin-bottom: 10px;
          font-size: 12px;
          line-height: 1.6;
        }
        .chat-msg.user .msg-label { color: #60a5fa; }
        .chat-msg.ai   .msg-label { color: #34d399; }
        .msg-label {
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          margin-bottom: 3px;
        }
        .msg-text { color: #9ca3af; }
        .chat-empty { color: #2d3748; font-size: 12px; }
        .chat-input-row {
          display: flex;
          gap: 8px;
        }
        .chat-input {
          flex: 1;
          background: #080b0f;
          border: 1px solid #1e2a38;
          border-radius: 6px;
          padding: 8px 12px;
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          color: #c9d1d9;
          outline: none;
          transition: border-color 0.2s;
        }
        .chat-input::placeholder { color: #374151; }
        .chat-input:focus { border-color: #2dd4bf44; }
        .chat-send {
          background: #2dd4bf18;
          border: 1px solid #2dd4bf44;
          color: #2dd4bf;
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          font-weight: 700;
          padding: 8px 14px;
          border-radius: 6px;
          cursor: pointer;
          letter-spacing: 0.06em;
          transition: background 0.2s, border-color 0.2s;
        }
        .chat-send:hover { background: #2dd4bf28; border-color: #2dd4bf88; }
        .chat-send:disabled { opacity: 0.4; cursor: not-allowed; }

        /* ── Scrollbar global ── */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1e2a38; border-radius: 2px; }
      `}</style>

      <div className="dashboard">
        {/* Header */}
        <header className="header">
          <div>
            <h1 className="header-title">AI Cloud Ops</h1>
            <p className="header-sub">Infrastructure Intelligence Dashboard</p>
          </div>
          <div className="header-right">
            <div
              className="health-pill"
              style={{
                color: healthColor,
                borderColor: `${healthColor}44`,
                background: `${healthColor}12`,
              }}
            >
              <span
                className="health-dot"
                style={{ background: healthColor }}
              />
              {overallHealth}
            </div>
            <span className="tick-counter">POLL #{tick} · every 3s</span>
          </div>
        </header>

        {/* Grid */}
        <div className="main-grid">
          {/* Metric cards */}
          <StatCard label="CPU Usage" value={metrics?.cpu ?? null} />
          <StatCard label="Memory Usage" value={metrics?.memory ?? null} />
          <StatCard label="Disk Usage" value={metrics?.disk ?? null} />

          {/* Area chart */}
          <div className="panel span-2">
            <p className="panel-title">Metric History</p>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart
                data={history}
                margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="gcpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gmem" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#34d399" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gdisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#facc15" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#facc15" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" />
                <XAxis
                  dataKey="t"
                  tick={{
                    fontSize: 9,
                    fill: "#374151",
                    fontFamily: "JetBrains Mono",
                  }}
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{
                    fontSize: 9,
                    fill: "#374151",
                    fontFamily: "JetBrains Mono",
                  }}
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stroke="#60a5fa"
                  strokeWidth={1.5}
                  fill="url(#gcpu)"
                  dot={false}
                  name="cpu"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stroke="#34d399"
                  strokeWidth={1.5}
                  fill="url(#gmem)"
                  dot={false}
                  name="memory"
                />
                <Area
                  type="monotone"
                  dataKey="disk"
                  stroke="#facc15"
                  strokeWidth={1.5}
                  fill="url(#gdisk)"
                  dot={false}
                  name="disk"
                />
              </AreaChart>
            </ResponsiveContainer>
            {/* Legend */}
            <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
              {[
                ["#60a5fa", "CPU"],
                ["#34d399", "Memory"],
                ["#facc15", "Disk"],
              ].map(([c, l]) => (
                <span
                  key={l}
                  style={{
                    fontSize: 10,
                    color: c,
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                  }}
                >
                  <span
                    style={{
                      width: 16,
                      height: 2,
                      background: c,
                      display: "inline-block",
                      borderRadius: 1,
                    }}
                  />
                  {l}
                </span>
              ))}
            </div>
          </div>

          {/* Alerts */}
          <div className="panel span-1">
            <p className="panel-title">Active Alerts</p>
            {!metrics ? (
              <p style={{ color: "#374151", fontSize: 12 }}>
                Waiting for data…
              </p>
            ) : alerts.length === 0 ? (
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
                const c =
                  a.severity === "high"
                    ? "#f87171"
                    : a.severity === "medium"
                      ? "#facc15"
                      : "#34d399";
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

          {/* AI Analysis */}
          <div className="panel span-2">
            <p className="panel-title">AI Incident Analysis</p>
            {analysisLoading ? (
              <div className="analysis-loading">
                <span>Generating</span>
                <span className="dot-anim">
                  <span>.</span>
                  <span>.</span>
                  <span>.</span>
                </span>
              </div>
            ) : (
              <div className="analysis-text">
                {analysis || "No analysis yet."}
              </div>
            )}
          </div>

          {/* SRE Chat */}
          <div className="panel span-1">
            <p className="panel-title">SRE Assistant</p>
            <div className="chat-log">
              {chatMessages.length === 0 ? (
                <p className="chat-empty">Ask about your infrastructure…</p>
              ) : (
                chatMessages.map((m, i) => (
                  <div key={i} className={`chat-msg ${m.role}`}>
                    <div className="msg-label">
                      {m.role === "user" ? "YOU" : "SRE-AI"}
                    </div>
                    <div className="msg-text">{m.text}</div>
                  </div>
                ))
              )}
              {chatLoading && (
                <div className="chat-msg ai">
                  <div className="msg-label">SRE-AI</div>
                  <div className="analysis-loading" style={{ marginTop: 4 }}>
                    <span className="dot-anim">
                      <span>.</span>
                      <span>.</span>
                      <span>.</span>
                    </span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div className="chat-input-row">
              <input
                className="chat-input"
                placeholder="e.g. why is CPU spiking?"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendChat()}
              />
              <button
                className="chat-send"
                onClick={sendChat}
                disabled={chatLoading}
              >
                SEND
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
