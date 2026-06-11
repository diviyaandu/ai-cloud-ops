"use client";

import ActionsPanel from "@/components/dashboard/ActionsPanel";

export default function ActionsView() {
  return (
    <div className="view">
      <div className="page-head">
        <div>
          <div className="page-title">Pending Actions</div>
          <div className="page-title-sub">
            Approve or reject agent-proposed write operations
          </div>
        </div>
      </div>
      <ActionsPanel />
    </div>
  );
}
