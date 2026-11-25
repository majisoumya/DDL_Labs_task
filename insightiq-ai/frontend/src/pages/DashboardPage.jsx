import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, BarChart3 } from "lucide-react";
import { Card, EmptyState, ErrorState, Badge } from "../components/common";
import {
  DateRangeFilter,
  KpiGrid,
  DashboardCharts,
  AnomalyAlertBanner,
} from "../components/dashboard";
import { useDashboardData } from "../hooks/useDashboardData";
import { insightService, exportService } from "../services";
import { formatCurrency, formatNumber, formatPercentage } from "../utils/formatters";

export const DashboardPage = () => {
  const [dateRange, setDateRange] = useState({ startDate: "", endDate: "" });
  const [anomaliesData, setAnomaliesData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    insightService
      .getAnomalies()
      .then((res) => setAnomaliesData(res))
      .catch(() => {});
  }, []);

  const {
    summary,
    monthlyRevenueChart,
    categoryRevenueChart,
    topProductsChart,
    salesTrendChart,
    loading,
    isRefreshing,
    error,
    lastUpdated,
    refetch,
  } = useDashboardData(dateRange);

  const handleDateChange = (newRange) => {
    setDateRange(newRange);
  };

  const handleExportCsv = () => {
    exportService.downloadSalesCsv({
      start_date: dateRange.startDate || undefined,
      end_date: dateRange.endDate || undefined,
    });
  };

  const kpis = summary?.kpis || {};
  const topProducts = summary?.top_products || [];
  const categoryBreakdown = summary?.category_breakdown || summary?.category_distribution || [];
  const isCompletelyEmpty =
    !loading &&
    !error &&
    kpis.total_revenue === 0 &&
    kpis.total_orders === 0 &&
    topProducts.length === 0;

  return (
    <div data-testid="dashboard-page" className="space-y-6">
      {/* 1. Date Range Toolbar & Refresh Controls */}
      <DateRangeFilter
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        onChange={handleDateChange}
        onRefresh={refetch}
        onExport={handleExportCsv}
        isRefreshing={isRefreshing}
        lastUpdated={lastUpdated}
      />

      {/* Anomaly Alerts Banner */}
      {anomaliesData?.anomalies?.length > 0 && (
        <AnomalyAlertBanner
          anomalies={anomaliesData.anomalies}
          executiveInsights={anomaliesData.executive_insights}
          onInvestigate={() => navigate("/analyst")}
        />
      )}

      {/* 2. Error State */}
      {error && (
        <div data-testid="dashboard-error" className="py-4">
          <ErrorState
            title="Failed to Load Executive Intelligence"
            message={error}
            onRetry={refetch}
          />
        </div>
      )}

      {/* 3. Empty State (e.g. invalid or out-of-range date filter) */}
      {isCompletelyEmpty && (
        <div data-testid="dashboard-empty" className="py-6">
          <EmptyState
            icon={BarChart3}
            title="No Records Found for Timeframe"
            description="There are no completed or pending transactions recorded for the selected date window."
            action={
              <button
                onClick={() => setDateRange({ startDate: "", endDate: "" })}
                className="px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors"
              >
                Reset to All Data
              </button>
            }
          />
        </div>
      )}

      {/* 4. KPI Summary Cards Grid */}
      <KpiGrid kpis={kpis} loading={loading} />

      {/* 5. Four Core Analytics Charts Grid */}
      <DashboardCharts
        monthlyRevenueChart={monthlyRevenueChart}
        categoryRevenueChart={categoryRevenueChart}
        topProductsChart={topProductsChart}
        salesTrendChart={salesTrendChart}
        loading={loading}
      />

      {/* 6. Catalog Leaders & Category Breakdown Summary Tables */}
      {!isCompletelyEmpty && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Products Table */}
          <Card
            title="Top Performing Products"
            subtitle="Catalog leaders ranked by cumulative gross revenue"
            action={
              <Link
                to="/products"
                className="text-xs font-medium text-brand-600 hover:text-brand-700 flex items-center gap-1"
              >
                Catalog View <ArrowRight size={13} />
              </Link>
            }
          >
            <div className="overflow-x-auto -mx-5 -my-5">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-subtle text-navy-600 font-semibold uppercase tracking-wider border-b border-surface-border">
                  <tr>
                    <th className="px-5 py-3">Product Name</th>
                    <th className="px-3 py-3">Category</th>
                    <th className="px-3 py-3 text-right">Units</th>
                    <th className="px-5 py-3 text-right">Revenue</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {topProducts.slice(0, 5).map((p, idx) => (
                    <tr
                      key={p.product_id || idx}
                      className="hover:bg-surface-subtle/60 transition-colors"
                    >
                      <td className="px-5 py-3 font-medium text-navy-900 truncate max-w-[160px]">
                        {p.product_name}
                      </td>
                      <td className="px-3 py-3 text-navy-600">{p.category}</td>
                      <td className="px-3 py-3 text-right font-mono text-navy-700">
                        {formatNumber(p.units_sold)}
                      </td>
                      <td className="px-5 py-3 text-right font-semibold font-mono text-navy-900">
                        {formatCurrency(p.revenue)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Category Contribution Table */}
          <Card
            title="Category Distribution"
            subtitle="Revenue contribution share across merchandise departments"
            action={
              <Link
                to="/sales"
                className="text-xs font-medium text-brand-600 hover:text-brand-700 flex items-center gap-1"
              >
                Sales View <ArrowRight size={13} />
              </Link>
            }
          >
            <div className="overflow-x-auto -mx-5 -my-5">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-subtle text-navy-600 font-semibold uppercase tracking-wider border-b border-surface-border">
                  <tr>
                    <th className="px-5 py-3">Department</th>
                    <th className="px-3 py-3 text-right">Orders</th>
                    <th className="px-3 py-3 text-right">Share</th>
                    <th className="px-5 py-3 text-right">Revenue</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {categoryBreakdown.map((c, idx) => (
                    <tr
                      key={c.category || idx}
                      className="hover:bg-surface-subtle/60 transition-colors"
                    >
                      <td className="px-5 py-3 font-medium text-navy-900">
                        {c.category}
                      </td>
                      <td className="px-3 py-3 text-right font-mono text-navy-700">
                        {formatNumber(c.order_count)}
                      </td>
                      <td className="px-3 py-3 text-right">
                        <Badge variant="brand">{formatPercentage(c.percentage)}</Badge>
                      </td>
                      <td className="px-5 py-3 text-right font-semibold font-mono text-navy-900">
                        {formatCurrency(c.revenue)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
