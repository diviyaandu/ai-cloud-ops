export type RawResource = {
  type: string;
  count: number;
  regions: string[];
};

export type CloudResources = {
  total: number;
  mode: "live" | "mock";
  raw_by_type: RawResource[];
  // legacy fields kept for backward compat
  virtual_machines?: number;
  aks_clusters?: number;
  app_services?: number;
  storage_accounts?: number;
  cognitive_services?: number;
};
