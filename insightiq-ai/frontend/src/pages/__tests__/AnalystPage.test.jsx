import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AnalystPage } from "../AnalystPage";
import { analystService } from "../../services";

describe("AnalystPage Integration View", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders analyst studio interface with starter questions and welcome state", async () => {
    vi.spyOn(analystService, "getSuggestions").mockResolvedValue([
      "What is our total revenue?",
      "Show monthly revenue.",
      "Why did revenue decline last month?",
    ]);

    render(
      <BrowserRouter>
        <AnalystPage />
      </BrowserRouter>
    );

    expect(screen.getByTestId("analyst-studio-container")).toBeInTheDocument();
    expect(
      screen.getByText("InsightIQ AI Business Analyst")
    ).toBeInTheDocument();
    expect(screen.getByTestId("chat-welcome-state")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("What is our total revenue?")).toBeInTheDocument();
    });
  });

  it("submits inquiry, renders user query and verified assistant response", async () => {
    vi.spyOn(analystService, "getSuggestions").mockResolvedValue([
      "What is our total revenue?",
    ]);

    const mockResponse = {
      question: "What is our total revenue?",
      summary: "Total revenue reached $2,490.00 across 5 qualifying orders.",
      insights: [
        {
          title: "Sales Health",
          finding: "Consistent order velocity with AOV of $498.00.",
          severity: "positive",
          actionable_recommendation: "Focus on repeat customer retention.",
        },
      ],
      metrics_referenced: [
        {
          metric_name: "Total Revenue",
          exact_value: 2490.0,
          source: "orders",
        },
      ],
      chart_spec: null,
      tool_executions: [
        {
          tool_name: "get_sales_metrics",
          arguments: {},
          success: true,
          error: null,
          execution_time_ms: 10.5,
        },
      ],
      suggested_follow_ups: ["Show monthly revenue."],
      data_limitations_noted: "Cancelled orders are excluded.",
      needs_clarification: false,
    };

    vi.spyOn(analystService, "askQuestion").mockResolvedValue(mockResponse);

    render(
      <BrowserRouter>
        <AnalystPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText(/Ask a business question/i);
    fireEvent.change(input, { target: { value: "What is our total revenue?" } });

    const submitBtn = screen.getByRole("button", { name: /Send inquiry/i });
    fireEvent.click(submitBtn);

    // Verify user message appears
    expect(screen.getByTestId("chat-message-user")).toBeInTheDocument();

    // Verify assistant response appears
    await waitFor(() => {
      expect(screen.getByTestId("chat-message-assistant")).toBeInTheDocument();
      expect(
        screen.getByText("Total revenue reached $2,490.00 across 5 qualifying orders.")
      ).toBeInTheDocument();
      expect(screen.getByText("$2,490.00")).toBeInTheDocument();
      expect(screen.getByText("1 Analytics Tool Executed")).toBeInTheDocument();
      expect(screen.getByText("Show monthly revenue.")).toBeInTheDocument();
    });

    expect(analystService.askQuestion).toHaveBeenCalledWith(
      "What is our total revenue?",
      []
    );
  });

  it("handles clicking suggested question and clears conversation", async () => {
    vi.spyOn(analystService, "getSuggestions").mockResolvedValue([
      "Show monthly revenue.",
    ]);

    const mockResponse = {
      question: "Show monthly revenue.",
      summary: "Monthly revenue trend retrieved across 3 periods.",
      insights: [],
      metrics_referenced: [],
      chart_spec: null,
      tool_executions: [],
      suggested_follow_ups: [],
      data_limitations_noted: null,
      needs_clarification: false,
    };

    vi.spyOn(analystService, "askQuestion").mockResolvedValue(mockResponse);

    render(
      <BrowserRouter>
        <AnalystPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Show monthly revenue.")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Show monthly revenue."));

    await waitFor(() => {
      expect(
        screen.getByText("Monthly revenue trend retrieved across 3 periods.")
      ).toBeInTheDocument();
    });

    // Clear conversation
    const clearBtn = screen.getByRole("button", { name: /Clear conversation/i });
    expect(clearBtn).toBeInTheDocument();
    fireEvent.click(clearBtn);

    // Welcome state restored
    expect(screen.getByTestId("chat-welcome-state")).toBeInTheDocument();
    expect(
      screen.queryByText("Monthly revenue trend retrieved across 3 periods.")
    ).not.toBeInTheDocument();
  });

  it("displays error state when question query fails", async () => {
    vi.spyOn(analystService, "getSuggestions").mockResolvedValue([]);
    vi.spyOn(analystService, "askQuestion").mockRejectedValue(
      new Error("FastAPI connection timeout.")
    );

    render(
      <BrowserRouter>
        <AnalystPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText(/Ask a business question/i);
    fireEvent.change(input, { target: { value: "Test error" } });

    const submitBtn = screen.getByRole("button", { name: /Send inquiry/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Analyst Service Disruption")).toBeInTheDocument();
      expect(screen.getByText("FastAPI connection timeout.")).toBeInTheDocument();
    });
  });
});
