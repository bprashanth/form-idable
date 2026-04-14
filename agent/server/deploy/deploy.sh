#!/usr/bin/env bash
# Full deploy: build (with smoke test) → push to ECR → update Lambda.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"$SCRIPT_DIR/build.sh" --test
"$SCRIPT_DIR/push.sh"
