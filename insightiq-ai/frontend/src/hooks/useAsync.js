import { useState, useEffect, useCallback, useRef } from "react";

/**
 * Reusable asynchronous execution hook with loading, error, and retry states.
 * Uses a stable ref for asyncFunction to prevent infinite re-render loops when
 * callers pass anonymous inline functions, while strictly honoring the dependencies array.
 *
 * @param {Function} asyncFunction The async function to execute.
 * @param {Array} dependencies Dependency array triggering re-execution.
 * @param {boolean} immediate Whether to run immediately on mount (default: true).
 */
export const useAsync = (asyncFunction, dependencies = [], immediate = true) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);

  // Stable ref to the latest asyncFunction prevents execution from depending on function identity
  const fnRef = useRef(asyncFunction);
  useEffect(() => {
    fnRef.current = asyncFunction;
  });

  const execute = useCallback(
    async (...params) => {
      setLoading(true);
      setError(null);
      try {
        const result = await fnRef.current(...params);
        setData(result);
        setLoading(false);
        return result;
      } catch (err) {
        setError(err.message || "An unexpected error occurred.");
        setLoading(false);
        throw err;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    dependencies
  );

  useEffect(() => {
    if (immediate) {
      execute().catch(() => {});
    }
  }, [execute, immediate]);

  return {
    data,
    loading,
    error,
    execute,
    retry: execute,
  };
};

export default useAsync;
