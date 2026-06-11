"use client";

import AlertsPanel from "@/components/dashboard/AlertsPanel";
import type { CloudSummary } from "@/hooks/useCloudResources";

interface AlertsViewProps {
  summary: CloudSummary | null;
}

export default function AlertsView({ summary }: AlertsViewProps) {
  return (
    <div className="view">
      <div className="page-head">
        <div>
          <div className="page-title">Active Alerts</div>
          <div className="page-title-sub">
            Prometheus alertmanager · real-time
          </div>
        </div>
      </div>
      <AlertsPanel
        rawAlerts={(summary?.health.resources ?? []).map(
          (r: any) =>
            `${r.name ?? r.id ?? "Resource"} — ${r.health_state ?? "Unhealthy"}`,
        )}
      />
    </div>
  );
}
