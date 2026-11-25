import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DynamicChart } from "../DynamicChart";

describe("DynamicChart Component (Recharts Visualization)", () => {
  const lineSpec = {
    chart_type: "line",
    title: "Monthly Revenue",
    x_key: "month",
    y_key: "revenue",
    description: "Earned revenue over time",
    data: [
      { month: "2024-01", revenue: 880.0 },
      { month: "2024-02", revenue: 1210.0 },
      { month: "2024-03", revenue: 60.0 },
    ],
    metadata: { unit: "$" },
  };

  const barSpec = {
    chart_type: "bar",
    title: "Top 5 Products by Revenue",
    x_key: "product_name",
    y_key: "revenue",
    description: "Catalog ranking by gross sales",
    data: [
      { product_name: "Laptop", revenue: 999.99 },
      { product_name: "Headphones", revenue: 199.99 },
      { product_name: "Mouse", revenue: 49.99 },
    ],
    metadata: { unit: "$" },
  };

  const pieSpec = {
    chart_type: "pie",
    title: "Revenue by Category",
    x_key: "category",
    y_key: "revenue",
    description: "Category revenue distribution",
    data: [
      { category: "Electronics", revenue: 1050.0 },
      { category: "Clothing", revenue: 650.0 },
      { category: "Home", revenue: 450.0 },
    ],
    metadata: { unit: "$" },
  };

  const areaSpec = {
    chart_type: "area",
    title: "Sales Trajectory",
    x_key: "month",
    y_key: "revenue",
    data: [
      { month: "2024-01", revenue: 880.0 },
      { month: "2024-02", revenue: 1210.0 },
    ],
  };

  it("renders line chart with title, description, and badge", () => {
    render(<DynamicChart spec={lineSpec} />);
    expect(screen.getByTestId("chart-title")).toHaveTextContent("Monthly Revenue");
    expect(screen.getByTestId("chart-description")).toHaveTextContent("Earned revenue over time");
    expect(screen.getByText("line")).toBeInTheDocument();
    expect(screen.getByTestId("dynamic-chart-container")).toBeInTheDocument();
  });

  it("renders bar chart with correct title and badge", () => {
    render(<DynamicChart spec={barSpec} />);
    expect(screen.getByTestId("chart-title")).toHaveTextContent("Top 5 Products by Revenue");
    expect(screen.getByText("bar")).toBeInTheDocument();
    expect(screen.getByTestId("dynamic-chart-container")).toBeInTheDocument();
  });

  it("renders pie chart with correct title and badge", () => {
    render(<DynamicChart spec={pieSpec} />);
    expect(screen.getByTestId("chart-title")).toHaveTextContent("Revenue by Category");
    expect(screen.getByText("pie")).toBeInTheDocument();
    expect(screen.getByTestId("dynamic-chart-container")).toBeInTheDocument();
  });

  it("renders area chart with correct badge", () => {
    render(<DynamicChart spec={areaSpec} />);
    expect(screen.getByTestId("chart-title")).toHaveTextContent("Sales Trajectory");
    expect(screen.getByText("area")).toBeInTheDocument();
    expect(screen.getByTestId("dynamic-chart-container")).toBeInTheDocument();
  });

  it("renders graceful empty state when data is empty", () => {
    const emptySpec = {
      ...lineSpec,
      data: [],
    };
    render(<DynamicChart spec={emptySpec} />);
    expect(screen.getByTestId("chart-empty-data")).toBeInTheDocument();
    expect(
      screen.getByText("No data available for the specified timeframe or query.")
    ).toBeInTheDocument();
  });

  it("gracefully displays error on unsupported chart type", () => {
    const unsupportedSpec = {
      chart_type: "scatter",
      title: "Scatter Plot",
      x_key: "x",
      y_key: "y",
      data: [{ x: 1, y: 2 }],
    };
    render(<DynamicChart spec={unsupportedSpec} />);
    expect(screen.getByTestId("chart-unsupported-error")).toBeInTheDocument();
    expect(screen.getByText("Unsupported Chart Visualization")).toBeInTheDocument();
    expect(
      screen.getByText(/Visualization format “scatter” is not supported/i)
    ).toBeInTheDocument();
  });

  it("gracefully renders placeholder when spec is missing", () => {
    render(<DynamicChart spec={null} />);
    expect(screen.getByTestId("chart-empty-state")).toBeInTheDocument();
    expect(screen.getByText("No chart specification provided.")).toBeInTheDocument();
  });

  it("gracefully displays error when x_key or y_key is missing", () => {
    const badKeysSpec = {
      chart_type: "bar",
      title: "Missing Keys",
      data: [{ a: 1, b: 2 }],
    };
    render(<DynamicChart spec={badKeysSpec} />);
    expect(screen.getByTestId("chart-missing-keys-error")).toBeInTheDocument();
    expect(screen.getByText("Invalid Chart Specification")).toBeInTheDocument();
  });
});
