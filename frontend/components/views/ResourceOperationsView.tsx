"use client";

import { useState, useMemo } from "react";
import {
  useResourceOperations,
  useQueueAction,
  type FlatResource,
} from "@/hooks/useResourceOperations";

// ── Helpers ──────────────────────────────────────────────────────────────────

function shortType(type: string) {
  return type.split("/").pop() ?? type;
}

type ActionSupport = "container_app" | "vm" | "none";

function actionSupport(type: string): ActionSupport {
  const t = type.toLowerCase();
  if (t === "microsoft.app/containerapps") return "container_app";
  if (t === "microsoft.compute/virtualmachines") return "vm";
  return "none";
}

type StatusVariant = "running" | "stopped" | "warning" | "unknown";

function stateVariant(state: string): StatusVariant {
  const s = state.toLowerCase();
  if (["succeeded", "running", "ready"].includes(s)) return "running";
  if (["stopped", "deallocated", "scaled-to-zero"].includes(s))
    return "stopped";
  if (["failed", "degraded", "unhealthy"].includes(s)) return "warning";
  return "unknown";
}

const VARIANT_STYLES: Record<
  StatusVariant,
  { bg: string; color: string; dot: string }
> = {
  running: { bg: "#34d39915", color: "#34d399", dot: "#34d399" },
  stopped: { bg: "#f8717115", color: "#f87171", dot: "#f87171" },
  warning: { bg: "#fb923c15", color: "#fb923c", dot: "#fb923c" },
  unknown: { bg: "#9ca3af15", color: "#9ca3af", dot: "#9ca3af" },
};

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ state }: { state: string }) {
  const v = stateVariant(state);
  const s = VARIANT_STYLES[v];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        fontSize: 10,
        fontWeight: 600,
        padding: "2px 8px",
        borderRadius: 4,
        background: s.bg,
        color: s.color,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
      }}
    >
      <span
        style={{
          width: 5,
          height: 5,
          borderRadius: "50%",
          background: s.dot,
          flexShrink: 0,
        }}
      />
      {state || "Unknown"}
    </span>
  );
}

