import React, { useState } from "react";
import { DynamicChart } from "../charts/DynamicChart";
import { ChartSkeleton, Card } from "../common";

export const DashboardCharts = ({
  monthlyRevenueChart,
  categoryRevenueChart,
  topProductsChart,
  salesTrendChart,
  loading = false,
  className = "",
}) => {
  const [revenueChartType, setRevenueChartType] = useState("area");

  if (loading) {
    return (
      <div data-testid="dashboard-charts-skeleton" className={`space-y-6 ${className}`}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ChartSkeleton height={300} />
          </div>
          <div className="lg:col-span-1">
            <ChartSkeleton height={300} />
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton height={300} />
          <ChartSkeleton height={300} />
        </div>
      </div>
    );
  }

  // Allow toggling between Area and Line for monthly revenue
  const activeMonthlySpec = monthlyRevenueChart
    ? { ...monthlyRevenueChart, chart_type: revenueChartType }
    : null;

  return (
    <div data-testid="dashboard-charts-grid" className={`space-y-6 ${className}`}>
      {/* Upper Row: Monthly Trajectory (2 Cols) & Category Breakdown (1 Col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 1. Monthly Revenue Trajectory */}
        <div className="lg:col-span-2">
          {activeMonthlySpec ? (
            <Card
              title="Monthly Revenue Trajectory"
              subtitle="Earned gross revenue progression (excluding returns/cancellations)"
              action={
                <div className="flex bg-surface-muted p-0.5 rounded-lg border border-surface-border text-xs">
                  <button
                    onClick={() => setRevenueChartType("area")}
                    className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                      revenueChartType === "area"
                        ? "bg-surface text-navy-900 shadow-xs"
                        : "text-navy-600 hover:text-navy-900"
                    }`}
                  >
                    Area
                  </button>
                  <button
                    onClick={() => setRevenueChartType("line")}
                    className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                      revenueChartType === "line"
                        ? "bg-surface text-navy-900 shadow-xs"
                        : "text-navy-600 hover:text-navy-900"
                    }`}
                  >
                    Line
                  </button>
                </div>
              }
            >
              <DynamicChart spec={activeMonthlySpec} height={300} showTitle={false} borderless={true} />
            </Card>
          ) : (
            <ChartSkeleton height={300} />
          )}
        </div>

        {/* 2. Revenue by Category (Pie / Donut) */}
        <div className="lg:col-span-1">
          {categoryRevenueChart ? (
            <Card
              title="Revenue by Category"
              subtitle="Contribution share across merchandise departments"
            >
              <DynamicChart spec={categoryRevenueChart} height={300} showTitle={false} borderless={true} />
            </Card>
          ) : (
            <ChartSkeleton height={300} />
          )}
        </div>
      </div>

      {/* Lower Row: Top Products (1 Col) & Customer / Sales Trend (1 Col) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 3. Top Products by Revenue */}
        <div>
          {topProductsChart ? (
            <Card
              title="Top Products by Revenue"
              subtitle="Catalog leaders ranked by cumulative gross dollars"
            >
              <DynamicChart spec={topProductsChart} height={300} showTitle={false} borderless={true} />
            </Card>
          ) : (
            <ChartSkeleton height={300} />
          )}
        </div>

        {/* 4. Customer / Sales Activity Trend */}
        <div>
          {salesTrendChart ? (
            <Card
              title="Customer Orders & Sales Volume Trend"
              subtitle="Monthly customer order volume and unit throughput"
            >
              <DynamicChart spec={salesTrendChart} height={300} showTitle={false} borderless={true} />
            </Card>
          ) : (
            <ChartSkeleton height={300} />
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardCharts;
