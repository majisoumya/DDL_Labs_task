import React from "react";

export const Card = ({
  children,
  className = "",
  title,
  subtitle,
  action,
  headerBorder = true,
  ...props
}) => {
  return (
    <div
      data-testid="ui-card"
      className={`bg-surface rounded-xl border border-surface-border shadow-subtle hover:shadow-card transition-shadow duration-200 overflow-hidden ${className}`}
      {...props}
    >
      {(title || subtitle || action) && (
        <div
          className={`px-5 py-4 flex items-center justify-between ${
            headerBorder ? "border-b border-surface-border" : ""
          }`}
        >
          <div>
            {title && (
              <h3 className="text-sm font-semibold text-navy-900 tracking-tight">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-navy-600 mt-0.5">{subtitle}</p>
            )}
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
};

export default Card;
