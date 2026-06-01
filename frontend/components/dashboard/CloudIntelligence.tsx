"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from "recharts";
import type { CloudResources } from "@/types/cloud";

type Props = {
  data: CloudResources | null;
  loading: boolean;
  error: string | null;
};

const RESOURCE_DEFS = [
  {
    key: "virtual_machines",
    label: "Virtual Machines",
    short: "VM",
    color: "#60a5fa",
  },
  {
    key: "aks_clusters",
    label: "AKS Clusters",
    short: "AKS",
    color: "#34d399",
  },
  {
    key: "app_services",
    label: "App Services",
    short: "APP",
    color: "#fb923c",
  },
  {
    key: "storage_accounts",
    label: "Storage Accounts",
    short: "STG",
    color: "#facc15",
  },
  {
    key: "cognitive_services",
    label: "Cognitive Svcs",
    short: "COG",
    color: "#a78bfa",
  },
] as const;

type ResourceKey = (typeof RESOURCE_DEFS)[number]["key"];

function toBarData(data: CloudResources | null, active: Set<ResourceKey>) {
  return RESOURCE_DEFS.filter((d) => active.has(d.key)).map((d) => ({
    ...d,
    value: data
      ? (((data as Record<string, unknown>)[d.key] as number) ?? 0)
      : 0,
  }));
}

function toRadialData(data: CloudResources | null, active: Set<ResourceKey>) {
  const all = RESOURCE_DEFS.filter((d) => active.has(d.key)).map((d) => ({
    ...d,
    fill: d.color,
    value: data
      ? (((data as Record<string, unknown>)[d.key] as number) ?? 0)
      : 0,
  }));
  const total = all.reduce((s, d) => s + d.value, 0) || 1;
  return all.map((d) => ({ ...d, pct: Math.round((d.value / total) * 100) }));
}

function BarTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div
      style={{
        background: "#0f1520",
        border: "1px solid #1e2a38",
        borderRadius: 7,
        padding: "8px 12px",
        fontFamily: "JetBrains Mono, monospace",
      }}
    >
      <p
        style={{
          fontSize: 9,
          color: "#3d5066",
          letterSpacing: "0.1em",
          marginBottom: 4,
        }}
      >
        {d.payload.label}
      </p>
      <p
        style={{
          fontSize: 18,
          fontFamily: "Syne, sans-serif",
          fontWeight: 800,
          color: d.fill,
        }}
      >
        {d.value}
      </p>
    </div>
  );
}

function Skeleton({ w = "100%", h = 16 }: { w?: string | number; h?: number }) {
  return (
    <span
      style={{
        display: "block",
        width: w,
        height: h,
        borderRadius: 4,
        background:
          "linear-gradient(90deg,#141c26 25%,#1e2a38 50%,#141c26 75%)",
        backgroundSize: "200% 100%",
        animation: "shimmer 1.6s infinite",
      }}
    />
  );
}

