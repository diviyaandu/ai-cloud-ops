"use client";

import { useState } from "react";
import { fetchAnalysis } from "../../services/api";

type Props = { onGroqCall: (total: number) => void };

export default function AnalysisPanel({ onGroqCall }: Props) {
  const [analysis, setAnalysis] = useState("");
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const data = await fetchAnalysis();
      setAnalysis(data.analysis);
      onGroqCall(data.groq_calls_total);
    } catch {
      setAnalysis("Failed to reach backend.");
    }
    setLoading(false);
  };

  return (
    <div className="panel span-2">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 16,
        }}
      >
        <p className="panel-title" style={{ margin: 0 }}>
          AI Incident Analysis
        </p>
        <button
          className="chat-send"
          onClick={run}
          disabled={loading}
          style={{ fontSize: 10, padding: "5px 12px" }}
        >
          {loading ? (
            <span className="dot-anim">
              <span>.</span>
              <span>.</span>
              <span>.</span>
            </span>
          ) : (
            "▶ ANALYZE"
          )}
        </button>
      </div>
      {loading ? (
        <div className="analysis-loading">
          <span>Calling Groq</span>
          <span className="dot-anim">
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </span>
        </div>
      ) : (
        <div className="analysis-text">
          {analysis ||
            "Click ▶ ANALYZE to run AI analysis on current metrics. Each click = 1 Groq call."}
        </div>
      )}
    </div>
  );
}
