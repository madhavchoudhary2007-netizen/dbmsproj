#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
PYTHON="$REPO_ROOT/.venv/bin/python"
IMPORT='from backend.app.config import JWT_SECRET'
CASES=0
FAILURES=0

check_case() {
  local label="$1"
  local expected="$2"
  shift 2
  local actual

  CASES=$((CASES + 1))
  if "$@" >/dev/null 2>&1; then
    actual=success
  else
    actual=failure
  fi

  if [[ "$actual" == "$expected" ]]; then
    printf 'PASS: %s\n' "$label"
  else
    FAILURES=$((FAILURES + 1))
    printf 'FAIL: %s (expected %s, got %s)\n' "$label" "$expected" "$actual"
  fi
}

cd "$REPO_ROOT" || exit 1

if [[ ! -x "$PYTHON" ]]; then
  printf 'FAIL: configured Python interpreter is unavailable\n'
  exit 1
fi

check_case 'production missing secret rejected' failure \
  env -u JWT_SECRET APP_ENV=production "$PYTHON" -c "$IMPORT"
check_case 'production demo secret rejected' failure \
  env APP_ENV=production JWT_SECRET=dev-change-me "$PYTHON" -c "$IMPORT"
check_case 'production short secret rejected' failure \
  env APP_ENV=production JWT_SECRET=short-test-key "$PYTHON" -c "$IMPORT"
check_case 'production adequate secret accepted' success \
  env APP_ENV=production JWT_SECRET=regression-test-signing-secret-with-adequate-length "$PYTHON" -c "$IMPORT"
check_case 'local missing secret fallback accepted' success \
  env -u JWT_SECRET APP_ENV=local "$PYTHON" -c "$IMPORT"

printf 'Cases: %s run, %s failed.\n' "$CASES" "$FAILURES"
[[ "$FAILURES" -eq 0 ]]
