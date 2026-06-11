export const TYPE_ACCENTS: Record<string, string> = {
  "microsoft.compute/virtualmachines": "#60a5fa",
  "microsoft.containerservice/managedclusters": "#34d399",
  "microsoft.web/sites": "#fb923c",
  "microsoft.storage/storageaccounts": "#facc15",
  "microsoft.cognitiveservices/accounts": "#a78bfa",
};

export const DEFAULT_ACCENT = "#2dd4bf";

export function labelFor(type: string): string {
  const short = type.split("/").pop() ?? type;
  return short.replace(/([a-z])([A-Z])/g, "$1 $2");
}
