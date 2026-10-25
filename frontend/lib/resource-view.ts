import type { Row } from "./api";
import type { ViewState } from "./data-state";

export function resourceViewState(input: {
  rows: readonly Row[];
  visibleRows: readonly Row[];
  loading: boolean;
  error: string;
  term: string;
  retry: () => void;
  clear: () => void;
}): ViewState<readonly Row[]> {
  const { rows, visibleRows, loading, error, term, retry, clear } = input;

  if (loading) return { status: "loading" };
  if (error && rows.length === 0) {
    return { status: "error", error: { message: error, retryable: true }, retry };
  }
  if (error) {
    return {
      status: "partial",
      data: visibleRows,
      totalCount: rows.length,
      filter: { label: error, clear: retry },
    };
  }
  if (rows.length === 0) return { status: "empty", reason: "first-use" };
  if (visibleRows.length === 0) return { status: "empty", reason: "no-data" };
  if (term.length > 0) {
    return {
      status: "partial",
      data: visibleRows,
      totalCount: rows.length,
      filter: { label: term, clear },
    };
  }
  return { status: "populated", data: visibleRows };
}
