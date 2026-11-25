import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DateRangeFilter } from "../DateRangeFilter";
import { KpiGrid } from "../KpiGrid";
import { DashboardCharts } from "../DashboardCharts";

describe("Dashboard Components", () => {
  describe("DateRangeFilter", () => {
    it("renders all preset buttons and triggers onChange on click", () => {
      const onChangeMock = vi.fn();
      render(<DateRangeFilter onChange={onChangeMock} />);

      expect(screen.getByText("All Data")).toBeInTheDocument();
      expect(screen.getByText("FY 2024")).toBeInTheDocument();
      expect(screen.getByText("Q1 2024")).toBeInTheDocument();
      expect(screen.getByText("Q2 2024")).toBeInTheDocument();

      fireEvent.click(screen.getByText("FY 2024"));
      expect(onChangeMock).toHaveBeenCalledWith({
        startDate: "2024-01-01",
        endDate: "2024-06-30",
      });

      fireEvent.click(screen.getByText("Q1 2024"));
      expect(onChangeMock).toHaveBeenCalledWith({
        startDate: "2024-01-01",
        endDate: "2024-03-31",
      });
    });

    it("triggers onRefresh when refresh button is clicked", () => {
      const onRefreshMock = vi.fn();
      render(<DateRangeFilter onChange={vi.fn()} onRefresh={onRefreshMock} />);

      const refreshBtn = screen.getByLabelText("Refresh analytics data");
      fireEvent.click(refreshBtn);
      expect(onRefreshMock).toHaveBeenCalledTimes(1);
    });

    it("displays syncing state when isRefreshing is true", () => {
      render(
        <DateRangeFilter
          onChange={vi.fn()}
          onRefresh={vi.fn()}
          isRefreshing={true}
        />
      );

      expect(screen.getByText("Syncing...")).toBeInTheDocument();
    });
  });

  describe("KpiGrid", () => {
    it("renders skeleton placeholders when loading is true", () => {
      render(<KpiGrid loading={true} />);
      expect(screen.getByTestId("kpi-grid-skeleton")).toBeInTheDocument();
    });

    it("displays formatted revenue, orders, customers, and AOV correctly", () => {
      const kpis = {
        total_revenue: 2490.0,
        total_orders: 5,
        total_customers: 4,
        repeat_customers: 1,
        average_order_value: 498.0,
      };

      render(<KpiGrid kpis={kpis} loading={false} />);

      expect(screen.getByText("Total Revenue")).toBeInTheDocument();
      expect(screen.getByText("$2,490.00")).toBeInTheDocument();

      expect(screen.getByText("Total Orders")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();

      expect(screen.getByText("Total Customers")).toBeInTheDocument();
      expect(screen.getByText("4")).toBeInTheDocument();
      expect(screen.getByText("1 repeat buyers")).toBeInTheDocument();

      expect(screen.getByText("Average Order Value")).toBeInTheDocument();
      expect(screen.getByText("$498.00")).toBeInTheDocument();
    });
  });

  describe("DashboardCharts", () => {
    const mockMonthlySpec = {
      chart_type: "area",
      title: "Monthly Revenue Trajectory",
      x_key: "month",
      y_key: "revenue",
      data: [
        { month: "2024-01", revenue: 1220.0 },
        { month: "2024-02", revenue: 1210.0 },
        { month: "2024-03", revenue: 60.0 },
      ],
      metadata: { unit: "$" },
    };

    const mockCategorySpec = {
      chart_type: "pie",
      title: "Revenue by Category",
      x_key: "category",
      y_key: "revenue",
      data: [
        { category: "Electronics", revenue: 2150.0 },
        { category: "Apparel", revenue: 340.0 },
      ],
      metadata: { unit: "$" },
    };

    const mockTopProductsSpec = {
      chart_type: "bar",
      title: "Top Products by Revenue",
      x_key: "product_name",
      y_key: "revenue",
      data: [
        { product_name: "Laptop", revenue: 2000.0 },
        { product_name: "Hoodie", revenue: 240.0 },
      ],
      metadata: { unit: "$" },
    };

    const mockSalesTrendSpec = {
      chart_type: "bar",
      title: "Customer Orders & Sales Volume Trend",
      x_key: "month",
      y_key: "order_count",
      y_keys: ["order_count", "units_sold"],
      data: [
        { month: "2024-01", order_count: 2, units_sold: 5 },
        { month: "2024-02", order_count: 2, units_sold: 4 },
      ],
      metadata: { unit: "orders" },
    };

    it("renders loading skeletons when loading is true", () => {
      render(<DashboardCharts loading={true} />);
      expect(screen.getByTestId("dashboard-charts-skeleton")).toBeInTheDocument();
    });

    it("renders all 4 charts when data is provided", () => {
      render(
        <DashboardCharts
          monthlyRevenueChart={mockMonthlySpec}
          categoryRevenueChart={mockCategorySpec}
          topProductsChart={mockTopProductsSpec}
          salesTrendChart={mockSalesTrendSpec}
          loading={false}
        />
      );

      // Verify all 4 chart headings are present in the DOM
      expect(screen.getByText("Monthly Revenue Trajectory")).toBeInTheDocument();
      expect(screen.getByText("Revenue by Category")).toBeInTheDocument();
      expect(screen.getByText("Top Products by Revenue")).toBeInTheDocument();
      expect(
        screen.getByText("Customer Orders & Sales Volume Trend")
      ).toBeInTheDocument();
    });

    it("toggles monthly revenue chart between area and line format", () => {
      render(
        <DashboardCharts
          monthlyRevenueChart={mockMonthlySpec}
          categoryRevenueChart={mockCategorySpec}
          topProductsChart={mockTopProductsSpec}
          salesTrendChart={mockSalesTrendSpec}
          loading={false}
        />
      );

      const lineToggleBtn = screen.getByText("Line");
      fireEvent.click(lineToggleBtn);
      expect(lineToggleBtn).toHaveClass("bg-surface");
    });
  });
});
