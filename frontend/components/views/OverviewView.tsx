"use client";

import { useState, useEffect, useRef } from "react";
import CloudIntelligence from "@/components/dashboard/CloudIntelligence";
import AlertsPanel from "@/components/dashboard/AlertsPanel";
import InsightCards from "@/components/dashboard/InsightCards";
import ResourceCard from "@/components/layout/ResourceCard";
import StatusPill from "@/components/layout/StatusPill";
import TagFilterBar from "@/components/layout/TagFilterBar";
import {
  useTagValues,
  useFilteredResources,
  type CloudSummary,
} from "@/hooks/useCloudResources";
import type { CloudResources } from "@/types/cloud";
import { TYPE_ACCENTS, DEFAULT_ACCENT, labelFor } from "@/lib/resourceUtils";

interface OverviewViewProps {
  data: CloudResources | null;
  loading: boolean;
  error: string | null;
  summary: CloudSummary | null;
  summaryLoading: boolean;
}

export default function OverviewView({
  data,
  loading,
  error,
  summary,
  summaryLoading,
}: OverviewViewProps) {
  const isLive = data?.mode === "live";
  const [tagFilters, setTagFilters] = useState<Record<string, string>>({});
  const tagValues = useTagValues();
  const { data: filteredData } = useFilteredResources(tagFilters);

  const allTypes: string[] = (data?.raw_by_type ?? []).map((r) => r.type);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const initializedTypes = useRef(false);

  useEffect(() => {
    if (data?.raw_by_type && !initializedTypes.current) {
      initializedTypes.current = true;
      setSelected(new Set(allTypes));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const filteredTypes = (data?.raw_by_type ?? []).filter((r) => {
    const matchesSearch = r.type.toLowerCase().includes(search.toLowerCase());
    const matchesSelected = selected.size === 0 || selected.has(r.type);
    return matchesSearch && matchesSelected;
  });

  const allSelected = selected.size === allTypes.length;

  return (
    <div className="view">
      <div className="page-head">
        <div>
          <div className="page-title">Resource Overview</div>
          <div className="page-title-sub">Azure subscription · live inventory</div>
        </div>
        <StatusPill live={isLive} loading={loading} />
      </div>

      <p className="section-lbl">Live Insights</p>
      <InsightCards data={summary} loading={summaryLoading} />

      <p className="section-lbl">Resource Inventory</p>

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
        {filteredTypes.map((r, i) => (
          <ResourceCard
            key={r.type}
            index={i + 1}
            label={labelFor(r.type)}
            sublabel={r.type.split("/")[0].replace("microsoft.", "")}
            value={r.count}
            accent={TYPE_ACCENTS[r.type.toLowerCase()] ?? DEFAULT_ACCENT}
            icon="◇"
            loading={loading}
            region={r.regions?.join(" · ")}
          />
        ))}
      </div>

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

      <p className="section-lbl">Monitoring</p>
      <div className="content-grid">
        <div className="left-col">
          <div className="panel">
            <CloudIntelligence data={data} loading={loading} error={error} />
          </div>
        </div>
        <div className="right-col">
          <AlertsPanel
            rawAlerts={(summary?.health.resources ?? []).map(
              (r: any) =>
                `${r.name ?? r.id ?? "Resource"} — ${r.health_state ?? "Unhealthy"}`,
            )}
          />
        </div>
      </div>
    </div>
  );
}