function ActionButtons({
  resource,
  onQueued,
}: {
  resource: FlatResource;
  onQueued: (msg: string) => void;
}) {
  const queue = useQueueAction();
  const support = actionSupport(resource.type);
  const [busy, setBusy] = useState(false);

  if (support === "none") {
    return <span style={{ fontSize: 10, color: "#4b5563" }}>—</span>;
  }

  const handle = async (verb: "start" | "stop") => {
    setBusy(true);
    const action_type =
      support === "container_app"
        ? verb === "stop"
          ? "stop_container_app"
          : "start_container_app"
        : verb === "stop"
          ? "stop_vm"
          : "start_vm";

    const params =
      support === "container_app"
        ? { resource_group: resource.resource_group, app_name: resource.name }
        : { resource_group: resource.resource_group, vm_name: resource.name };

    const result = await queue(action_type, params);
    setBusy(false);
    if (result.ok) {
      onQueued(
        `${verb === "stop" ? "Stop" : "Start"} queued for ${resource.name} — approve in Actions tab`,
      );
    } else {
      onQueued(`Failed to queue: ${result.error}`);
    }
  };

  return (
    <div style={{ display: "flex", gap: 5 }}>
      <button
        disabled={busy}
        onClick={() => handle("start")}
        style={{
          fontSize: 10,
          padding: "2px 9px",
          borderRadius: 4,
          background: "#34d39918",
          border: "1px solid #34d39955",
          color: busy ? "#4b5563" : "#34d399",
          cursor: busy ? "not-allowed" : "pointer",
        }}
      >
        Start
      </button>
      <button
        disabled={busy}
        onClick={() => handle("stop")}
        style={{
          fontSize: 10,
          padding: "2px 9px",
          borderRadius: 4,
          background: "#f8717118",
          border: "1px solid #f8717155",
          color: busy ? "#4b5563" : "#f87171",
          cursor: busy ? "not-allowed" : "pointer",
        }}
      >
        Stop
      </button>
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export default function ResourceOperationsView() {
  const { data, loading, error, refresh } = useResourceOperations();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [rgFilter, setRgFilter] = useState("");
  const [toast, setToast] = useState<string | null>(null);

  const resources = data?.resources ?? [];

  const allTypes = useMemo(
    () => [...new Set(resources.map((r) => r.type))].sort(),
    [resources],
  );
  const allRGs = useMemo(
    () => [...new Set(resources.map((r) => r.resource_group))].sort(),
    [resources],
  );

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return resources.filter((r) => {
      const matchSearch =
        !q ||
        r.name.toLowerCase().includes(q) ||
        r.type.toLowerCase().includes(q) ||
        r.resource_group.toLowerCase().includes(q);
      const matchType = !typeFilter || r.type === typeFilter;
      const matchRG = !rgFilter || r.resource_group === rgFilter;
      return matchSearch && matchType && matchRG;
    });
  }, [resources, search, typeFilter, rgFilter]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  };

  return (
    <div className="view">
      {/* Header */}
      <div className="page-head">
        <div>
          <div className="page-title">Resource Operations</div>
          <div className="page-title-sub">
            Azure subscription · start / stop · approval workflow
          </div>
        </div>
        <button
          onClick={refresh}
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
      </div>

      {/* Toolbar */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 14,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <input
          className="ri-search"
          placeholder="Search name, type, resource group…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: "1 1 220px", minWidth: 180 }}
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          style={{
            fontSize: 11,
            padding: "4px 10px",
            borderRadius: 4,
            background: "#0d1821",
            border: "1px solid #1e2d3d",
            color: typeFilter ? "#e5e7eb" : "#6b7280",
            cursor: "pointer",
          }}
        >
          <option value="">All Types</option>
          {allTypes.map((t) => (
            <option key={t} value={t}>
              {shortType(t)}
            </option>
          ))}
        </select>
        <select
          value={rgFilter}
          onChange={(e) => setRgFilter(e.target.value)}
          style={{
            fontSize: 11,
            padding: "4px 10px",
            borderRadius: 4,
            background: "#0d1821",
            border: "1px solid #1e2d3d",
            color: rgFilter ? "#e5e7eb" : "#6b7280",
            cursor: "pointer",
          }}
        >
          <option value="">All Resource Groups</option>
          {allRGs.map((rg) => (
            <option key={rg} value={rg}>
              {rg}
            </option>
          ))}
        </select>
        {(search || typeFilter || rgFilter) && (
          <button
            onClick={() => {
              setSearch("");
              setTypeFilter("");
              setRgFilter("");
            }}
            style={{
              fontSize: 10,
              padding: "3px 9px",
              borderRadius: 4,
              background: "transparent",
              border: "1px solid #1e2d3d",
              color: "#6b7280",
              cursor: "pointer",
            }}
          >
            Clear
          </button>
        )}
        <span style={{ fontSize: 10, color: "#4b5563", marginLeft: "auto" }}>
          {filtered.length} / {resources.length} resources
        </span>
      </div>

      {/* Error */}
      {error && (
        <div
          style={{
            fontSize: 11,
            color: "#f87171",
            marginBottom: 12,
            padding: "8px 12px",
            background: "#f8717110",
            borderRadius: 4,
            border: "1px solid #f8717130",
          }}
        >
          {error}
        </div>
      )}

      {/* Table */}
      <div className="panel" style={{ overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: 11,
            }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid #1e2d3d",
                  background: "#ffffff04",
                }}
              >
                {[
                  "Name",
                  "Type",
                  "Resource Group",
                  "Location",
                  "State",
                  "Actions",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "9px 14px",
                      textAlign: "left",
                      fontSize: 9,
                      fontWeight: 700,
                      letterSpacing: "0.12em",
                      textTransform: "uppercase",
                      color: "#4b5563",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(6)].map((_, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #0f1922" }}>
                    {[...Array(6)].map((_, j) => (
                      <td key={j} style={{ padding: "10px 14px" }}>
                        <div
                          style={{
                            height: 10,
                            borderRadius: 3,
                            background: "#ffffff08",
                            width: j === 0 ? "60%" : j === 5 ? "80px" : "40%",
                          }}
                        />
                      </td>
                    ))}
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    style={{
                      padding: "32px 14px",
                      textAlign: "center",
                      color: "#4b5563",
                      fontSize: 11,
                    }}
                  >
                    No resources match the current filters.
                  </td>
                </tr>
              ) : (
                filtered.map((r) => (
                  <tr
                    key={r.id}
                    style={{
                      borderBottom: "1px solid #0f1922",
                      transition: "background 0.1s",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.background = "#ffffff04")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.background = "transparent")
                    }
                  >
                    <td
                      style={{
                        padding: "9px 14px",
                        color: "#e5e7eb",
                        fontWeight: 500,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {r.name}
                    </td>
                    <td
                      style={{
                        padding: "9px 14px",
                        color: "#6b7280",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {shortType(r.type)}
                    </td>
                    <td
                      style={{
                        padding: "9px 14px",
                        color: "#6b7280",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {r.resource_group}
                    </td>
                    <td
                      style={{
                        padding: "9px 14px",
                        color: "#6b7280",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {r.location}
                    </td>
                    <td style={{ padding: "9px 14px" }}>
                      <StatusBadge state={r.state} />
                    </td>
                    <td style={{ padding: "9px 14px" }}>
                      <ActionButtons resource={r} onQueued={showToast} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            background: "#0d1821",
            border: "1px solid #1e2d3d",
            borderRadius: 6,
            padding: "10px 16px",
            fontSize: 11,
            color: "#e5e7eb",
            zIndex: 1000,
            maxWidth: 360,
            boxShadow: "0 4px 20px #00000060",
          }}
        >
          <span style={{ color: "#34d399", marginRight: 8 }}>✦</span>
          {toast}
        </div>
      )}
    </div>
  );
}
