import React from "react";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

export const MetricCard = ({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  trend = "neutral", // "positive", "negative", "neutral"
  subtext,
  className = "",
  ...props
}) => {
  const isPositive = trend === "positive" || (typeof change === "number" && change > 0);
  const isNegative = trend === "negative" || (typeof change === "number" && change < 0);

  return (
    <div
      data-testid="ui-metric-card"
      className={`bg-surface p-5 rounded-xl border border-surface-border shadow-subtle hover:shadow-card transition-shadow duration-200 flex flex-col justify-between ${className}`}
      {...props}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-navy-600">
          {title}
        </span>
        {Icon && (
          <div className="p-2 bg-surface-muted rounded-lg text-brand-600">
            <Icon size={18} />
          </div>
        )}
      </div>

      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight text-navy-900">
          {value ?? "—"}
        </div>

        {(change !== undefined || subtext) && (
          <div className="mt-2 flex items-center gap-1.5 text-xs">
            {change !== undefined && (
              <span
                className={`inline-flex items-center gap-0.5 font-semibold px-1.5 py-0.5 rounded ${
                  isPositive
                    ? "bg-emerald-50 text-emerald-700"
                    : isNegative
                    ? "bg-rose-50 text-rose-700"
                    : "bg-surface-muted text-navy-600"
                }`}
              >
                {isPositive ? (
                  <ArrowUpRight size={13} />
                ) : isNegative ? (
                  <ArrowDownRight size={13} />
                ) : (
                  <Minus size={13} />
                )}
                {typeof change === "number"
                  ? `${Math.abs(change).toFixed(1)}%`
                  : change}
              </span>
            )}
            {(changeLabel || subtext) && (
              <span className="text-navy-600 truncate">
                {changeLabel || subtext}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricCard;
