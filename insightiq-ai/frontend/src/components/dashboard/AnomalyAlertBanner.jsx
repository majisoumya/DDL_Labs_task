import React, { useState } from "react";
import { AlertTriangle, ArrowRight, X, TrendingDown, ShieldAlert } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge } from "../common";

export const AnomalyAlertBanner = ({
  anomalies = [],
  executiveInsights = [],
  onInvestigate,
  className = "",
}) => {
  const [dismissed, setDismissed] = useState(false);
  const navigate = useNavigate();

  if (dismissed || !anomalies || anomalies.length === 0) return null;

  const primaryAnomaly = anomalies[0];
  const isHighSeverity = primaryAnomaly.severity === "high" || primaryAnomaly.severity === "critical";

  const handleInvestigateClick = () => {
    if (onInvestigate) {
      onInvestigate("Why did revenue decline last month?");
    } else {
      navigate("/analyst");
    }
  };

  return (
    <div
      data-testid="anomaly-alert-banner"
      className={`rounded-2xl border p-4 shadow-subtle transition-all ${
        isHighSeverity
          ? "bg-gradient-to-r from-rose-50 via-rose-50/60 to-surface border-rose-200"
          : "bg-gradient-to-r from-amber-50 via-amber-50/60 to-surface border-amber-200"
      } ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className={`p-2 rounded-xl shrink-0 ${
              isHighSeverity
                ? "bg-rose-100 text-rose-700"
                : "bg-amber-100 text-amber-700"
            }`}
          >
            {isHighSeverity ? <ShieldAlert size={18} /> : <AlertTriangle size={18} />}
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-bold text-navy-900 uppercase tracking-wider">
                Revenue Anomaly Detected
              </span>
              <Badge
                variant={isHighSeverity ? "danger" : "warning"}
                size="sm"
              >
                {primaryAnomaly.severity} Impact
              </Badge>
              {primaryAnomaly.z_score !== null && primaryAnomaly.z_score !== undefined && (
                <span className="text-[11px] font-mono text-navy-600 bg-white/80 px-2 py-0.5 rounded border border-surface-border">
                  Z-Score: {primaryAnomaly.z_score.toFixed(2)}
                </span>
              )}
            </div>

            <p className="text-xs text-navy-800 leading-relaxed max-w-3xl">
              {primaryAnomaly.description ||
                "A significant period-over-period variance was detected in historical performance metrics."}
            </p>

            {primaryAnomaly.recommendation && (
              <p className="text-[11px] text-navy-600 font-medium">
                💡 <strong className="text-navy-700">Observation:</strong> {primaryAnomaly.recommendation}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
          <button
            onClick={handleInvestigateClick}
            className="px-3.5 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl shadow-xs flex items-center gap-1.5 transition-colors"
          >
            <span>Investigate with AI</span>
            <ArrowRight size={13} />
          </button>

          <button
            onClick={() => setDismissed(true)}
            aria-label="Dismiss anomaly alert"
            className="p-1.5 text-navy-400 hover:text-navy-700 rounded-lg hover:bg-black/5 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnomalyAlertBanner;
