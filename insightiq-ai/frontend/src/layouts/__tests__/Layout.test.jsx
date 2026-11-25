import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { Sidebar, Header, AppLayout } from "../index";

describe("Layout Components", () => {
  it("renders Sidebar navigation links and warehouse status", () => {
    render(
      <BrowserRouter>
        <Sidebar isOpen={true} onClose={vi.fn()} />
      </BrowserRouter>
    );

    expect(screen.getByText("InsightIQ")).toBeInTheDocument();
    expect(screen.getByText("Executive Overview")).toBeInTheDocument();
    expect(screen.getByText("Sales Analytics")).toBeInTheDocument();
    expect(screen.getByText("Product Catalog")).toBeInTheDocument();
    expect(screen.getByText("Customer Cohorts")).toBeInTheDocument();
    expect(screen.getByText("AI Analyst Studio")).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL Live")).toBeInTheDocument();
  });

  it("renders Header with title and audited ground truth badge", () => {
    const onOpenSidebarMock = vi.fn();
    render(
      <Header onOpenSidebar={onOpenSidebarMock} title="Sales Performance" />
    );

    expect(screen.getByText("Sales Performance")).toBeInTheDocument();
    expect(screen.getByText("Audited Ground Truth")).toBeInTheDocument();

    const menuBtn = screen.getByLabelText("Open sidebar");
    fireEvent.click(menuBtn);
    expect(onOpenSidebarMock).toHaveBeenCalledTimes(1);
  });

  it("renders AppLayout containing sidebar, header, and main container", () => {
    render(
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    );

    expect(screen.getByTestId("app-layout")).toBeInTheDocument();
    expect(screen.getByTestId("app-sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("app-header")).toBeInTheDocument();
    expect(screen.getByTestId("main-content")).toBeInTheDocument();
  });
});
