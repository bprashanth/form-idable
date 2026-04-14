#!/usr/bin/env bash
# Build the Docker image. Pass --test to run a smoke test after build.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/config.sh"

echo "=== Building ${IMAGE} ==="
docker build -t "$IMAGE" "$SERVER_DIR"

if [ "${1:-}" = "--test" ]; then
  echo "=== Smoke test ==="
  CONTAINER_ID=$(docker run -d --rm -p 8079:${SERVER_PORT} "$IMAGE")
  sleep 5

  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:8079${HEALTH_CHECK_PATH}" || echo "000")
  docker stop "$CONTAINER_ID" >/dev/null 2>&1 || true

  if [ "$STATUS" = "200" ]; then
    echo "  health check passed (HTTP ${STATUS})"
  else
    echo "  health check FAILED (HTTP ${STATUS}) — check HEALTH_CHECK_PATH in config.sh"
    exit 1
  fi
fi

echo "=== Build complete ==="
