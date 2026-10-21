#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME='apexgrid-test'
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/test-stack.compose.yaml"
DATABASE_URL='postgresql://apexgrid:apexgrid@localhost:15432/apexgrid'
MONGODB_URL='mongodb://localhost:27018'
TEST_PYTHON="$REPO_ROOT/.venv/bin/python"

usage() {
  printf 'Usage: %s {up|down|env}\n' "${0##*/}" >&2
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    printf 'Docker is unavailable: install Docker and ensure it is on PATH.\n' >&2
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    printf 'Docker is unavailable: start the Docker daemon and try again.\n' >&2
    exit 1
  fi
}

require_test_python() {
  if [[ ! -x "$TEST_PYTHON" ]]; then
    printf 'Test Python environment is missing: create %s and install backend dependencies.\n' "$TEST_PYTHON" >&2
    exit 1
  fi
}

compose() {
  docker compose --project-name "$PROJECT_NAME" --file "$COMPOSE_FILE" "$@"
}

run_bootstrap() {
  (
    cd "$REPO_ROOT/backend"
    DATABASE_URL="$DATABASE_URL" \
      MONGODB_URL="$MONGODB_URL" \
      MONGODB_DATABASE='apexgrid' \
      APP_ENV='local' \
      SEED_DEMO_DATA='1' \
      PYTHONPATH="$REPO_ROOT/backend${PYTHONPATH:+:$PYTHONPATH}" \
      "$TEST_PYTHON" -m app.bootstrap
  )
}

case "${1:-}" in
  env)
    printf 'DATABASE_URL=%s\nMONGODB_URL=%s\n' "$DATABASE_URL" "$MONGODB_URL"
    ;;
  up)
    require_test_python
    require_docker
    compose up --detach --wait
    run_bootstrap
    ;;
  down)
    require_docker
    if [[ "$PROJECT_NAME" != 'apexgrid-test' ]]; then
      printf 'Refusing volume deletion: unexpected Compose project %s.\n' "$PROJECT_NAME" >&2
      exit 1
    fi
    compose down --volumes
    ;;
  *)
    usage
    exit 2
    ;;
esac
