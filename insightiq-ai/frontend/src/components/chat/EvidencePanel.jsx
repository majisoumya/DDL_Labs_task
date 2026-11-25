import React from "react";
import { ShieldCheck, Lightbulb, AlertCircle, FileText } from "lucide-react";
import { Badge } from "../common";
import { formatCurrency, formatNumber } from "../../utils/formatters";

export const EvidencePanel = ({
  metrics = [],
  insights = [],
  dataLimitations = null,
  className = "",
}) => {
  const hasMetrics = metrics && metrics.length > 0;
  const hasInsights = insights && insights.length > 0;

  if (!hasMetrics && !hasInsights && !dataLimitations) return null;

  const formatMetricValue = (val, name) => {
    if (typeof val === "number") {
      const lower = (name || "").toLowerCase();
      if (lower.includes("revenue") || lower.includes("spend") || lower.includes("aov") || lower.includes("price") || lower.includes("delta")) {
        return formatCurrency(val);
      }
      return formatNumber(val);
    }
    return String(val);
  };

  return (
    <div
      data-testid="evidence-panel"
      className={`space-y-3 rounded-xl border border-surface-border bg-surface p-4 text-xs ${className}`}
    >
      {/* 1. Verified Metrics Section */}
      {hasMetrics && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 font-semibold text-navy-900 uppercase tracking-wider text-[11px]">
            <ShieldCheck size={14} className="text-emerald-600" />
            <span>Verified Ground-Truth Metrics</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {metrics.map((m, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-lg border border-surface-border bg-surface-subtle flex flex-col justify-between"
              >
                <div className="text-[11px] text-navy-600 font-medium truncate">
                  {m.metric_name}
                </div>
                <div className="text-sm font-bold text-navy-900 font-mono mt-1">
                  {formatMetricValue(m.exact_value, m.metric_name)}
                </div>
                {m.source && (
                  <div className="text-[10px] text-navy-400 mt-1 font-mono truncate">
                    source: {m.source}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 2. Structured Insights & Recommendations */}
      {hasInsights && (
        <div className="space-y-2 pt-2 border-t border-surface-border">
          {insights.map((insight, idx) => (
            <div key={idx} className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-navy-900">{insight.title}</span>
                {insight.severity && (
                  <Badge
                    variant={
                      insight.severity === "critical"
                        ? "danger"
                        : insight.severity === "warning"
                        ? "warning"
                        : "brand"
                    }
                    size="sm"
                  >
                    {insight.severity}
                  </Badge>
                )}
              </div>
              <p className="text-navy-700 text-xs leading-relaxed">
                {insight.finding}
              </p>

              {/* Actionable Executive Recommendation */}
              {insight.actionable_recommendation && (
                <div className="mt-2 p-2.5 rounded-lg bg-brand-50/70 border border-brand-100 flex items-start gap-2 text-brand-900">
                  <Lightbulb size={14} className="text-brand-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[11px] uppercase tracking-wider block text-brand-700">
                      Recommendation
                    </span>
                    <span className="text-xs text-brand-900">
                      {insight.actionable_recommendation}
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 3. Documented Data Limitations */}
      {dataLimitations && (
        <div className="pt-2 border-t border-surface-border flex items-start gap-2 text-[11px] text-navy-600">
          <FileText size={13} className="text-navy-400 shrink-0 mt-0.5" />
          <span>
            <strong className="text-navy-700">Data Governance Note:</strong> {dataLimitations}
          </span>
        </div>
      )}
    </div>
  );
};

export default EvidencePanel;
