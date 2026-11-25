import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { DashboardPage } from "../DashboardPage";
import { AnalystPage } from "../AnalystPage";
import { DynamicChart } from "../../components/charts/DynamicChart";
import * as useDashboardDataModule from "../../hooks/useDashboardData";
import { analystService, insightService } from "../../services";

describe("Frontend Resilience, Error States, and Edge Case Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // ---------------------------------------------------------------------------
  // 1. Dashboard API Failure & Error Recovery
  // ---------------------------------------------------------------------------
  it("renders ErrorState and supports retry when Dashboard API fails", async () => {
    const mockRefetch = vi.fn();
    vi.spyOn(useDashboardDataModule, "useDashboardData").mockReturnValue({
      summary: null,
      monthlyRevenueChart: null,
      categoryRevenueChart: null,
      topProductsChart: null,
      salesTrendChart: null,
      loading: false,
      error: "Network connection refused.",
      refetch: mockRefetch,
    });
    vi.spyOn(insightService, "getAnomalies").mockResolvedValue({
      anomalies: [],
      executive_insights: [],
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    // Verify Error State renders
    expect(screen.getByTestId("dashboard-error")).toBeInTheDocument();
    expect(screen.getByText(/Failed to Load Executive Intelligence/i)).toBeInTheDocument();
    expect(screen.getByText(/Network connection refused/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry request/i })).toBeInTheDocument();

    // Click retry
    fireEvent.click(screen.getByRole("button", { name: /retry request/i }));
    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  // ---------------------------------------------------------------------------
  // 2. Dashboard Empty Dataset Handling
  // ---------------------------------------------------------------------------
  it("handles zero/empty datasets without crashing and displays EmptyState", async () => {
    vi.spyOn(useDashboardDataModule, "useDashboardData").mockReturnValue({
      summary: {
        kpis: {
          total_revenue: 0,
          total_orders: 0,
          total_customers: 0,
          average_order_value: 0,
        },
        top_products: [],
        category_breakdown: [],
      },
      monthlyRevenueChart: {
        chart_type: "area",
        title: "Monthly Revenue",
        x_key: "month",
        y_key: "revenue",
        data: [],
      },
      categoryRevenueChart: {
        chart_type: "pie",
        title: "Revenue by Category",
        x_key: "category",
        y_key: "revenue",
        data: [],
      },
      topProductsChart: {
        chart_type: "bar",
        title: "Top Products",
        x_key: "product_name",
        y_key: "revenue",
        data: [],
      },
      salesTrendChart: {
        chart_type: "bar",
        title: "Customer & Sales Velocity",
        x_key: "month",
        y_key: "revenue",
        data: [],
      },
      loading: false,
      error: null,
      refetch: vi.fn(),
    });
    vi.spyOn(insightService, "getAnomalies").mockResolvedValue({
      anomalies: [],
      executive_insights: [],
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    // Empty state container should render
    expect(screen.getByTestId("dashboard-empty")).toBeInTheDocument();
    expect(screen.getByText(/No Records Found for Timeframe/i)).toBeInTheDocument();
  });

  // ---------------------------------------------------------------------------
  // 3. AI Analyst Chat API Failure Handling
  // ---------------------------------------------------------------------------
  it("displays prominent error message when Analyst Chat API fails", async () => {
    vi.spyOn(analystService, "getSuggestions").mockResolvedValue([
      "What is our total revenue?",
    ]);
    vi.spyOn(analystService, "getHistory").mockResolvedValue([]);
    vi.spyOn(analystService, "askQuestion").mockRejectedValue(
      new Error("OpenAI API service unavailable (502)")
    );

    render(
      <BrowserRouter>
        <AnalystPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask a business question/i)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Ask a business question/i);
    fireEvent.change(input, { target: { value: "Why did revenue drop?" } });
    fireEvent.click(screen.getByRole("button", { name: /Send inquiry/i }));

    // Verify error banner is displayed
    await waitFor(() => {
      expect(screen.getByText(/Analyst Service Disruption/i)).toBeInTheDocument();
      expect(screen.getByText(/OpenAI API service unavailable \(502\)/i)).toBeInTheDocument();
    });

    // Verify input is re-enabled and usable
    expect(input).not.toBeDisabled();
  });

  // ---------------------------------------------------------------------------
  // 4. DynamicChart Malformed / Edge-Case Specs
  // ---------------------------------------------------------------------------
  it("gracefully renders fallback states for null, unsupported, or empty chart specs", () => {
    // 4.1 Null spec
    const { rerender } = render(<DynamicChart spec={null} />);
    expect(screen.getByTestId("chart-empty-state")).toBeInTheDocument();
    expect(screen.getByText(/No chart specification provided/i)).toBeInTheDocument();

    // 4.2 Unsupported chart type
    rerender(
      <DynamicChart
        spec={{
          chart_type: "scatter_plot_3d",
          title: "Scatter Plot",
          x_key: "x",
          y_key: "y",
          data: [{ x: 1, y: 2 }],
        }}
      />
    );
    expect(screen.getByTestId("chart-unsupported-error")).toBeInTheDocument();
    expect(screen.getByText("Unsupported Chart Visualization")).toBeInTheDocument();
    expect(screen.getByText(/scatter_plot_3d/i)).toBeInTheDocument();

    // 4.3 Empty dataset
    rerender(
      <DynamicChart
        spec={{
          chart_type: "bar",
          title: "Empty Bar Chart",
          x_key: "category",
          y_key: "revenue",
          data: [],
        }}
      />
    );
    expect(screen.getByTestId("chart-empty-data")).toBeInTheDocument();
    expect(screen.getByText(/No data available for the specified timeframe or query/i)).toBeInTheDocument();
  });
});
