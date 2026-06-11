"use client";

import { useEffect, useState } from "react";

const BASE = "http://127.0.0.1:8000";

export type FlatResource = {
  id: string;
  name: string;
  type: string;
  resource_group: string;
  location: string;
  state: string;
};

type ResourceOperationsData = {
  total: number;
  mode: "live" | "mock";
  resources: FlatResource[];
};

export function useResourceOperations() {
  const [data, setData] = useState<ResourceOperationsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refresh = () => setTick((t) => t + 1);

  useEffect(() => {
    setLoading(true);
    fetch(`${BASE}/resource-operations`)
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
  }, [tick]);

  return { data, loading, error, refresh };
}

export function useQueueAction() {
  const queue = async (
    action_type: string,
    params: Record<string, unknown>,
    proposed_by = "resource-ops-ui",
  ): Promise<{ ok: boolean; id?: string; error?: string }> => {
    try {
      const res = await fetch(`${BASE}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_type, params, proposed_by }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return { ok: true, id: data.id };
    } catch (e: any) {
      return { ok: false, error: e.message };
    }
  };
  return queue;
}
