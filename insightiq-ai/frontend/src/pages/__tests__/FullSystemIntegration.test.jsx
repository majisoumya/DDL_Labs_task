import React from "react";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DashboardPage } from "../DashboardPage";
import { AnalystPage } from "../AnalystPage";
import { Header } from "../../layouts/Header";
import {
  insightService,
  exportService,
  systemService,
  analystService,
} from "../../services";
import * as useDashboardDataModule from "../../hooks/useDashboardData";

describe("Full System Integration Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // -------------------------------------------------------------
  // 1. Dashboard Anomaly Detection Integration
  // -------------------------------------------------------------
  it("renders revenue anomaly alert banner on Dashboard when detected", async () => {
    vi.spyOn(useDashboardDataModule, "useDashboardData").mockReturnValue({
      summary: {
        kpis: { total_revenue: 2490.0, total_orders: 5, average_order_value: 498.0, active_customers: 4 },
        top_products: [{ product_id: 1, product_name: "Pro Laptop 15", category: "Electronics", total_revenue: 2000.0, units_sold: 2 }],
        category_breakdown: [{ category: "Electronics", revenue: 2150.0, percentage: 86.35 }],
      },
      monthlyRevenueChart: null,
      categoryRevenueChart: null,
      topProductsChart: null,
      salesTrendChart: null,
      loading: false,
      isRefreshing: false,
      error: null,
      lastUpdated: "Just now",
      refetch: vi.fn(),
    });

    vi.spyOn(insightService, "getAnomalies").mockResolvedValue({
      status: "success",
      anomaly_count: 1,
      anomalies: [
        {
          anomaly_type: "revenue_drop",
          metric: "monthly_revenue",
          period: "2024-03",
          value: 60.0,
          comparison_value: 1210.0,
          percentage_change: -95.04,
          z_score: -1.25,
          severity: "high",
          description: "Steep revenue decline of 95.0% in March 2024 compared to previous month.",
          recommendation: "Investigate low order volume and product catalog velocity.",
        },
      ],
      executive_insights: [],
      has_critical_anomalies: true,
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("anomaly-alert-banner")).toBeInTheDocument();
      expect(screen.getByText(/Revenue Anomaly Detected/i)).toBeInTheDocument();
      expect(screen.getByText(/Steep revenue decline of 95.0%/i)).toBeInTheDocument();
      expect(screen.getByText("high Impact")).toBeInTheDocument();
      expect(screen.getByText("Investigate with AI")).toBeInTheDocument();
    });

    // Dismiss banner
    const dismissBtn = screen.getByRole("button", { name: /Dismiss anomaly alert/i });
    fireEvent.click(dismissBtn);
    expect(screen.queryByTestId("anomaly-alert-banner")).not.toBeInTheDocument();
  });

  // -------------------------------------------------------------
  // 2. CSV Export Button on Dashboard
  // -------------------------------------------------------------
  it("triggers sales CSV export from Dashboard toolbar", () => {
    vi.spyOn(useDashboardDataModule, "useDashboardData").mockReturnValue({
      summary: null,
      loading: false,
      isRefreshing: false,
      error: null,
      refetch: vi.fn(),
    });

    vi.spyOn(insightService, "getAnomalies").mockResolvedValue({ anomalies: [] });
    const spyExport = vi.spyOn(exportService, "downloadSalesCsv").mockImplementation(() => {});

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    const exportBtn = screen.getByRole("button", { name: /Export CSV/i });
    expect(exportBtn).toBeInTheDocument();
    fireEvent.click(exportBtn);

    expect(spyExport).toHaveBeenCalledTimes(1);
  });

  // -------------------------------------------------------------
  // 3. Dataset Quality Modal in Header
  // -------------------------------------------------------------
  it("opens dataset quality and governance summary modal from Header", async () => {
    vi.spyOn(systemService, "getQualitySummary").mockResolvedValue({
      status: "healthy",
      database_engine: "postgresql",
      inventory: {
        customers_count: 5,
        products_count: 5,
        orders_total: 8,
        order_items_total: 11,
      },
      order_status_breakdown: {
        completed: 5,
        pending: 1,
        cancelled: 1,
        returned: 1,
      },
      governance_exclusions: {
        excluded_orders_count: 2,
        excluded_revenue_dollars: 1080.0,
        policy_rule: "Cancelled and returned transactions are quarantined.",
      },
      data_integrity: {
        referential_integrity: "valid",
        audit_certification: "100% Ground-Truth Certified",
      },
    });

    render(
      <BrowserRouter>
        <Header title="Overview" />
      </BrowserRouter>
    );

    const triggerBtn = screen.getByTestId("data-quality-trigger");
    expect(triggerBtn).toBeInTheDocument();
    fireEvent.click(triggerBtn);

    // Modal appears
    await waitFor(() => {
      expect(screen.getByTestId("data-quality-modal")).toBeInTheDocument();
      expect(
        screen.getByText("Dataset Quality & Governance Report")
      ).toBeInTheDocument();
      expect(
        screen.getByText("100% Ground-Truth Certified")
      ).toBeInTheDocument();
      expect(screen.getByText("POSTGRESQL LIVE")).toBeInTheDocument();
      expect(screen.getByText("8")).toBeInTheDocument(); // total orders
    });

    // Close modal
    const closeBtn = screen.getByRole("button", { name: /Close Report/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByTestId("data-quality-modal")).not.toBeInTheDocument();
  });

  // -------------------------------------------------------------
  // 4. Analyst Studio Audit History Drawer
  // -------------------------------------------------------------
  it("opens audit history drawer and displays past executions in Analyst Studio", async () => {
    vi.spyOn(analystService, "getSuggestions").mockResolvedValue([]);
    vi.spyOn(analystService, "getHistory").mockResolvedValue([
      {
        id: "rec-123",
        timestamp: "2026-11-25T12:00:00Z",
        question: "What is our total revenue?",
        duration_ms: 14.2,
        tools_count: 1,
        tools_executed: ["get_sales_metrics"],
        has_chart: false,
        success: true,
      },
    ]);

    const spyAsk = vi.spyOn(analystService, "askQuestion").mockResolvedValue({
      question: "What is our total revenue?",
      summary: "Revenue is $2,490.00",
      insights: [],
      metrics_referenced: [],
      tool_executions: [],
    });

    render(
      <BrowserRouter>
        <AnalystPage />
      </BrowserRouter>
    );

    const historyBtn = screen.getByTestId("audit-history-trigger");
    expect(historyBtn).toBeInTheDocument();
    fireEvent.click(historyBtn);

    await waitFor(() => {
      const drawer = screen.getByTestId("execution-history-drawer");
      expect(drawer).toBeInTheDocument();
      expect(within(drawer).getByText("Analytics Audit History")).toBeInTheDocument();
      expect(within(drawer).getByText("What is our total revenue?")).toBeInTheDocument();
      expect(within(drawer).getByText("14.2ms")).toBeInTheDocument();
      expect(within(drawer).getByText("get_sales_metrics")).toBeInTheDocument();
    });

    // Click Re-run button
    const rerunBtn = screen.getByRole("button", { name: /Re-run/i });
    fireEvent.click(rerunBtn);

    // Verify drawer closed and inquiry was submitted
    expect(screen.queryByTestId("execution-history-drawer")).not.toBeInTheDocument();
    expect(spyAsk).toHaveBeenCalledWith("What is our total revenue?", []);
  });
});
