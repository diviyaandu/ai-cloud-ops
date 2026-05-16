"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export default function Home() {
  const [metrics, setMetrics] = useState<any>(null);
  const [analysis, setAnalysis] = useState("");

  // Fast metrics updates
  useEffect(() => {
    const fetchMetrics = () => {
      fetch("http://127.0.0.1:8000/metrics")
        .then((res) => res.json())
        .then((data) => setMetrics(data));
    };

    fetchMetrics();

    const interval = setInterval(fetchMetrics, 3000);

    return () => clearInterval(interval);
  }, []);

  // Slow AI analysis (fetch once)
  useEffect(() => {
    fetch("http://127.0.0.1:8000/analyze")
      .then((res) => res.json())
      .then((data) => setAnalysis(data.analysis));
  }, []);

  const chartData = metrics
    ? [
        { name: "CPU", value: metrics.cpu },
        { name: "Memory", value: metrics.memory },
        { name: "Disk", value: metrics.disk },
      ]
    : [];

  return (
    <main className="p-10">
      <h1 className="text-4xl font-bold mb-6">AI Cloud Ops Dashboard</h1>

      {!metrics ? (
        <p>Loading metrics...</p>
      ) : (
        <div className="space-y-4">
          <div className="text-xl">CPU: {metrics.cpu}%</div>

          <div className="text-xl">Memory: {metrics.memory}%</div>

          <div className="text-xl">Disk: {metrics.disk}%</div>

          <LineChart width={600} height={300} data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" />
          </LineChart>

          <div className="mt-6">
            <h2 className="text-2xl font-bold mb-2">Alerts</h2>

            {metrics.alerts.length === 0 ? (
              <p>No active alerts</p>
            ) : (
              metrics.alerts.map((alert: string, index: number) => (
                <div key={index} className="p-3 mb-2 border rounded-lg">
                  {alert}
                </div>
              ))
            )}
          </div>

          <div className="mt-8 p-4 border rounded-xl">
            <h2 className="text-2xl font-bold mb-2">AI Incident Analysis</h2>

            {analysis ? <p>{analysis}</p> : <p>Generating AI analysis...</p>}
          </div>
        </div>
      )}
    </main>
  );
}
