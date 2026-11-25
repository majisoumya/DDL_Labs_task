import React from "react";

export const Skeleton = ({ className = "", ...props }) => {
  return (
    <div
      data-testid="ui-skeleton"
      className={`animate-pulse bg-slate-200/80 rounded ${className}`}
      {...props}
    />
  );
};

export const CardSkeleton = () => {
  return (
    <div
      data-testid="ui-card-skeleton"
      className="bg-surface p-5 rounded-xl border border-surface-border shadow-subtle animate-pulse space-y-3"
    >
      <div className="flex justify-between items-center">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-36" />
      <div className="flex gap-2 items-center">
        <Skeleton className="h-4 w-12" />
        <Skeleton className="h-3 w-28" />
      </div>
    </div>
  );
};

export const ChartSkeleton = ({ height = 300 }) => {
  return (
    <div
      data-testid="ui-chart-skeleton"
      className="bg-surface p-5 rounded-xl border border-surface-border shadow-subtle animate-pulse space-y-4"
    >
      <div className="flex justify-between items-center">
        <div className="space-y-1.5">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-48" />
        </div>
        <Skeleton className="h-6 w-16 rounded" />
      </div>
      <div
        className="w-full flex items-end justify-between gap-3 pt-6"
        style={{ height: `${height}px` }}
      >
        {[40, 65, 85, 30, 95, 50, 70].map((h, idx) => (
          <Skeleton
            key={idx}
            className="flex-1 rounded-t"
            style={{ height: `${h}%` }}
          />
        ))}
      </div>
    </div>
  );
};

export const TableSkeleton = ({ rows = 5, cols = 4 }) => {
  return (
    <div
      data-testid="ui-table-skeleton"
      className="bg-surface rounded-xl border border-surface-border shadow-subtle animate-pulse overflow-hidden"
    >
      <div className="p-4 border-b border-surface-border flex justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-20" />
      </div>
      <div className="divide-y divide-surface-border">
        {Array.from({ length: rows }).map((_, rIdx) => (
          <div key={rIdx} className="p-4 flex gap-4">
            {Array.from({ length: cols }).map((_, cIdx) => (
              <Skeleton
                key={cIdx}
                className="h-4 flex-1"
                style={{ width: `${100 / cols}%` }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Skeleton;
