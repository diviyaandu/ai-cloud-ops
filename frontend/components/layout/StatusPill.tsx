"use client";

interface StatusPillProps {
  live: boolean;
  loading: boolean;
}

export default function StatusPill({ live, loading }: StatusPillProps) {
  if (loading)
    return (
      <span className="pill pill--connecting">
        <span className="pill-dot" />
        CONNECTING
      </span>
    );

  return (
    <span className={`pill ${live ? "pill--live" : "pill--offline"}`}>
      <span className={`pill-dot ${live ? "pill-dot--pulse" : ""}`} />
      {live ? "LIVE · AZURE" : "OFFLINE"}
    </span>
  );
}
