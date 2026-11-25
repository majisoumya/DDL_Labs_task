/**
 * Sales and Core Analytics API Service
 */

import api from "./apiClient";

export const analyticsService = {
  getDashboardSummary: (params = {}) => api.get("dashboard/summary", params),

  getSalesMetrics: (params = {}) => api.get("sales/metrics", params),

  getMonthlyRevenue: (params = {}) => api.get("sales/monthly", params),

  getCategoryRevenue: (params = {}) => api.get("sales/categories", params),

  getRevenueByProduct: (params = {}) => api.get("sales/products", params),

  getSalesGrowth: (params = {}) => api.get("sales/growth", params),
};

export default analyticsService;
