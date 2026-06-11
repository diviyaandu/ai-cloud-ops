"use client";

import AnalysisPanel from "@/components/dashboard/AnalysisPanel";

export default function AnalysisView() {
  return (
    <div className="view">
      <div className="page-head">
        <div>
          <div className="page-title">AI Incident Analysis</div>
          <div className="page-title-sub">Groq llama-3.1-8b · on-demand</div>
        </div>
      </div>
      <div className="analysis-wrap">
        <AnalysisPanel />
      </div>
    </div>
  );
}
