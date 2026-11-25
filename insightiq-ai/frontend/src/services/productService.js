/**
 * Product Catalog Analytics API Service
 */

import api from "./apiClient";

export const productService = {
  getTopProducts: (params = {}) => api.get("products/top", params),

  getLowPerformingProducts: (params = {}) =>
    api.get("products/low-performing", params),

  getProductDetail: (productId, params = {}) =>
    api.get(`products/${productId}`, params),
};

export default productService;
