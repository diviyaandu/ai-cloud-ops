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

  useEffect(() => {
    fetch("http://127.0.0.1:8000/metrics")
      .then((res) => res.json())
      .then((data) => setMetrics(data));
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
      <h1 className="text-4xl font-bold mb-6">
        AI Cloud Ops Dashboard
      </h1>

      {metrics && (
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
        </div>
      )}
    </main>
  );
}