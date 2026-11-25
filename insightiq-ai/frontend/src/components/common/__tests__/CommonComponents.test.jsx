import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  Card,
  MetricCard,
  Skeleton,
  CardSkeleton,
  ChartSkeleton,
  TableSkeleton,
  EmptyState,
  ErrorState,
  Badge,
} from "../index";

describe("UI Primitive Components", () => {
  it("renders Card with title, subtitle, and action", () => {
    render(
      <Card
        title="Sales Card"
        subtitle="Monthly performance"
        action={<button>Action Btn</button>}
      >
        <p>Card Body Content</p>
      </Card>
    );

    expect(screen.getByText("Sales Card")).toBeInTheDocument();
    expect(screen.getByText("Monthly performance")).toBeInTheDocument();
    expect(screen.getByText("Action Btn")).toBeInTheDocument();
    expect(screen.getByText("Card Body Content")).toBeInTheDocument();
    expect(screen.getByTestId("ui-card")).toBeInTheDocument();
  });

  it("renders MetricCard with positive trend badge and formatted value", () => {
    render(
      <MetricCard
        title="Total Revenue"
        value="$2,490.00"
        change={12.5}
        changeLabel="vs last month"
        trend="positive"
      />
    );

    expect(screen.getByText("Total Revenue")).toBeInTheDocument();
    expect(screen.getByText("$2,490.00")).toBeInTheDocument();
    expect(screen.getByText("12.5%")).toBeInTheDocument();
    expect(screen.getByText("vs last month")).toBeInTheDocument();
  });

  it("renders MetricCard with negative trend", () => {
    render(
      <MetricCard
        title="Orders"
        value="120"
        change={-8.4}
        changeLabel="MoM drop"
        trend="negative"
      />
    );

    expect(screen.getByText("Orders")).toBeInTheDocument();
    expect(screen.getByText("8.4%")).toBeInTheDocument();
    expect(screen.getByText("MoM drop")).toBeInTheDocument();
  });

  it("renders Loading Skeletons correctly", () => {
    const { unmount } = render(<Skeleton className="h-6 w-24" />);
    expect(screen.getByTestId("ui-skeleton")).toBeInTheDocument();
    unmount();

    render(<CardSkeleton />);
    expect(screen.getByTestId("ui-card-skeleton")).toBeInTheDocument();

    render(<ChartSkeleton height={200} />);
    expect(screen.getByTestId("ui-chart-skeleton")).toBeInTheDocument();

    render(<TableSkeleton rows={3} cols={2} />);
    expect(screen.getByTestId("ui-table-skeleton")).toBeInTheDocument();
  });

  it("renders EmptyState with custom title, description, and action button", () => {
    render(
      <EmptyState
        title="No Products Found"
        description="Try searching with a different SKU name."
        action={<button>Reset Filters</button>}
      />
    );

    expect(screen.getByText("No Products Found")).toBeInTheDocument();
    expect(screen.getByText("Try searching with a different SKU name.")).toBeInTheDocument();
    expect(screen.getByText("Reset Filters")).toBeInTheDocument();
  });

  it("renders ErrorState and triggers retry callback on click", () => {
    const onRetryMock = vi.fn();
    render(
      <ErrorState
        title="Database Timeout"
        message="Unable to reach PostgreSQL pool."
        onRetry={onRetryMock}
      />
    );

    expect(screen.getByText("Database Timeout")).toBeInTheDocument();
    expect(screen.getByText("Unable to reach PostgreSQL pool.")).toBeInTheDocument();

    const retryBtn = screen.getByText("Retry Request");
    fireEvent.click(retryBtn);
    expect(onRetryMock).toHaveBeenCalledTimes(1);
  });

  it("renders Badge variants correctly", () => {
    render(<Badge variant="brand">Active</Badge>);
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByTestId("ui-badge")).toHaveClass("bg-brand-50");
  });
});
