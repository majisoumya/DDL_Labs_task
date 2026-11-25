import apiClient from "./apiClient";

export const systemService = {
  /**
   * Retrieves dataset quality and governance summary.
   * @returns {Promise<Object>}
   */
  getQualitySummary: async () => {
    return apiClient.get("/system/quality-summary");
  },
};

export default systemService;
