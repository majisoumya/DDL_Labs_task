import { API_BASE_URL } from "../utils/config";

export const exportService = {
  /**
   * Downloads verified sales performance report as CSV.
   * @param {Object} params - { start_date, end_date }
   */
  downloadSalesCsv: async (params = {}) => {
    const query = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}/export/sales-csv${query ? `?${query}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to export sales CSV");
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = "insightiq_sales_report.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
  },

  /**
   * Downloads product catalog analytics as CSV.
   * @param {number|Object} params - Limit or { limit, start_date, end_date }
   */
  downloadProductsCsv: async (params = 50) => {
    const queryObj = typeof params === "number" ? { limit: params } : { limit: 50, ...params };
    const query = new URLSearchParams(
      Object.fromEntries(Object.entries(queryObj).filter(([_, v]) => v !== undefined && v !== ""))
    ).toString();
    const url = `${API_BASE_URL}/export/products-csv${query ? `?${query}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to export products CSV");
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = "insightiq_products_catalog.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
  },

  /**
   * Downloads customer cohort rankings as CSV.
   * @param {number|Object} params - Limit or { limit, start_date, end_date }
   */
  downloadCustomersCsv: async (params = 50) => {
    const queryObj = typeof params === "number" ? { limit: params } : { limit: 50, ...params };
    const query = new URLSearchParams(
      Object.fromEntries(Object.entries(queryObj).filter(([_, v]) => v !== undefined && v !== ""))
    ).toString();
    const url = `${API_BASE_URL}/export/customers-csv${query ? `?${query}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to export customers CSV");
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = "insightiq_customers_cohort.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
  },
};

export default exportService;
