import React, { useState } from "react";
import { TrendingUp, DollarSign, ShoppingBag, BarChart2, Download } from "lucide-react";
import {
  MetricCard,
  Card,
  CardSkeleton,
  ChartSkeleton,
  ErrorState,
} from "../components/common";
import { DateRangeFilter } from "../components/dashboard";
import { DynamicChart } from "../components/charts/DynamicChart";
import { useAsync } from "../hooks/useAsync";
import { analyticsService, chartService, exportService } from "../services";
import { formatCurrency, formatNumber } from "../utils/formatters";

export const SalesPage = () => {
  const [chartType, setChartType] = useState("line");
  const [dateRange, setDateRange] = useState({ startDate: "", endDate: "" });

  const {
    data: salesData,
    loading: loadingSales,
    error: errorSales,
    retry: retrySales,
  } = useAsync(async () => {
    const params = {
      start_date: dateRange.startDate || undefined,
      end_date: dateRange.endDate || undefined,
    };
    const [metrics, monthlyChart, catChart] = await Promise.all([
      analyticsService.getSalesMetrics(params),
      chartService.getMonthlyRevenueChart({ ...params, chart_type: chartType }),
      chartService.getCategoryRevenueChart({ ...params, chart_type: "bar" }),
    ]);
    return { metrics, monthlyChart, catChart };
  }, [chartType, dateRange.startDate, dateRange.endDate]);

  if (loadingSales) {
    return (
      <div data-testid="sales-loading" className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <ChartSkeleton height={320} />
      </div>
    );
  }

  if (errorSales) {
    return (
      <div data-testid="sales-error" className="py-8">
        <ErrorState
          title="Could not load sales analytics"
          message={errorSales}
          onRetry={retrySales}
        />
      </div>
    );
  }

  const { metrics, monthlyChart, catChart } = salesData || {};

  return (
    <div data-testid="sales-page" className="space-y-6">
      {/* Date Range Controls & Presets */}
      <DateRangeFilter
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        onChange={setDateRange}
        onRefresh={retrySales}
        onExport={() =>
          exportService.downloadSalesCsv({
            start_date: dateRange.startDate || undefined,
            end_date: dateRange.endDate || undefined,
          })
        }
      />

      {/* Action Toolbar */}
      <div className="flex items-center justify-between bg-surface p-3.5 rounded-xl border border-surface-border shadow-subtle">
        <span className="text-xs font-semibold text-navy-800">
          Executive Sales Performance Ledger
        </span>
        <button
          onClick={() =>
            exportService.downloadSalesCsv({
              start_date: dateRange.startDate || undefined,
              end_date: dateRange.endDate || undefined,
            })
          }
          className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-subtle hover:bg-surface-muted border border-surface-border text-navy-800 rounded-lg text-xs font-medium shadow-xs transition-colors"
        >
          <Download size={13} className="text-navy-600" />
          <span>Export Sales CSV</span>
        </button>
      </div>

      {/* Top Sales KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Gross Sales Revenue"
          value={formatCurrency(metrics?.total_revenue)}
          subtext="Net of return adjustments"
          icon={DollarSign}
        />
        <MetricCard
          title="Total Eligible Orders"
          value={formatNumber(metrics?.eligible_orders)}
          subtext="Excluding 2 cancelled/returned orders"
          icon={ShoppingBag}
        />
        <MetricCard
          title="Average Order Value (AOV)"
          value={formatCurrency(metrics?.average_order_value)}
          subtext="Per completed order"
          icon={TrendingUp}
        />
      </div>

      {/* Monthly Sales Trend Chart */}
      {monthlyChart && (
        <Card
          title="Sales Revenue Trajectory"
          subtitle="Monthly historical performance tracking"
          action={
            <div className="flex bg-surface-muted p-0.5 rounded-lg border border-surface-border text-xs">
              <button
                onClick={() => setChartType("line")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  chartType === "line"
                    ? "bg-surface text-navy-900 shadow-xs"
                    : "text-navy-600 hover:text-navy-900"
                }`}
              >
                Line
              </button>
              <button
                onClick={() => setChartType("area")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  chartType === "area"
                    ? "bg-surface text-navy-900 shadow-xs"
                    : "text-navy-600 hover:text-navy-900"
                }`}
              >
                Area
              </button>
            </div>
          }
        >
          <DynamicChart spec={monthlyChart} height={320} />
        </Card>
      )}

      {/* Category Performance Bar Chart */}
      {catChart && (
        <Card
          title="Category Revenue Breakdown"
          subtitle="Revenue generated per merchandise department"
        >
          <DynamicChart spec={catChart} height={280} />
        </Card>
      )}
    </div>
  );
};

export default SalesPage;
