import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { AlertCircle, BarChart3, Database } from "lucide-react";

const DEFAULT_PALETTE = [
  "#3B82F6", // Blue
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#EF4444", // Red
  "#8B5CF6", // Violet
  "#06B6D4", // Cyan
  "#EC4899", // Pink
  "#F97316", // Orange
];

const formatNumber = (value, unit = "") => {
  if (value === null || value === undefined) return "—";
  if (typeof value !== "number") {
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    value = num;
  }
  if (unit === "$" || (typeof value === "number" && value >= 100)) {
    return value.toLocaleString("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }
  return value.toLocaleString("en-US");
};

const CustomTooltip = ({ active, payload, label, unit }) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div
      data-testid="chart-custom-tooltip"
      style={{
        backgroundColor: "#FFFFFF",
        border: "1px solid #E2E8F0",
        borderRadius: "8px",
        padding: "8px 12px",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        fontSize: "12px",
      }}
    >
      <div style={{ fontWeight: 600, color: "#1E293B", marginBottom: "4px" }}>
        {label}
      </div>
      {payload.map((entry, index) => (
        <div
          key={`item-${index}`}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            color: entry.color || "#475569",
            margin: "2px 0",
          }}
        >
          <span
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: entry.color || "#3B82F6",
              display: "inline-block",
            }}
          />
          <span style={{ textTransform: "capitalize" }}>{entry.name}:</span>
          <span style={{ fontWeight: 600 }}>
            {unit === "$" ? `$${formatNumber(entry.value, unit)}` : formatNumber(entry.value, unit)}
            {unit && unit !== "$" ? ` ${unit}` : ""}
          </span>
        </div>
      ))}
    </div>
  );
};

