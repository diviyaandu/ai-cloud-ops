export type CloudResources = {
  total: number;
  virtual_machines: number;
  aks_clusters: number;
  app_services: number;
  storage_accounts: number;
  cognitive_services: number;
  mode: "live" | "mock";
  raw_by_type: { type: string; count: number; regions: string[] }[];
};
