import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export const ErrorState = ({
  title = "Failed to load analytical data",
  message = "An error occurred while communicating with the analytics warehouse.",
  onRetry,
  className = "",
  ...props
}) => {
  return (
    <div
      data-testid="ui-error-state"
      className={`p-6 bg-rose-50/50 border border-rose-200 rounded-xl text-center flex flex-col items-center justify-center ${className}`}
      {...props}
    >
      <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 mb-3">
        <AlertTriangle size={20} />
      </div>
      <h4 className="text-sm font-semibold text-rose-900">{title}</h4>
      <p className="text-xs text-rose-700 max-w-md mt-1">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 bg-surface text-xs font-medium text-navy-800 border border-surface-border rounded-lg shadow-sm hover:bg-surface-subtle transition-colors"
        >
          <RefreshCw size={13} />
          Retry Request
        </button>
      )}
    </div>
  );
};

export default ErrorState;
