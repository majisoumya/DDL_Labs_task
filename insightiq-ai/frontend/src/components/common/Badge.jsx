import React from "react";

export const Badge = ({
  children,
  variant = "neutral", // "neutral", "brand", "success", "warning", "danger"
  size = "md", // "sm", "md"
  className = "",
  ...props
}) => {
  const variantStyles = {
    neutral: "bg-surface-muted text-navy-700 border-surface-border",
    brand: "bg-brand-50 text-brand-700 border-brand-100",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    danger: "bg-rose-50 text-rose-700 border-rose-200",
  };

  const sizeStyles = {
    sm: "px-1.5 py-0.5 text-[10px]",
    md: "px-2 py-0.5 text-xs",
  };

  return (
    <span
      data-testid="ui-badge"
      className={`inline-flex items-center font-medium border rounded-md uppercase tracking-wider ${
        variantStyles[variant] || variantStyles.neutral
      } ${sizeStyles[size] || sizeStyles.md} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

export default Badge;
