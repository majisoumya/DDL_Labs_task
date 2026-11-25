import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  SuggestedQuestions,
  ChatInput,
  ToolStatusPanel,
  EvidencePanel,
  ChatMessage,
  ChatThread,
} from "../index";

describe("Chat Subcomponents Unit Tests", () => {
  // -------------------------------------------------------------
  // 1. SuggestedQuestions Component
  // -------------------------------------------------------------
  describe("SuggestedQuestions", () => {
    it("renders list of questions and handles selection", () => {
      const handleSelect = vi.fn();
      const questions = [
        "What is our total revenue?",
        "Why did revenue decline last month?",
      ];

      render(
        <SuggestedQuestions questions={questions} onSelect={handleSelect} />
      );

      expect(screen.getByText("Suggested Inquiries")).toBeInTheDocument();
      expect(
        screen.getByText("What is our total revenue?")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Why did revenue decline last month?")
      ).toBeInTheDocument();

      fireEvent.click(screen.getByText("What is our total revenue?"));
      expect(handleSelect).toHaveBeenCalledWith("What is our total revenue?");
    });

    it("returns null when questions list is empty", () => {
      const { container } = render(
        <SuggestedQuestions questions={[]} onSelect={vi.fn()} />
      );
      expect(container.firstChild).toBeNull();
    });
  });

  // -------------------------------------------------------------
  // 2. ChatInput Component
  // -------------------------------------------------------------
  describe("ChatInput", () => {
    it("allows typing and submitting an inquiry", () => {
      const handleSend = vi.fn();
      render(<ChatInput onSend={handleSend} />);

      const input = screen.getByPlaceholderText(/Ask a business question/i);
      fireEvent.change(input, { target: { value: "Show monthly revenue" } });
      expect(input.value).toBe("Show monthly revenue");

      const submitBtn = screen.getByRole("button", { name: /Send inquiry/i });
      fireEvent.click(submitBtn);

      expect(handleSend).toHaveBeenCalledWith("Show monthly revenue");
      expect(input.value).toBe("");
    });

    it("renders clear button when hasMessages is true and calls onClear", () => {
      const handleClear = vi.fn();
      render(
        <ChatInput
          onSend={vi.fn()}
          onClear={handleClear}
          hasMessages={true}
        />
      );

      const clearBtn = screen.getByRole("button", {
        name: /Clear conversation/i,
      });
      expect(clearBtn).toBeInTheDocument();
      fireEvent.click(clearBtn);
      expect(handleClear).toHaveBeenCalledTimes(1);
    });

    it("disables send button when input is empty or loading", () => {
      const { rerender } = render(<ChatInput onSend={vi.fn()} loading={false} />);
      const submitBtn = screen.getByRole("button", { name: /Send inquiry/i });
      expect(submitBtn).toBeDisabled();

      rerender(<ChatInput onSend={vi.fn()} loading={true} />);
      expect(screen.getByRole("button", { name: /Send inquiry/i })).toBeDisabled();
    });
  });

  // -------------------------------------------------------------
  // 3. ToolStatusPanel Component
  // -------------------------------------------------------------
  describe("ToolStatusPanel", () => {
    const sampleTools = [
      {
        tool_name: "get_sales_metrics",
        arguments: { start_date: "2024-01-01" },
        success: true,
        error: null,
        execution_time_ms: 12.4,
      },
      {
        tool_name: "get_monthly_revenue",
        arguments: {},
        success: true,
        error: null,
        execution_time_ms: 8.6,
      },
    ];

    it("renders tool count and execution duration summary", () => {
      render(<ToolStatusPanel toolExecutions={sampleTools} />);

      expect(screen.getByText(/2 Analytics Tools Executed/i)).toBeInTheDocument();
      expect(screen.getByText("21.0ms")).toBeInTheDocument();
    });

    it("expands to show tool audit details when toggled", () => {
      render(<ToolStatusPanel toolExecutions={sampleTools} />);

      expect(screen.queryByText("get_sales_metrics")).not.toBeInTheDocument();

      const toggleBtn = screen.getByText(/Audit Details/i);
      fireEvent.click(toggleBtn);

      expect(screen.getByText("get_sales_metrics")).toBeInTheDocument();
      expect(screen.getByText("get_monthly_revenue")).toBeInTheDocument();
      expect(screen.getByText(/2024-01-01/)).toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------
  // 4. EvidencePanel Component
  // -------------------------------------------------------------
  describe("EvidencePanel", () => {
    it("renders verified ground-truth metrics, structured insights, and governance notes", () => {
      const metrics = [
        {
          metric_name: "Total Revenue",
          exact_value: 2490.0,
          source: "orders",
        },
        {
          metric_name: "Total Orders",
          exact_value: 5,
          source: "orders",
        },
      ];

      const insights = [
        {
          title: "Strong Electronics Contribution",
          finding: "Electronics generated 86.3% of total Q1 sales volume.",
          severity: "positive",
          actionable_recommendation:
            "Maintain depth in premium electronics inventory.",
        },
      ];

      render(
        <EvidencePanel
          metrics={metrics}
          insights={insights}
          dataLimitations="Orders with cancelled or returned status are strictly excluded."
        />
      );

      expect(
        screen.getByText("Verified Ground-Truth Metrics")
      ).toBeInTheDocument();
      expect(screen.getByText("$2,490.00")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
      expect(screen.getAllByText(/source: orders/i)).toHaveLength(2);

      expect(
        screen.getByText("Strong Electronics Contribution")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/86.3% of total Q1 sales volume/)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Maintain depth in premium electronics inventory/)
      ).toBeInTheDocument();

      expect(screen.getByText(/Data Governance Note:/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Orders with cancelled or returned status/i)
      ).toBeInTheDocument();
    });
  });

  // -------------------------------------------------------------
  // 5. ChatMessage & ChatThread Components
  // -------------------------------------------------------------
  describe("ChatMessage & ChatThread", () => {
    it("renders user message cleanly", () => {
      render(
        <ChatMessage
          message={{ role: "user", content: "What is our total revenue?" }}
        />
      );

      expect(screen.getByTestId("chat-message-user")).toBeInTheDocument();
      expect(
        screen.getByText("What is our total revenue?")
      ).toBeInTheDocument();
    });

    it("renders assistant message with summary, follow-ups, and embedded chart", () => {
      const handleFollowUp = vi.fn();
      const assistantMessage = {
        role: "assistant",
        summary: "Total revenue reached $2,490.00 across 5 qualifying orders.",
        insights: [],
        metrics_referenced: [],
        chart_spec: {
          chart_type: "line",
          title: "Monthly Revenue Trajectory",
          x_key: "month",
          y_key: "revenue",
          data: [{ month: "2024-01", revenue: 1220.0 }],
        },
        suggested_follow_ups: ["Show monthly revenue.", "Compare categories."],
      };

      render(
        <ChatMessage
          message={assistantMessage}
          onSelectFollowUp={handleFollowUp}
        />
      );

      expect(screen.getByTestId("chat-message-assistant")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Total revenue reached $2,490.00 across 5 qualifying orders."
        )
      ).toBeInTheDocument();
      expect(screen.getByTestId("dynamic-chart-container")).toBeInTheDocument();

      const followUpBtn = screen.getByText("Show monthly revenue.");
      fireEvent.click(followUpBtn);
      expect(handleFollowUp).toHaveBeenCalledWith("Show monthly revenue.");
    });

    it("renders welcome empty state in ChatThread", () => {
      render(
        <ChatThread
          messages={[]}
          loading={false}
          suggestedQuestions={["What is our revenue?"]}
          onSelectSuggested={vi.fn()}
        />
      );

      expect(screen.getByTestId("chat-welcome-state")).toBeInTheDocument();
      expect(
        screen.getByText("InsightIQ Autonomous Business Analyst")
      ).toBeInTheDocument();
    });

    it("renders thinking indicator in ChatThread when loading", () => {
      render(
        <ChatThread
          messages={[{ role: "user", content: "Analyze sales" }]}
          loading={true}
          suggestedQuestions={[]}
          onSelectSuggested={vi.fn()}
        />
      );

      expect(screen.getByTestId("chat-loading-indicator")).toBeInTheDocument();
      expect(
        screen.getByText(/Querying analytics warehouse and synthesizing evidence/i)
      ).toBeInTheDocument();
    });
  });
});
