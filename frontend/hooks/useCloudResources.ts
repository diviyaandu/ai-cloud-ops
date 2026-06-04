"use client";

import { useEffect, useState } from "react";
import type { CloudResources } from "@/types/cloud";

const BASE = "http://127.0.0.1:8000";
const POLL_INTERVAL_MS = 30_000; // cloud inventory — poll every 30s not 3s

export function useCloudResources() {
  const [data, setData] = useState<CloudResources | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
  }, []);

  return { data, loading, error };
}

// Add after the existing hook:
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
