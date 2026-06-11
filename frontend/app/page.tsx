"use client";

import "@/styles/global.css";
import "@/styles/layout.css";
import "@/styles/cards.css";
import "@/styles/dashboard.css";
import "@/styles/filters.css";
import "@/styles/chat.css";
import "@/styles/alerts.css";
import "@/styles/analysis.css";
import "@/styles/ic.css";

import { useState } from "react";
import { useCloudResources, useCloudSummary } from "@/hooks/useCloudResources";
import type { NavItem } from "@/types/nav";

import Topbar from "@/components/layout/Topbar";
import Sidebar from "@/components/layout/Sidebar";
import OverviewView from "@/components/views/OverviewView";
import AgentView from "@/components/views/AgentView";
import AnalysisView from "@/components/views/AnalysisView";
import AlertsView from "@/components/views/AlertsView";
import ActionsView from "@/components/views/ActionsView";
import ResourceOperationsView from "@/components/views/ResourceOperationsView";

export default function Home() {
  const {
    data,
    loading,
    error,
    refresh: refreshResources,
  } = useCloudResources();
  const {
    data: summary,
    loading: summaryLoading,
    refresh: refreshSummary,
  } = useCloudSummary();
  const [activeNav, setActiveNav] = useState<NavItem>("overview");

  const handleRefresh = () => {
    refreshResources();
    refreshSummary();
  };

  return (
    <div className="app">
      <Topbar data={data} loading={loading} onRefresh={handleRefresh} />
      <Sidebar
        activeNav={activeNav}
        onNav={setActiveNav}
        data={data}
        loading={loading}
      />

      <main className="main">
        {activeNav === "overview" && (
          <OverviewView
            data={data}
            loading={loading}
            error={error}
            summary={summary}
            summaryLoading={summaryLoading}
          />
        )}
        {activeNav === "agent" && <AgentView />}
        {activeNav === "analysis" && <AnalysisView />}
        {activeNav === "alerts" && <AlertsView summary={summary} />}
        {activeNav === "actions" && <ActionsView />}
        {activeNav === "operations" && <ResourceOperationsView />}
      </main>
    </div>
  );
}