export default function CloudIntelligence({ data, loading, error }: Props) {
  const [active, setActive] = useState<Set<ResourceKey>>(
    new Set(RESOURCE_DEFS.map((d) => d.key)),
  );

  function toggle(key: ResourceKey) {
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size === 1) return prev; // keep at least one
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  const barData = toBarData(data, active);
  const radData = toRadialData(data, active);
  const hasData = !loading && !error && data;
  const filteredTotal = barData.reduce((s, d) => s + d.value, 0);

  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 16px",
          borderBottom: "1px solid #141c26",
          background: "rgba(255,255,255,0.01)",
        }}
      >
        <span
          style={{
            fontSize: 9,
            fontWeight: 700,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: "#3d5066",
            fontFamily: "JetBrains Mono, monospace",
          }}
        >
          Cloud Intelligence
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {hasData && (
            <span
              style={{ fontSize: 8, color: "#3d5066", letterSpacing: "0.06em" }}
            >
              {data.mode === "live" ? "LIVE · AZURE" : "MOCK"}
            </span>
          )}
          <span
            style={{
              fontSize: 9,
              fontWeight: 700,
              letterSpacing: "0.1em",
              padding: "3px 9px",
              borderRadius: 100,
              border: `1px solid ${error ? "rgba(248,113,113,0.2)" : "rgba(45,212,191,0.2)"}`,
              background: error
                ? "rgba(248,113,113,0.05)"
                : "rgba(45,212,191,0.05)",
              color: error ? "#f87171" : "#2dd4bf",
              fontFamily: "JetBrains Mono, monospace",
            }}
          >
            {loading ? "…" : error ? "ERR" : `${data?.total ?? 0} total`}
          </span>
        </div>
      </div>

      {/* ── Filter toggles ── */}
      <div
        style={{
          display: "flex",
          gap: 6,
          padding: "10px 16px",
          borderBottom: "1px solid #141c26",
          flexWrap: "wrap",
        }}
      >
        {RESOURCE_DEFS.map((d) => {
          const on = active.has(d.key);
          return (
            <button
              key={d.key}
              onClick={() => toggle(d.key)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                padding: "3px 9px",
                borderRadius: 4,
                cursor: "pointer",
                fontFamily: "JetBrains Mono, monospace",
                fontSize: 8,
                fontWeight: 700,
                letterSpacing: "0.08em",
                border: `1px solid ${on ? d.color + "44" : "#141c26"}`,
                background: on ? d.color + "12" : "transparent",
                color: on ? d.color : "#2d3d52",
                transition: "all 0.15s",
              }}
            >
              <span
                style={{
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  background: on ? d.color : "#2d3d52",
                  display: "inline-block",
                  flexShrink: 0,
                  transition: "background 0.15s",
                }}
              />
              {d.short}
            </button>
          );
        })}
        {active.size < RESOURCE_DEFS.length && (
          <button
            onClick={() => setActive(new Set(RESOURCE_DEFS.map((d) => d.key)))}
            style={{
              padding: "3px 9px",
              borderRadius: 4,
              cursor: "pointer",
              fontFamily: "JetBrains Mono, monospace",
              fontSize: 8,
              fontWeight: 700,
              letterSpacing: "0.08em",
              border: "1px solid #1e2a38",
              background: "transparent",
              color: "#3d5066",
              marginLeft: "auto",
              transition: "color 0.15s",
            }}
          >
            reset
          </button>
        )}
      </div>

      {/* Body */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 160px",
          gap: 0,
          padding: "16px 16px 12px",
          alignItems: "center",
        }}
      >
        {/* Bar chart */}
        <div>
          {loading ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 8,
                paddingRight: 16,
              }}
            >
              {RESOURCE_DEFS.map((d) => (
                <div
                  key={d.key}
                  style={{ display: "flex", gap: 8, alignItems: "center" }}
                >
                  <Skeleton w={48} h={10} />
                  <Skeleton w="60%" h={22} />
                </div>
              ))}
            </div>
          ) : error ? (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: 160,
                flexDirection: "column",
                gap: 6,
                color: "#f87171",
                fontSize: 11,
                fontFamily: "JetBrains Mono, monospace",
              }}
            >
              <span style={{ fontSize: 18, opacity: 0.4 }}>⚠</span>
              <span>{error}</span>
              <span style={{ fontSize: 9, color: "#3d5066" }}>
                Check backend · port 8000
              </span>
            </div>
          ) : (
            <ResponsiveContainer
              width="100%"
              height={Math.max(active.size * 34, 80)}
            >
              <BarChart
                data={barData}
                layout="vertical"
                margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
                barCategoryGap="28%"
              >
                <XAxis
                  type="number"
                  tick={{
                    fontSize: 8,
                    fill: "#2d3d52",
                    fontFamily: "JetBrains Mono, monospace",
                  }}
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                  tickFormatter={(v) => (v === 0 ? "" : String(v))}
                />
                <YAxis
                  type="category"
                  dataKey="short"
                  tick={{
                    fontSize: 8,
                    fill: "#2d3d52",
                    fontFamily: "JetBrains Mono, monospace",
                  }}
                  tickLine={false}
                  axisLine={false}
                  width={32}
                />
                <Tooltip
                  content={<BarTooltip />}
                  cursor={{ fill: "rgba(255,255,255,0.02)" }}
                />
                <Bar dataKey="value" radius={[0, 3, 3, 0]} maxBarSize={14}>
                  {barData.map((d) => (
                    <Cell
                      key={d.key}
                      fill={d.color}
                      fillOpacity={d.value === 0 ? 0.18 : 0.8}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Radial */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 8,
          }}
        >
          {loading ? (
            <Skeleton w={120} h={120} />
          ) : (
            !error && (
              <>
                <div style={{ position: "relative", width: 120, height: 120 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart
                      data={radData}
                      innerRadius={22}
                      outerRadius={56}
                      startAngle={90}
                      endAngle={-270}
                      barSize={7}
                    >
                      <PolarAngleAxis
                        type="number"
                        domain={[0, 100]}
                        tick={false}
                      />
                      <RadialBar
                        dataKey="pct"
                        background={{ fill: "#141c26" }}
                        cornerRadius={4}
                      />
                    </RadialBarChart>
                  </ResponsiveContainer>
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      pointerEvents: "none",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "Syne, sans-serif",
                        fontSize: 20,
                        fontWeight: 800,
                        color: "#d4dde8",
                        lineHeight: 1,
                      }}
                    >
                      {filteredTotal}
                    </span>
                    <span
                      style={{
                        fontSize: 7,
                        color: "#2d3d52",
                        letterSpacing: "0.1em",
                        marginTop: 2,
                      }}
                    >
                      {active.size < RESOURCE_DEFS.length
                        ? "FILTERED"
                        : "TOTAL"}
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                    width: "100%",
                  }}
                >
                  {radData.map((d) => (
                    <div
                      key={d.key}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: 5,
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 5,
                        }}
                      >
                        <span
                          style={{
                            width: 6,
                            height: 6,
                            borderRadius: "50%",
                            background: d.color,
                            display: "inline-block",
                            opacity: d.value === 0 ? 0.2 : 1,
                            flexShrink: 0,
                          }}
                        />
                        <span
                          style={{
                            fontSize: 8,
                            color: "#3d5066",
                            letterSpacing: "0.06em",
                          }}
                        >
                          {d.short}
                        </span>
                      </div>
                      <span
                        style={{
                          fontSize: 9,
                          fontWeight: 700,
                          color: d.value === 0 ? "#1e2a38" : d.color,
                          fontFamily: "Syne, sans-serif",
                        }}
                      >
                        {d.value}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )
          )}
        </div>
      </div>

      {/* Raw type strip */}
      {hasData && data.raw_by_type?.length > 0 && (
        <div
          style={{
            borderTop: "1px solid #141c26",
            padding: "8px 16px",
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
          }}
        >
          {data.raw_by_type.map(
            (r: { type: string; count: number; regions: string[] }) => (
              <span
                key={r.type}
                style={{
                  fontSize: 8,
                  color: "#2d3d52",
                  background: "#0f1520",
                  border: "1px solid #141c26",
                  borderRadius: 4,
                  padding: "2px 7px",
                  letterSpacing: "0.06em",
                  whiteSpace: "nowrap",
                  fontFamily: "JetBrains Mono, monospace",
                }}
              >
                {r.type.split("/").pop()} ×{r.count}
              </span>
            ),
          )}
        </div>
      )}
    </div>
  );
}
