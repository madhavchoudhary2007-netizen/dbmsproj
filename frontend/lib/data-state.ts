export type ViewState<T> =
  | { status: "empty"; reason: "no-data" | "first-use" }
  | { status: "loading" }
  | { status: "populated"; data: T }
  | { status: "error"; error: { message: string; retryable: boolean }; retry: () => void }
  | { status: "partial"; data: T; filter: { label: string; clear: () => void }; totalCount: number };

export function assertNever(value: never): never {
  throw new Error(`Unexpected value: ${JSON.stringify(value)}`);
}
