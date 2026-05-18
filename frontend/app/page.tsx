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

  const getStatusColor = (value: number) => {
    if (value > 80) return "text-red-400";
    if (value > 60) return "text-yellow-400";
    return "text-green-400";
  };

  return (
    <main className="min-h-screen bg-black text-white p-8">
      <h1 className="text-5xl font-bold mb-10">AI Cloud Ops Dashboard</h1>

      {!metrics ? (
        <p className="text-xl">Loading metrics...</p>
      ) : (
        <div className="space-y-8">
          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-lg">
              <h2 className="text-xl mb-2">CPU Usage</h2>
              <p
                className={`text-4xl font-bold ${getStatusColor(metrics.cpu)}`}
              >
                {metrics.cpu}%
              </p>
            </div>

            <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-lg">
              <h2 className="text-xl mb-2">Memory Usage</h2>
              <p
                className={`text-4xl font-bold ${getStatusColor(metrics.memory)}`}
              >
                {metrics.memory}%
              </p>
            </div>

            <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-lg">
              <h2 className="text-xl mb-2">Disk Usage</h2>
              <p
                className={`text-4xl font-bold ${getStatusColor(metrics.disk)}`}
              >
                {metrics.disk}%
              </p>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-lg">
            <h2 className="text-2xl font-bold mb-4">System Metrics</h2>

            <LineChart width={700} height={300} data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#60a5fa"
                strokeWidth={3}
              />
            </LineChart>
          </div>

          {/* Alerts */}
          <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-lg">
            <h2 className="text-2xl font-bold mb-4">Active Alerts</h2>

            {metrics.alerts.length === 0 ? (
              <p className="text-green-400">No active alerts</p>
            ) : (
              metrics.alerts.map((alert: string, index: number) => (
                <div
                  key={index}
                  className="bg-red-500/20 border border-red-500 p-4 rounded-xl mb-3"
                >
                  {alert}
                </div>
              ))
            )}
          </div>

          {/* AI Analysis */}
          <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-lg">
            <h2 className="text-2xl font-bold mb-4">AI Incident Analysis</h2>

            {analysis ? (
              <div className="whitespace-pre-wrap text-zinc-300 leading-7">
                {analysis}
              </div>
            ) : (
              <p>Generating AI analysis...</p>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
