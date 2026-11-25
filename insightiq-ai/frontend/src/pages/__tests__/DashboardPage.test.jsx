import React from "react";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { DashboardPage } from "../DashboardPage";
import * as useDashboardDataModule from "../../hooks/useDashboardData";

describe("DashboardPage Integration View", () => {
  it("renders loading skeletons while fetching data", () => {
    vi.spyOn(useDashboardDataModule, "useDashboardData").mockReturnValue({
      summary: null,
      monthlyRevenueChart: null,
      categoryRevenueChart: null,
      topProductsChart: null,
      salesTrendChart: null,
      loading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    expect(screen.getByTestId("kpi-grid-skeleton")).toBeInTheDocument();
    expect(screen.getByTestId("dashboard-charts-skeleton")).toBeInTheDocument();
  });

  it("renders error state when backend analytics call fails", () => {
    vi.spyOn(useDashboardDataModule, "useDashboardData").mockReturnValue({
      summary: null,
      monthlyRevenueChart: null,
      categoryRevenueChart: null,
      topProductsChart: null,
      salesTrendChart: null,
      loading: false,
      error: "FastAPI server unreachable.",
      refetch: vi.fn(),
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    expect(screen.getByTestId("dashboard-error")).toBeInTheDocument();
    expect(
      screen.getByText("FastAPI server unreachable.")
    ).toBeInTheDocument();
  });

  it("renders real API-derived KPIs, 4 charts, and catalog tables", () => {
    vi.spyOn(useDashboardDataModule, "useDashboardData").mockReturnValue({
      summary: {
        kpis: {
          total_revenue: 2490.0,
          total_orders: 5,
          total_customers: 4,
          repeat_customers: 1,
          average_order_value: 498.0,
        },
        top_products: [
          {
            product_id: 1,
            product_name: "Laptop",
            category: "Electronics",
            units_sold: 2,
            revenue: 2000.0,
          },
        ],
        category_breakdown: [
          {
            category: "Electronics",
            revenue: 2150.0,
            percentage: 86.35,
            order_count: 2,
          },
        ],
      },
      monthlyRevenueChart: {
        chart_type: "area",
        title: "Monthly Revenue Trajectory",
        x_key: "month",
        y_key: "revenue",
        data: [{ month: "2024-01", revenue: 1220.0 }],
      },
      categoryRevenueChart: {
        chart_type: "pie",
        title: "Revenue by Category",
        x_key: "category",
        y_key: "revenue",
        data: [{ category: "Electronics", revenue: 2150.0 }],
      },
      topProductsChart: {
        chart_type: "bar",
        title: "Top Products by Revenue",
        x_key: "product_name",
        y_key: "revenue",
        data: [{ product_name: "Laptop", revenue: 2000.0 }],
      },
      salesTrendChart: {
        chart_type: "bar",
        title: "Customer Orders & Sales Volume Trend",
        x_key: "month",
        y_key: "order_count",
        data: [{ month: "2024-01", order_count: 2 }],
      },
      loading: false,
      error: null,
      lastUpdated: "18:30:00",
      refetch: vi.fn(),
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    // Verify 4 KPIs
    expect(screen.getByText("$2,490.00")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("$498.00")).toBeInTheDocument();

    // Verify all 4 chart sections
    expect(screen.getByText("Monthly Revenue Trajectory")).toBeInTheDocument();
    expect(screen.getByText("Revenue by Category")).toBeInTheDocument();
    expect(screen.getByText("Top Products by Revenue")).toBeInTheDocument();
    expect(
      screen.getByText("Customer Orders & Sales Volume Trend")
    ).toBeInTheDocument();

    // Verify table data
    expect(screen.getByText("Top Performing Products")).toBeInTheDocument();
    expect(screen.getByText("Category Distribution")).toBeInTheDocument();
    expect(screen.getByText("Laptop")).toBeInTheDocument();
    expect(screen.getByText(/86\./)).toBeInTheDocument();
  });
});
