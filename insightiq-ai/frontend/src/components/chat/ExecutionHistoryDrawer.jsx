import React, { useEffect, useState } from "react";
import { X, Clock, Terminal, RotateCcw, Trash2, CheckCircle2, History } from "lucide-react";
import { analystService } from "../../services";

export const ExecutionHistoryDrawer = ({ isOpen, onClose, onSelectQuery }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const records = await analystService.getHistory();
      if (Array.isArray(records)) {
        setHistory(records);
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchHistory();
    }
  }, [isOpen]);

  const handleClear = async () => {
    try {
      await analystService.clearHistory();
      setHistory([]);
    } catch {
      // Fallback
    }
  };

  if (!isOpen) return null;

  return (
    <div
      data-testid="execution-history-drawer"
      className="fixed inset-0 z-50 bg-navy-950/40 backdrop-blur-xs flex justify-end"
    >
      <div className="w-full max-w-md bg-surface h-full shadow-modal border-l border-surface-border flex flex-col text-xs">
        {/* Drawer Header */}
        <div className="px-5 py-4 border-b border-surface-border flex items-center justify-between bg-surface-subtle">
          <div className="flex items-center gap-2">
            <History size={16} className="text-brand-600" />
            <h3 className="font-bold text-navy-900 text-sm">
              Analytics Audit History
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <button
                onClick={handleClear}
                title="Clear all execution history"
                className="p-1.5 text-navy-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
              >
                <Trash2 size={15} />
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 text-navy-400 hover:text-navy-700 hover:bg-black/5 rounded-lg transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Drawer Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading && (
            <div className="py-12 text-center text-navy-500">
              Loading audit logs...
            </div>
          )}

          {!loading && history.length === 0 && (
            <div className="py-16 text-center text-navy-400 space-y-2">
              <Clock size={28} className="mx-auto text-navy-300" />
              <p className="text-xs font-medium">No execution history recorded yet.</p>
              <p className="text-[11px]">
                Inquiries sent to the AI Analyst will be logged here for transparent auditing.
              </p>
            </div>
          )}

          {!loading &&
            history.map((record) => (
              <div
                key={record.id}
                className="p-3 bg-surface-subtle border border-surface-border rounded-xl space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-navy-900 text-xs">
                    {record.question}
                  </p>
                  <button
                    onClick={() => {
                      onSelectQuery(record.question);
                      onClose();
                    }}
                    title="Re-run inquiry"
                    className="p-1 bg-brand-50 hover:bg-brand-100 text-brand-700 rounded-lg transition-colors shrink-0 flex items-center gap-1 text-[11px] font-medium px-2 py-0.5"
                  >
                    <RotateCcw size={11} />
                    <span>Re-run</span>
                  </button>
                </div>

                <div className="flex items-center gap-2 text-[10px] text-navy-500 font-mono">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 size={11} className="text-emerald-600" />
                    {record.duration_ms}ms
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Terminal size={11} />
                    {record.tools_count} tool{record.tools_count > 1 ? "s" : ""}
                  </span>
                  <span>•</span>
                  <span>{new Date(record.timestamp).toLocaleTimeString()}</span>
                </div>

                {record.tools_executed && record.tools_executed.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {record.tools_executed.map((tool, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-1.5 py-0.5 bg-surface border border-surface-border text-navy-600 rounded"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default ExecutionHistoryDrawer;
