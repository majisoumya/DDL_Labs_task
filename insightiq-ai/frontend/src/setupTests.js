import React from "react";
import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock ResponsiveContainer for jsdom test runner to avoid 0-width/0-height warnings
vi.mock("recharts", async () => {
  const OriginalRecharts = await vi.importActual("recharts");
  return {
    ...OriginalRecharts,
    ResponsiveContainer: ({ children }) =>
      React.createElement(
        "div",
        { "data-testid": "mocked-responsive-container", style: { width: 800, height: 400 } },
        children
      ),
  };
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock scrollIntoView for jsdom
window.HTMLElement.prototype.scrollIntoView = vi.fn();
