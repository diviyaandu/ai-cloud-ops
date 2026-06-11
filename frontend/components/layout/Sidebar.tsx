"use client";

import NavBtn from "@/components/layout/NavBtn";
import type { NavItem } from "@/types/nav";
import type { CloudResources } from "@/types/cloud";

interface SidebarProps {
  activeNav: NavItem;
  onNav: (item: NavItem) => void;
  data: CloudResources | null;
  loading: boolean;
}

export default function Sidebar({
  activeNav,
  onNav,
  data,
  loading,
}: SidebarProps) {
  return (
    <nav className="sidebar">
      <span className="sidebar-section">Views</span>
      <NavBtn
        id="overview"
        label="Overview"
        icon="◈"
        active={activeNav === "overview"}
        onClick={() => onNav("overview")}
      />
      <NavBtn
        id="agent"
        label="AI Copilot"
        icon="⬡"
        active={activeNav === "agent"}
        onClick={() => onNav("agent")}
      />
      <NavBtn
        id="analysis"
        label="Analysis"
        icon="◇"
        active={activeNav === "analysis"}
        onClick={() => onNav("analysis")}
      />
      <NavBtn
        id="alerts"
        label="Alerts"
        icon="▲"
        active={activeNav === "alerts"}
        badge={0}
        onClick={() => onNav("alerts")}
      />
      <NavBtn
        id="actions"
        label="Actions"
        icon="✦"
        active={activeNav === "actions"}
        onClick={() => onNav("actions")}
      />
      <NavBtn
        id="operations"
        label="Resource Ops"
        icon="⚡"
        active={activeNav === "operations"}
        onClick={() => onNav("operations")}
      />

      <span className="sidebar-section">Subscription</span>
      <div className="sidebar-footer">
        <div>
          <b>Sub</b> d91323a4
        </div>
        <div>
          <b>RG</b> rg-finops-prod
        </div>
        <div>
          <b>Region</b> eastus
        </div>
        <div>
          <b>Model</b> llama-3.1-8b
        </div>
        <div>
          <b>Mode</b> {loading ? "…" : data?.mode === "live" ? "live" : "mock"}
        </div>
      </div>
    </nav>
  );
}
