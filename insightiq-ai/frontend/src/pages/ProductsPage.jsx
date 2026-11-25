import React, { useState } from "react";
import { Package, Award, AlertCircle } from "lucide-react";
import {
  MetricCard,
  Card,
  CardSkeleton,
  TableSkeleton,
  ErrorState,
  Badge,
} from "../components/common";
import { DateRangeFilter } from "../components/dashboard";
import { DynamicChart } from "../components/charts/DynamicChart";
import { useAsync } from "../hooks/useAsync";
import { productService, chartService, exportService } from "../services";
import { formatCurrency, formatNumber } from "../utils/formatters";

export const ProductsPage = () => {
  const [sortBy, setSortBy] = useState("revenue");
  const [dateRange, setDateRange] = useState({ startDate: "", endDate: "" });

  const {
    data: productData,
    loading,
    error,
    retry,
  } = useAsync(async () => {
    const params = {
      start_date: dateRange.startDate || undefined,
      end_date: dateRange.endDate || undefined,
    };
    const [topProducts, lowPerforming, chartSpec] = await Promise.all([
      productService.getTopProducts({ limit: 10, sort_by: sortBy, ...params }),
      productService.getLowPerformingProducts({ limit: 10, threshold_revenue: 500.0, ...params }),
      chartService.getTopProductsChart({ limit: 5, sort_by: sortBy, ...params }),
    ]);
    return { topProducts, lowPerforming, chartSpec };
  }, [sortBy, dateRange.startDate, dateRange.endDate]);

  if (loading) {
    return (
      <div data-testid="products-loading" className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <TableSkeleton rows={6} cols={5} />
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="products-error" className="py-8">
        <ErrorState
          title="Could not load product analytics"
          message={error}
          onRetry={retry}
        />
      </div>
    );
  }

  const { topProducts = [], lowPerforming = [], chartSpec } = productData || {};

  return (
    <div data-testid="products-page" className="space-y-6">
      {/* Date Range Controls & Presets */}
      <DateRangeFilter
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        onChange={setDateRange}
        onRefresh={retry}
        onExport={() =>
          exportService.downloadProductsCsv({
            start_date: dateRange.startDate || undefined,
            end_date: dateRange.endDate || undefined,
          })
        }
      />
      {/* Top Product Chart */}
      {chartSpec && (
        <Card
          title="Catalog Performance Ranking"
          subtitle={`Top 5 products ranked by ${sortBy === "revenue" ? "earned revenue" : "units sold"}`}
          action={
            <div className="flex bg-surface-muted p-0.5 rounded-lg border border-surface-border text-xs">
              <button
                onClick={() => setSortBy("revenue")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  sortBy === "revenue"
                    ? "bg-surface text-navy-900 shadow-xs"
                    : "text-navy-600 hover:text-navy-900"
                }`}
              >
                By Revenue
              </button>
              <button
                onClick={() => setSortBy("units")}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  sortBy === "units"
                    ? "bg-surface text-navy-900 shadow-xs"
                    : "text-navy-600 hover:text-navy-900"
                }`}
              >
                By Volume
              </button>
            </div>
          }
        >
          <DynamicChart spec={chartSpec} height={280} />
        </Card>
      )}

      {/* Catalog Leaderboard Table */}
      <Card
        title="Top Selling Inventory"
        subtitle="Ranked SKU performance and current warehouse stock"
      >
        <div className="overflow-x-auto -mx-5 -my-5">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface-subtle text-navy-600 font-semibold uppercase tracking-wider border-b border-surface-border">
              <tr>
                <th className="px-5 py-3">Rank</th>
                <th className="px-3 py-3">Product Name</th>
                <th className="px-3 py-3">Category</th>
                <th className="px-3 py-3 text-right">Units Sold</th>
                <th className="px-3 py-3 text-right">Stock</th>
                <th className="px-5 py-3 text-right">Gross Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {topProducts.map((p, idx) => (
                <tr key={p.product_id || idx} className="hover:bg-surface-subtle/60 transition-colors">
                  <td className="px-5 py-3 font-bold text-navy-600">#{idx + 1}</td>
                  <td className="px-3 py-3 font-medium text-navy-900">{p.product_name}</td>
                  <td className="px-3 py-3 text-navy-600">{p.category}</td>
                  <td className="px-3 py-3 text-right font-mono text-navy-700">
                    {formatNumber(p.units_sold)}
                  </td>
                  <td className="px-3 py-3 text-right font-mono text-navy-600">
                    {formatNumber(p.stock)}
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

      {/* Underperforming SKUs */}
      {lowPerforming.length > 0 && (
        <Card
          title="Underperforming SKUs / Zero Sales"
          subtitle="Products below the $500 threshold requiring inventory review"
        >
          <div className="overflow-x-auto -mx-5 -my-5">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-subtle text-navy-600 font-semibold uppercase tracking-wider border-b border-surface-border">
                <tr>
                  <th className="px-5 py-3">Product Name</th>
                  <th className="px-3 py-3">Category</th>
                  <th className="px-3 py-3 text-right">Units Sold</th>
                  <th className="px-3 py-3 text-right">Stock</th>
                  <th className="px-5 py-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {lowPerforming.map((p, idx) => (
                  <tr key={p.product_id || idx} className="hover:bg-surface-subtle/60 transition-colors">
                    <td className="px-5 py-3 font-medium text-navy-900">{p.product_name}</td>
                    <td className="px-3 py-3 text-navy-600">{p.category}</td>
                    <td className="px-3 py-3 text-right font-mono text-navy-700">
                      {formatNumber(p.units_sold)}
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-navy-600">
                      {formatNumber(p.stock)}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Badge variant="warning">
                        {p.units_sold === 0 ? "Zero Sales" : "Below $500"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ProductsPage;
