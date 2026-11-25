import React, { useState } from "react";
import { Terminal, CheckCircle2, XCircle, ChevronDown, ChevronRight, Clock } from "lucide-react";

export const ToolStatusPanel = ({ toolExecutions = [], className = "" }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!toolExecutions || toolExecutions.length === 0) return null;

  const totalTimeMs = toolExecutions.reduce(
    (sum, t) => sum + (t.execution_time_ms || 0),
    0
  );

  return (
    <div
      data-testid="tool-status-panel"
      className={`rounded-xl border border-surface-border bg-surface-subtle overflow-hidden text-xs ${className}`}
    >
      {/* Header Bar */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between text-navy-700 hover:bg-surface-muted transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-brand-600" />
          <span className="font-semibold text-navy-900">
            {toolExecutions.length} Analytics Tool{toolExecutions.length > 1 ? "s" : ""} Executed
          </span>
          <span className="text-[11px] text-navy-600 font-mono flex items-center gap-1">
            <Clock size={11} />
            {totalTimeMs.toFixed(1)}ms
          </span>
        </div>
        <div className="flex items-center gap-1 text-navy-600">
          <span className="text-[11px]">Audit Details</span>
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </div>
      </button>

      {/* Expanded Tool Details */}
      {isOpen && (
        <div className="p-3 border-t border-surface-border space-y-2 bg-surface">
          {toolExecutions.map((tool, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg border border-surface-border bg-surface-subtle flex flex-col gap-1.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {tool.success ? (
                    <CheckCircle2 size={13} className="text-emerald-600" />
                  ) : (
                    <XCircle size={13} className="text-rose-600" />
                  )}
                  <span className="font-mono font-semibold text-navy-900">
                    {tool.tool_name}
                  </span>
                </div>
                <span className="text-[10px] font-mono text-navy-600">
                  {tool.execution_time_ms ? `${tool.execution_time_ms.toFixed(1)}ms` : "—"}
                </span>
              </div>

              {/* Arguments (Sanitized) */}
              {tool.arguments && Object.keys(tool.arguments).length > 0 && (
                <div className="text-[11px] font-mono text-navy-600 bg-surface px-2 py-1 rounded border border-surface-border">
                  <span className="text-navy-400">args: </span>
                  {JSON.stringify(tool.arguments)}
                </div>
              )}

              {tool.error && (
                <div className="text-[11px] text-rose-600 font-medium">
                  Error: {tool.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ToolStatusPanel;
