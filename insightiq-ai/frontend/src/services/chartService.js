/**
 * Dynamic Chart Generation and Validation API Service
 */

import api from "./apiClient";

export const chartService = {
  getMonthlyRevenueChart: (params = {}) =>
    api.get("charts/monthly-revenue", params),

  getCategoryRevenueChart: (params = {}) =>
    api.get("charts/category-revenue", params),

  getTopProductsChart: (params = {}) =>
    api.get("charts/top-products", params),

  getSalesTrendChart: (params = {}) =>
    api.get("charts/sales-trend", params),

  generateChart: (payload) => api.post("charts/generate", payload),

  validateChart: (chartSpec) => api.post("charts/validate", chartSpec),
};

export default chartService;
