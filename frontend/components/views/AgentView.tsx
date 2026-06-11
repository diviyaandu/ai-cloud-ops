"use client";

import AgentPanel from "@/components/chat/AgentPanel";

export default function AgentView() {
  return (
    <div className="view">
      <div className="page-head">
        <div>
          <div className="page-title">AI Copilot</div>
          <div className="page-title-sub">
            Multi-agent · Router → Operational / Security / FinOps
          </div>
        </div>
      </div>
      <div className="agent-wrap">
        <AgentPanel />
      </div>
    </div>
  );
}
