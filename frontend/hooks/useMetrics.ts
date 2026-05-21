"use client";

import { useEffect, useState } from "react";
import { fetchMetrics } from "@/services/api";
import type { Metrics, MetricPoint } from "@/types/metrics";

const MAX_HISTORY = 20;
const POLL_INTERVAL_MS = 3000;

function timeLabel(): string {
  const now = new Date();
  return [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map((n) => n.toString().padStart(2, "0"))
    .join(":");
}

export function useMetrics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [history, setHistory] = useState<MetricPoint[]>([]);
  const [tick, setTick] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const poll = () => {
      fetchMetrics()
        .then((data) => {
          setMetrics(data);
          setError(null);
          setHistory((prev) => [
            ...prev.slice(-(MAX_HISTORY - 1)),
            {
              t: timeLabel(),
              cpu: data.cpu,
              memory: data.memory,
              disk: data.disk,
            },
          ]);
          setTick((n) => n + 1);
        })
        .catch((e) => setError(e.message));
    };

    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, []);

  return { metrics, history, tick, error };
}
