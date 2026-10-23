#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
TEST_PYTHON="$REPO_ROOT/.venv/bin/python"
DATABASE_URL='postgresql://apexgrid:apexgrid@localhost:15432/apexgrid'
MONGODB_URL='mongodb://localhost:27018'
API_URL='http://127.0.0.1:18000/api'
REPORT_DIR="$(mktemp -d)"
REPORT="$REPORT_DIR/backend-tests.xml"
API_LOG="$REPORT_DIR/api.log"
API_PID=''

cleanup() {
  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
  rm -f "$REPORT" "$API_LOG"
  rmdir "$REPORT_DIR" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [[ ! -x "$TEST_PYTHON" ]]; then
  printf 'FAIL: test Python environment is missing at %s\n' "$TEST_PYTHON" >&2
  exit 1
fi

printf 'Starting isolated apexgrid-test database stack...\n'
bash "$SCRIPT_DIR/test-stack.sh" up

set +e
(
  cd "$REPO_ROOT"
  APEXGRID_TEST_STACK=1 DATABASE_URL="$DATABASE_URL" MONGODB_URL="$MONGODB_URL" \
    MONGODB_DATABASE='apexgrid' APP_ENV='local' \
    PYTHONPATH="$REPO_ROOT/backend${PYTHONPATH:+:$PYTHONPATH}" \
    "$TEST_PYTHON" -m pytest backend/tests -q --junitxml="$REPORT"
)
pytest_status=$?
set -e

set +e
"$TEST_PYTHON" "$SCRIPT_DIR/junit_gate.py" "$REPORT" "$pytest_status"
summary_status=$?
set -e
if [[ "$summary_status" -ne 0 ]]; then
  printf 'FAIL: backend test gate failed (pytest exit %s; real skips are rejected).\n' "$pytest_status" >&2
  exit 1
fi

printf 'Starting loopback API on 127.0.0.1:18000...\n'
(
  cd "$REPO_ROOT/backend"
  DATABASE_URL="$DATABASE_URL" MONGODB_URL="$MONGODB_URL" \
    MONGODB_DATABASE='apexgrid' APP_ENV='local' \
    PYTHONPATH="$REPO_ROOT/backend${PYTHONPATH:+:$PYTHONPATH}" \
    exec "$TEST_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 18000
) >"$API_LOG" 2>&1 &
API_PID=$!

API_URL="$API_URL" "$TEST_PYTHON" - <<'PY'
import os
import time
import urllib.request

url = os.environ["API_URL"] + "/health"
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status == 200:
                break
    except Exception:
        time.sleep(0.25)
else:
    raise SystemExit("API did not become healthy within 30 seconds")
PY

printf 'Running live acceptance flow...\n'
cd "$REPO_ROOT"
API_URL="$API_URL" DATABASE_URL="$DATABASE_URL" MONGODB_URL="$MONGODB_URL" \
  "$TEST_PYTHON" scripts/acceptance.py
printf 'PASS: isolated database baseline and live acceptance flow.\n'
