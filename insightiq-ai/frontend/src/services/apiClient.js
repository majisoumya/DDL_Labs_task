/**
 * Resilient API Client with Timeout and Error Handling
 */

import { API_BASE_URL, APP_CONFIG } from "../utils/config";

export class ApiError extends Error {
  constructor(message, status = 500, data = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

const buildUrl = (endpoint, params = {}) => {
  // Strip trailing slash from base and leading slash from endpoint
  const cleanBase = API_BASE_URL.replace(/\/+$/, "");
  const cleanEndpoint = endpoint.replace(/^\/+/, "");
  const fullUrl = `${cleanBase}/${cleanEndpoint}`;

  // Filter out null or undefined query parameters
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== null && val !== undefined && val !== "") {
      searchParams.append(key, String(val));
      // Automatically alias camelCase date parameters to snake_case for seamless backend compatibility
      if (key === "startDate" && !params.start_date) {
        searchParams.append("start_date", String(val));
      }
      if (key === "endDate" && !params.end_date) {
        searchParams.append("end_date", String(val));
      }
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `${fullUrl}?${queryString}` : fullUrl;
};

export const request = async (endpoint, options = {}) => {
  const {
    method = "GET",
    params = {},
    body = null,
    headers = {},
    timeoutMs = APP_CONFIG.requestTimeoutMs,
  } = options;

  const url = buildUrl(endpoint, params);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const config = {
    method,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...headers,
    },
    signal: controller.signal,
  };

  if (body && method !== "GET") {
    config.body = typeof body === "string" ? body : JSON.stringify(body);
  }

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    const contentType = response.headers.get("content-type");
    let responseData = null;
    if (contentType && contentType.includes("application/json")) {
      responseData = await response.json();
    } else {
      responseData = await response.text();
    }

    if (!response.ok) {
      const errorMsg =
        (responseData && (responseData.detail || responseData.message || responseData.error)) ||
        `HTTP request failed with status ${response.status}`;
      throw new ApiError(errorMsg, response.status, responseData);
    }

    return responseData;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === "AbortError") {
      throw new ApiError(
        `Request to ${endpoint} timed out after ${timeoutMs}ms.`,
        408
      );
    }
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message || "Network request failed.", 500);
  }
};

export const api = {
  get: (endpoint, params = {}, options = {}) =>
    request(endpoint, { method: "GET", params, ...options }),
  post: (endpoint, body = {}, options = {}) =>
    request(endpoint, { method: "POST", body, ...options }),
  put: (endpoint, body = {}, options = {}) =>
    request(endpoint, { method: "PUT", body, ...options }),
  delete: (endpoint, options = {}) =>
    request(endpoint, { method: "DELETE", ...options }),
};

export default api;
