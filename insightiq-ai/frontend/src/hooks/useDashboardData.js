import { useState, useEffect, useCallback } from "react";
import analyticsService from "../services/analyticsService";
import chartService from "../services/chartService";

/**
 * Dedicated hook for loading executive dashboard metrics and all 4 dynamic chart specs.
 */
export const useDashboardData = (params = {}) => {
  const [summary, setSummary] = useState(null);
  const [monthlyRevenueChart, setMonthlyRevenueChart] = useState(null);
  const [categoryRevenueChart, setCategoryRevenueChart] = useState(null);
  const [topProductsChart, setTopProductsChart] = useState(null);
  const [salesTrendChart, setSalesTrendChart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = useCallback(
    async (isManualRefresh = false) => {
      if (isManualRefresh) {
        setIsRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const queryParams = {
        ...params,
        start_date: params.start_date || params.startDate || undefined,
        end_date: params.end_date || params.endDate || undefined,
      };

      try {
        const [
          summaryRes,
          monthlyChartRes,
          categoryChartRes,
          topProductsChartRes,
          salesTrendChartRes,
        ] = await Promise.all([
          analyticsService.getDashboardSummary(queryParams),
          chartService.getMonthlyRevenueChart({ ...queryParams, chart_type: "area" }),
          chartService.getCategoryRevenueChart({ ...queryParams, chart_type: "pie" }),
          chartService.getTopProductsChart({ ...queryParams, limit: 5, sort_by: "revenue" }),
          chartService.getSalesTrendChart({ ...queryParams, chart_type: "bar" }),
        ]);

        setSummary(summaryRes);
        setMonthlyRevenueChart(monthlyChartRes);
        setCategoryRevenueChart(categoryChartRes);
        setTopProductsChart(topProductsChartRes);
        setSalesTrendChart(salesTrendChartRes);

        const now = new Date();
        setLastUpdated(now.toLocaleTimeString("en-US", { hour12: false }));
        setLoading(false);
        setIsRefreshing(false);
      } catch (err) {
        setError(err.message || "Failed to fetch dashboard intelligence.");
        setLoading(false);
        setIsRefreshing(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(params)]
  );

  useEffect(() => {
    fetchData(false);
  }, [fetchData]);

  return {
    summary,
    monthlyRevenueChart,
    categoryRevenueChart,
    topProductsChart,
    salesTrendChart,
    loading,
    isRefreshing,
    error,
    lastUpdated,
    refetch: () => fetchData(true),
  };
};

export default useDashboardData;