export const DynamicChart = ({
  spec,
  height = 320,
  className = "",
  showTitle = true,
  borderless = false,
}) => {
  // 1. Guard against null or missing spec
  if (!spec) {
    return (
      <div
        data-testid="chart-empty-state"
        style={{
          height: `${height}px`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#F8FAFC",
          borderRadius: "8px",
          border: "1px dashed #CBD5E1",
          color: "#64748B",
        }}
      >
        <Database size={32} style={{ marginBottom: "8px", opacity: 0.5 }} />
        <span style={{ fontSize: "14px" }}>No chart specification provided.</span>
      </div>
    );
  }

  const {
    chart_type,
    title,
    x_key,
    y_key,
    y_keys,
    data = [],
    description,
    metadata = {},
  } = spec;

  const normalizedType = chart_type ? chart_type.toLowerCase() : "";
  const unit = metadata?.unit || (y_key && y_key.includes("revenue") ? "$" : "");
  const palette = metadata?.color_palette || DEFAULT_PALETTE;

  // 2. Validate Chart Type
  const supportedTypes = ["line", "bar", "pie", "area"];
  if (!supportedTypes.includes(normalizedType)) {
    return (
      <div
        data-testid="chart-unsupported-error"
        style={{
          height: `${height}px`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#FEF2F2",
          borderRadius: "8px",
          border: "1px solid #FECACA",
          color: "#991B1B",
          padding: "16px",
          textAlign: "center",
        }}
      >
        <AlertCircle size={32} style={{ marginBottom: "8px" }} />
        <div style={{ fontWeight: 600, fontSize: "14px" }}>
          Unsupported Chart Visualization
        </div>
        <div style={{ fontSize: "12px", marginTop: "4px" }}>
          Visualization format &ldquo;{chart_type}&rdquo; is not supported. Supported formats: line, bar, pie, area.
        </div>
      </div>
    );
  }

  // 3. Handle Empty Dataset Gracefully
  if (!data || data.length === 0) {
    return (
      <div
        data-testid="chart-empty-data"
        style={{
          border: "1px solid #E2E8F0",
          borderRadius: "8px",
          backgroundColor: "#FFFFFF",
          padding: "16px",
        }}
      >
        <div style={{ marginBottom: "12px" }}>
          <h3 style={{ fontSize: "16px", fontWeight: 600, color: "#0F172A", margin: 0 }}>
            {title || "Chart Visualization"}
          </h3>
          {description && (
            <p style={{ fontSize: "12px", color: "#64748B", margin: "4px 0 0 0" }}>
              {description}
            </p>
          )}
        </div>
        <div
          style={{
            height: `${height - 60}px`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#F8FAFC",
            borderRadius: "6px",
            color: "#64748B",
            fontSize: "13px",
          }}
        >
          <BarChart3 size={28} style={{ marginBottom: "8px", opacity: 0.4 }} />
          <span>No data available for the specified timeframe or query.</span>
        </div>
      </div>
    );
  }

  // 4. Validate Required Keys
  if (!x_key || !y_key) {
    return (
      <div
        data-testid="chart-missing-keys-error"
        style={{
          height: `${height}px`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#FFFBEB",
          borderRadius: "8px",
          border: "1px solid #FDE68A",
          color: "#92400E",
          padding: "16px",
        }}
      >
        <AlertCircle size={28} style={{ marginBottom: "8px" }} />
        <span style={{ fontWeight: 600, fontSize: "14px" }}>Invalid Chart Specification</span>
        <span style={{ fontSize: "12px", marginTop: "4px" }}>
          Specification missing required &ldquo;x_key&rdquo; or &ldquo;y_key&rdquo;.
        </span>
      </div>
    );
  }

  // Render Recharts by chart_type
  const renderChart = () => {
    switch (normalizedType) {
      case "line": {
        const seriesKeys = y_keys && y_keys.length > 0 ? y_keys : [y_key];
        return (
          <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
            <XAxis dataKey={x_key} stroke="#64748B" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => (unit === "$" ? `$${formatNumber(v)}` : formatNumber(v))}
            />
            <Tooltip content={<CustomTooltip unit={unit} />} />
            {seriesKeys.length > 1 && <Legend wrapperStyle={{ fontSize: "12px" }} />}
            {seriesKeys.map((key, idx) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={key.replace(/_/g, " ")}
                stroke={palette[idx % palette.length]}
                strokeWidth={2.5}
                dot={{ r: 3, fill: palette[idx % palette.length] }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        );
      }

      case "area": {
        const primaryColor = palette[0];
        return (
          <AreaChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={primaryColor} stopOpacity={0.4} />
                <stop offset="95%" stopColor={primaryColor} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
            <XAxis dataKey={x_key} stroke="#64748B" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => (unit === "$" ? `$${formatNumber(v)}` : formatNumber(v))}
            />
            <Tooltip content={<CustomTooltip unit={unit} />} />
            <Area
              type="monotone"
              dataKey={y_key}
              name={y_key.replace(/_/g, " ")}
              stroke={primaryColor}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#areaGradient)"
            />
          </AreaChart>
        );
      }

      case "bar": {
        return (
          <BarChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
            <XAxis dataKey={x_key} stroke="#64748B" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => (unit === "$" ? `$${formatNumber(v)}` : formatNumber(v))}
            />
            <Tooltip content={<CustomTooltip unit={unit} />} />
            <Bar dataKey={y_key} name={y_key.replace(/_/g, " ")} fill={palette[0]} radius={[4, 4, 0, 0]}>
              {data.map((_, idx) => (
                <Cell key={`cell-${idx}`} fill={palette[idx % palette.length]} />
              ))}
            </Bar>
          </BarChart>
        );
      }

      case "pie": {
        return (
          <PieChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
            <Tooltip
              formatter={(value, name) => [
                unit === "$" ? `$${formatNumber(value, unit)}` : formatNumber(value, unit),
                name,
              ]}
            />
            <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
            <Pie
              data={data}
              dataKey={y_key}
              nameKey={x_key}
              cx="50%"
              cy="50%"
              outerRadius={height > 250 ? 90 : 70}
              innerRadius={height > 250 ? 40 : 25}
              paddingAngle={2}
              label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              labelLine={false}
            >
              {data.map((_, idx) => (
                <Cell key={`pie-cell-${idx}`} fill={palette[idx % palette.length]} />
              ))}
            </Pie>
          </PieChart>
        );
      }

      default:
        return null;
    }
  };

  return (
    <div
      data-testid="dynamic-chart-container"
      className={`insightiq-chart ${className}`}
      style={
        borderless
          ? { width: "100%" }
          : {
              border: "1px solid #E2E8F0",
              borderRadius: "8px",
              backgroundColor: "#FFFFFF",
              padding: "16px",
              boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)",
            }
      }
    >
      {showTitle && title && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
          <div>
            <h3
              data-testid="chart-title"
              style={{ fontSize: "15px", fontWeight: 600, color: "#0F172A", margin: 0 }}
            >
              {title}
            </h3>
            {description && (
              <p
                data-testid="chart-description"
                style={{ fontSize: "12px", color: "#64748B", margin: "4px 0 0 0" }}
              >
                {description}
              </p>
            )}
          </div>
          <span
            style={{
              fontSize: "11px",
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "#475569",
              backgroundColor: "#F1F5F9",
              padding: "2px 8px",
              borderRadius: "4px",
            }}
          >
            {normalizedType}
          </span>
        </div>
      )}

      <div style={{ width: "100%", height: `${height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DynamicChart;
