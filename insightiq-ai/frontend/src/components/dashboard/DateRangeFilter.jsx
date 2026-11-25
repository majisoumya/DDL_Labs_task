import React, { useState } from "react";
import { Calendar, RefreshCw, Filter, Check, Download } from "lucide-react";

const PRESETS = [
  { id: "all", label: "All Data", start: "", end: "" },
  { id: "ytd", label: "FY 2024", start: "2024-01-01", end: "2024-06-30" },
  { id: "q1", label: "Q1 2024", start: "2024-01-01", end: "2024-03-31" },
  { id: "q2", label: "Q2 2024", start: "2024-04-01", end: "2024-06-30" },
];

export const DateRangeFilter = ({
  startDate = "",
  endDate = "",
  onChange,
  onRefresh,
  onExport,
  isRefreshing = false,
  lastUpdated,
  className = "",
}) => {
  const [activePreset, setActivePreset] = useState("all");
  const [customStart, setCustomStart] = useState(startDate);
  const [customEnd, setCustomEnd] = useState(endDate);

  const handlePresetSelect = (preset) => {
    setActivePreset(preset.id);
    setCustomStart(preset.start);
    setCustomEnd(preset.end);
    onChange({ startDate: preset.start, endDate: preset.end });
  };

  const handleCustomApply = (e) => {
    e.preventDefault();
    setActivePreset("custom");
    onChange({ startDate: customStart, endDate: customEnd });
  };

  return (
    <div
      data-testid="date-range-filter"
      className={`bg-surface p-4 rounded-xl border border-surface-border shadow-subtle flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 ${className}`}
    >
      {/* Left: Quick Presets */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-navy-600 mr-2 flex items-center gap-1.5">
          <Filter size={13} />
          Period:
        </span>
        {PRESETS.map((preset) => {
          const isSelected = activePreset === preset.id;
          return (
            <button
              key={preset.id}
              onClick={() => handlePresetSelect(preset)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                isSelected
                  ? "bg-navy-900 text-white shadow-xs"
                  : "bg-surface-subtle hover:bg-surface-muted text-navy-700 border border-surface-border"
              }`}
            >
              {preset.label}
            </button>
          );
        })}
      </div>

      {/* Right: Custom Date Pickers & Refresh Button */}
      <div className="flex flex-wrap items-center gap-2">
        <form onSubmit={handleCustomApply} className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-surface-subtle px-2.5 py-1.5 rounded-lg border border-surface-border text-xs">
            <Calendar size={13} className="text-navy-600" />
            <input
              type="date"
              aria-label="Start date"
              value={customStart}
              onChange={(e) => {
                setCustomStart(e.target.value);
                setActivePreset("custom");
              }}
              className="bg-transparent text-navy-900 focus:outline-hidden text-xs"
            />
            <span className="text-navy-600 font-mono">→</span>
            <input
              type="date"
              aria-label="End date"
              value={customEnd}
              onChange={(e) => {
                setCustomEnd(e.target.value);
                setActivePreset("custom");
              }}
              className="bg-transparent text-navy-900 focus:outline-hidden text-xs"
            />
          </div>

          <button
            type="submit"
            className="px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
          >
            Apply
          </button>
        </form>

        {/* Data Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            aria-label="Refresh analytics data"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-subtle hover:bg-surface-muted border border-surface-border rounded-lg text-xs font-medium text-navy-700 shadow-xs transition-colors disabled:opacity-60"
          >
            <RefreshCw
              size={13}
              className={isRefreshing ? "animate-spin text-brand-600" : "text-navy-600"}
            />
            <span>{isRefreshing ? "Syncing..." : "Refresh"}</span>
          </button>
        )}

        {/* CSV Export Button */}
        {onExport && (
          <button
            onClick={onExport}
            title="Download verified analytics data as CSV"
            aria-label="Export CSV"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-subtle hover:bg-surface-muted border border-surface-border rounded-lg text-xs font-medium text-navy-700 shadow-xs transition-colors"
          >
            <Download size={13} className="text-navy-600" />
            <span>Export CSV</span>
          </button>
        )}

        {/* Last Synced Badge */}
        {lastUpdated && (
          <span className="text-[11px] text-navy-600 hidden lg:inline font-mono">
            Updated: {lastUpdated}
          </span>
        )}
      </div>
    </div>
  );
};

export default DateRangeFilter;
