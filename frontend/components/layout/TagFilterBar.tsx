"use client";

interface TagFilterBarProps {
  tagValues: Record<string, string[]>;
  activeFilters: Record<string, string>;
  onFilter: (key: string, value: string) => void;
  onClear: () => void;
}

const KEYS = ["Project", "Environment", "Owner", "Application"];

export default function TagFilterBar({
  tagValues,
  activeFilters,
  onFilter,
  onClear,
}: TagFilterBarProps) {
  const hasActive = Object.values(activeFilters).some(Boolean);

  return (
    <div className="tag-filter-bar">
      {KEYS.map((k) => (
        <select
          key={k}
          value={activeFilters[k] || ""}
          onChange={(e) => onFilter(k, e.target.value)}
          className="tag-select"
        >
          <option value="">{k}</option>
          {(tagValues[k] || []).map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      ))}
      {hasActive && (
        <button className="tag-clear" onClick={onClear}>
          ✕ Clear
        </button>
      )}
    </div>
  );
}
