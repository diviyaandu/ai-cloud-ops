"use client";

import type { CSSProperties } from "react";

interface ResourceCardProps {
  label: string;
  sublabel: string;
  value: number | null;
  accent: string;
  icon: string;
  loading: boolean;
  region?: string;
  index: number;
}

export default function ResourceCard({
  label,
  sublabel,
  value,
  accent,
  icon,
  loading,
  region,
  index,
}: ResourceCardProps) {
  const isZero = value === 0;

  return (
    <div
      className="rc"
      style={
        {
          "--accent": accent,
          "--delay": `${index * 60}ms`,
        } as CSSProperties
      }
    >
      <span className="rc-corner" />
      <div className="rc-header">
        <span className="rc-icon" aria-hidden>
          {icon}
        </span>
        {region && <span className="rc-region">{region}</span>}
      </div>
      <div className="rc-value-wrap">
        {loading ? (
          <span className="rc-skeleton" />
        ) : value === null ? (
          <span className="rc-null">—</span>
        ) : (
          <span
            className="rc-value"
            style={{ color: isZero ? "var(--muted)" : "var(--fg)" }}
          >
            {value}
          </span>
        )}
      </div>
      <div className="rc-footer">
        <span className="rc-label">{label}</span>
        <span className="rc-sub">{sublabel}</span>
      </div>
      <div className="rc-bar">
        <span
          className="rc-bar-fill"
          style={{
            width: loading || value === null ? "0%" : isZero ? "4%" : "38%",
          }}
        />
      </div>
    </div>
  );
}
