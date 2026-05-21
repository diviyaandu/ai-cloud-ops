export type MetricPoint = {
  t: string;
  cpu: number;
  memory: number;
  disk: number;
};

export type AlertSeverity = "high" | "medium" | "low";

export type Alert = {
  text: string;
  severity: AlertSeverity;
};

export type Metrics = {
  cpu: number;
  memory: number;
  disk: number;
  alerts: string[];
  severity: string;
};

export type ChatMessage = {
  role: "user" | "ai";
  text: string;
};
