import apiClient from "./apiClient";

export const insightService = {
  /**
   * Scans and retrieves revenue and category anomalies.
   * @returns {Promise<Object>}
   */
  getAnomalies: async () => {
    return apiClient.get("/insights/anomalies");
  },
};

export default insightService;
