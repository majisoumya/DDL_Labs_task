import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api, ApiError, request } from "../apiClient";

describe("API Client Service", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("successfully parses and returns JSON responses on 200 OK", async () => {
    const mockData = { total_revenue: 2490.0 };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: {
        get: (h) => (h === "content-type" ? "application/json" : null),
      },
      json: async () => mockData,
    });

    const result = await api.get("sales/metrics", { start_date: "2024-01-01" });
    expect(result).toEqual(mockData);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("sales/metrics?start_date=2024-01-01"),
      expect.objectContaining({ method: "GET" })
    );
  });

  it("throws ApiError with detail message on non-200 responses", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      headers: {
        get: (h) => (h === "content-type" ? "application/json" : null),
      },
      json: async () => ({ detail: "Inverted date range filter." }),
    });

    await expect(api.get("sales/metrics")).rejects.toThrow(ApiError);
    await expect(api.get("sales/metrics")).rejects.toThrow(
      "Inverted date range filter."
    );
  });

  it("serializes POST body correctly", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: {
        get: (h) => (h === "content-type" ? "application/json" : null),
      },
      json: async () => ({ is_valid: true }),
    });

    const bodyPayload = { chart_type: "line", title: "Test" };
    const res = await api.post("charts/validate", bodyPayload);
    expect(res).toEqual({ is_valid: true });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("charts/validate"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(bodyPayload),
      })
    );
  });
});
