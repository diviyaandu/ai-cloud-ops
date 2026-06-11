"use client";

import type { NavItem } from "@/types/nav";

interface NavBtnProps {
  id: NavItem;
  label: string;
  icon: string;
  active: boolean;
  badge?: number;
  onClick: () => void;
}

export default function NavBtn({
  id,
  label,
  icon,
  active,
  badge,
  onClick,
}: NavBtnProps) {
  return (
    <button
      className={`nav-btn ${active ? "nav-btn--active" : ""}`}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
    >
      <span className="nav-icon" aria-hidden>
        {icon}
      </span>
      <span className="nav-label">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="nav-badge">{badge}</span>
      )}
    </button>
  );
}
