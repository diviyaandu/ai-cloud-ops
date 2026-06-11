"use client";

import { useEffect, useState } from "react";
import type { CloudResources } from "@/types/cloud";

const BASE = "http://127.0.0.1:8000";
const POLL_INTERVAL_MS = 30_000;
const SUMMARY_POLL_MS = 60_000; // summary is heavier — poll every 60s

export function useCloudResources() {
  const [data, setData] = useState<CloudResources | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [tick, setTick] = useState(0);
  const refresh = () => setTick((t) => t + 1);

  useEffect(() => {
    const poll = () => {
      fetch(`${BASE}/cloud-resources`)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((d) => {
          setData(d);
          setError(null);
          setLoading(false);
        })
        .catch((e) => {
          setError(e.message);
          setLoading(false);
        });
    };
    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [tick]);

  return { data, loading, error, refresh };
}

export type CloudSummary = {
  spend: {
    spent_usd: number | null;
    budget_usd: number | null;
    forecast_eom_usd: number | null;
    percent_used: number | null;
    status: string;
  };
  health: {
    unhealthy_total: number;
    critical: number;
    warning: number;
    status: string;
    resources: any[];
  };
  security: {
    untagged_total: number;
    recent_changes: number;
    status: string;
  };
  logs: {
    errors_24h: number;
    failed_ops_24h: number;
    status: string;
  };
  advisor: {
    total: number;
    potential_savings: number;
    status: string;
  };
};

export function useCloudSummary() {
  const [data, setData] = useState<CloudSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [tick, setTick] = useState(0);
  const refresh = () => setTick((t) => t + 1);

  useEffect(() => {
    const poll = () => {
      fetch(`${BASE}/cloud-summary`)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((d) => {
          setData(d);
          setError(null);
          setLoading(false);
        })
        .catch((e) => {
          setError(e.message);
          setLoading(false);
        });
    };
    poll();
    const id = setInterval(poll, SUMMARY_POLL_MS);
    return () => clearInterval(id);
  }, [tick]);

  return { data, loading, error, refresh };
}

export function useTagValues() {
  const [tags, setTags] = useState<Record<string, string[]>>({});
  useEffect(() => {
    fetch(`${BASE}/cloud-resources/tags`)
      .then((r) => r.json())
      .then(setTags)
      .catch(() => {});
  }, []);
  return tags;
}

export function useFilteredResources(filters: Record<string, string>) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const activeFilters = Object.entries(filters).filter(([, v]) => v);

  useEffect(() => {
    if (activeFilters.length === 0) {
      setData(null);
      return;
    }
    setLoading(true);
    const params = new URLSearchParams(
      activeFilters.map(([k, v]) => [k.toLowerCase(), v]),
    );
    fetch(`${BASE}/cloud-resources/filter?${params}`)
      .then((r) => r.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [JSON.stringify(filters)]);

  return { data, loading };
}
