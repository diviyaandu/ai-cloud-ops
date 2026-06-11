"use client";

import { useEffect, useState } from "react";

export function useGroqStats() {
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
