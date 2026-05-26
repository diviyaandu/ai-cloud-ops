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
