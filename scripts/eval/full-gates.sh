#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
PYTHON="$REPO_ROOT/.venv/bin/python"
DATABASE_URL='postgresql://apexgrid:apexgrid@localhost:15432/apexgrid'
MONGODB_URL='mongodb://localhost:27018'
MONGODB_DATABASE='apexgrid'
RESULTS_DIR="$(mktemp -d)"
FAILURES=0
GATES=0

cleanup() {
  local index
  for ((index = 0; index < GATES; index++)); do
    rm -f -- "$RESULTS_DIR/gate-$index.log"
  done
  rmdir "$RESULTS_DIR" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

cd "$REPO_ROOT" || exit 1

run_gate() {
  local name="$1"
  shift
  local log="$RESULTS_DIR/gate-$GATES.log"
  GATES=$((GATES + 1))
  printf 'RUN: %s\n' "$name"
  if "$@" >"$log" 2>&1; then
    printf 'PASS: %s\n' "$name"
  else
    local status=$?
    FAILURES=$((FAILURES + 1))
    printf 'FAIL: %s (exit %s)\n' "$name" "$status"
    tail -n 30 "$log" || true
  fi
}

run_gate 'backend ruff check and format' \
  "$PYTHON" -m ruff check backend/app backend/tests
run_gate 'backend ruff format' \
  "$PYTHON" -m ruff format --check backend/app backend/tests
run_gate 'backend mypy strict' \
  "$PYTHON" -m mypy --strict backend/app
run_gate 'database-backed pytest and live acceptance (zero skips)' \
  bash "$SCRIPT_DIR/db-baseline.sh"
run_gate 'frontend typecheck' npm --prefix frontend run typecheck
run_gate 'frontend lint (zero warnings, no explicit any)' \
  npm --prefix frontend run lint -- --max-warnings 0
run_gate 'frontend production build' npm --prefix frontend run build
run_gate 'browser E2E (all configured Playwright projects)' \
  env CI=1 npm --prefix frontend exec -- playwright test \
    --config frontend/playwright.config.ts --reporter=line
run_gate 'backend coverage' \
  env DATABASE_URL="$DATABASE_URL" MONGODB_URL="$MONGODB_URL" \
    MONGODB_DATABASE="$MONGODB_DATABASE" \
    PYTHONPATH="$REPO_ROOT/backend${PYTHONPATH:+:$PYTHONPATH}" \
    "$PYTHON" -m pytest -q --cov=backend/app --cov-report=term-missing \
    --cov-report=xml:coverage.xml backend/tests

if command -v curl >/dev/null 2>&1 \
  && curl --connect-timeout 5 --max-time 10 -fsSI https://pypi.org/simple/ >/dev/null \
  && curl --connect-timeout 5 --max-time 10 -fsSI https://registry.npmjs.org/ >/dev/null; then
  run_gate 'supply-chain audit (pip-audit and npm audit)' \
    bash -c '"$1" -m pip_audit -r backend/requirements.txt && npm --prefix frontend audit --audit-level=high' \
    _ "$PYTHON"
else
  GATES=$((GATES + 1))
  printf 'SKIP: supply-chain audit (package registries are unreachable)\n'
fi

printf 'Gates: %s run, %s failed.\n' "$GATES" "$FAILURES"
if [[ "$FAILURES" -ne 0 ]]; then
  exit 1
fi
