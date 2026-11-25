/**
 * Application Runtime Configuration
 * Loads environment variables with sensible SaaS defaults.
 */

export const API_BASE_URL =
  (import.meta.env && import.meta.env.VITE_API_BASE_URL) || "/api";

export const APP_CONFIG = {
  name: "InsightIQ AI",
  version: "1.0.0",
  tagline: "Autonomous Enterprise Intelligence",
  apiBaseUrl: API_BASE_URL,
  defaultCurrency: "USD",
  requestTimeoutMs: 15000,
};

export default APP_CONFIG;
