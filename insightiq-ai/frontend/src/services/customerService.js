/**
 * Customer Cohort Analytics API Service
 */

import api from "./apiClient";

export const customerService = {
  getCustomerMetrics: (params = {}) => api.get("customers/metrics", params),

  getTopCustomers: (params = {}) => api.get("customers/top", params),

  getCustomerOrderFrequency: (params = {}) =>
    api.get("customers/frequency", params),
};

export default customerService;
