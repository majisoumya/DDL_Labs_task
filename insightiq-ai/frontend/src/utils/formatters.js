/**
 * Standardized Formatting Utilities for Business Intelligence
 */

export const formatCurrency = (value, options = {}) => {
  if (value === null || value === undefined) return "—";
  const num = typeof value === "number" ? value : parseFloat(value);
  if (isNaN(num)) return "—";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: options.currency || "USD",
    minimumFractionDigits: options.minimumFractionDigits ?? 2,
    maximumFractionDigits: options.maximumFractionDigits ?? 2,
  }).format(num);
};

export const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined) return "—";
  const num = typeof value === "number" ? value : parseFloat(value);
  if (isNaN(num)) return "—";

  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

export const formatPercentage = (value, decimals = 1, showSign = false) => {
  if (value === null || value === undefined) return "—";
  const num = typeof value === "number" ? value : parseFloat(value);
  if (isNaN(num)) return "—";

  const prefix = showSign && num > 0 ? "+" : "";
  return `${prefix}${num.toFixed(decimals)}%`;
};

export const formatDate = (dateString, options = {}) => {
  if (!dateString) return "—";
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.toLocaleDateString("en-US", {
      year: options.year || "numeric",
      month: options.month || "short",
      day: options.day || "numeric",
      ...options,
    });
  } catch {
    return dateString;
  }
};
