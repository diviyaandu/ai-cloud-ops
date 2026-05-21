import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import type { MetricPoint } from "@/types/metrics";

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-time">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.stroke }}>
          {p.name.toUpperCase()}: {p.value}%
        </p>
      ))}
    </div>
  );
}

const SERIES = [
  { key: "cpu", color: "#60a5fa", gradId: "gcpu" },
  { key: "memory", color: "#34d399", gradId: "gmem" },
  { key: "disk", color: "#facc15", gradId: "gdisk" },
] as const;

type Props = { history: MetricPoint[] };

export default function MetricsChart({ history }: Props) {
  return (
    <div className="panel span-2">
      <p className="panel-title">Metric History</p>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart
          data={history}
          margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
        >
          <defs>
            {SERIES.map(({ color, gradId }) => (
              <linearGradient
                key={gradId}
                id={gradId}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="5%" stopColor={color} stopOpacity={0.25} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2a38" />
          <XAxis
            dataKey="t"
            tick={{
              fontSize: 9,
              fill: "#374151",
              fontFamily: "JetBrains Mono",
            }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{
              fontSize: 9,
              fill: "#374151",
              fontFamily: "JetBrains Mono",
            }}
            tickLine={false}
            axisLine={false}
            domain={[0, 100]}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip content={<CustomTooltip />} />
          {SERIES.map(({ key, color, gradId }) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color}
              strokeWidth={1.5}
              fill={`url(#${gradId})`}
              dot={false}
              name={key}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
      <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
        {SERIES.map(({ key, color }) => (
          <span
            key={key}
            style={{
              fontSize: 10,
              color,
              display: "flex",
              alignItems: "center",
              gap: 5,
            }}
          >
            <span
              style={{
                width: 16,
                height: 2,
                background: color,
                display: "inline-block",
                borderRadius: 1,
              }}
            />
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </span>
        ))}
      </div>
    </div>
  );
}
