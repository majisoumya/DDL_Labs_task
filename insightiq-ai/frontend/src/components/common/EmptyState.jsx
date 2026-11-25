import React from "react";
import { Database } from "lucide-react";

export const EmptyState = ({
  icon: Icon = Database,
  title = "No Data Available",
  description = "There are no records matching your selected parameters or time window.",
  action,
  className = "",
  ...props
}) => {
  return (
    <div
      data-testid="ui-empty-state"
      className={`flex flex-col items-center justify-center p-8 text-center bg-surface-subtle border border-dashed border-surface-border rounded-xl ${className}`}
      {...props}
    >
      <div className="w-12 h-12 rounded-full bg-surface-muted flex items-center justify-center text-navy-600 mb-3">
        <Icon size={24} />
      </div>
      <h4 className="text-sm font-semibold text-navy-900">{title}</h4>
      <p className="text-xs text-navy-600 max-w-sm mt-1">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};

export default EmptyState;
