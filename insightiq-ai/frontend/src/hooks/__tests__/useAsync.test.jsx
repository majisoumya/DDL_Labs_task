import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useState } from "react";
import { useAsync } from "../useAsync";

describe("useAsync Hook", () => {
  it("executes immediately on mount and populates data", async () => {
    const mockFn = vi.fn().mockResolvedValue({ status: "success" });

    const { result } = renderHook(() => useAsync(mockFn));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual({ status: "success" });
    expect(result.current.error).toBeNull();
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it("does not trigger an infinite loop when given an inline anonymous function", async () => {
    let callCount = 0;

    const { result, rerender } = renderHook(() => {
      return useAsync(async () => {
        callCount++;
        return `count-${callCount}`;
      }, []);
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(callCount).toBe(1);

    // Trigger multiple parent re-renders
    rerender();
    rerender();
    rerender();

    // The async function must NOT be called again because dependencies have not changed
    expect(callCount).toBe(1);
    expect(result.current.data).toBe("count-1");
  });

  it("re-executes when specified dependencies change", async () => {
    let callCount = 0;

    const { result, rerender } = renderHook(
      ({ chartType }) => {
        return useAsync(async () => {
          callCount++;
          return `rendered-${chartType}`;
        }, [chartType]);
      },
      { initialProps: { chartType: "line" } }
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(callCount).toBe(1);
    expect(result.current.data).toBe("rendered-line");

    // Change dependency from 'line' to 'bar'
    rerender({ chartType: "bar" });

    await waitFor(() => {
      expect(result.current.data).toBe("rendered-bar");
    });

    expect(callCount).toBe(2);
  });

  it("handles errors and allows retry", async () => {
    const mockFn = vi
      .fn()
      .mockRejectedValueOnce(new Error("API Connection Failed"))
      .mockResolvedValueOnce("Recovered Data");

    const { result } = renderHook(() => useAsync(mockFn));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("API Connection Failed");

    // Retry execution
    await act(async () => {
      await result.current.retry();
    });

    expect(result.current.data).toBe("Recovered Data");
    expect(result.current.error).toBeNull();
    expect(mockFn).toHaveBeenCalledTimes(2);
  });
});
