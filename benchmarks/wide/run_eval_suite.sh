#!/usr/bin/env bash
# Run the frozen tree-eval suite.
#
#   ./run_eval_suite.sh api                  # API models (gemini, openrouter)
#   ./run_eval_suite.sh local <served-name>  # whatever is on :8010 right now
#
# codex is EXCLUDED from the leaderboard by default: it was one of the three
# converters used to build the goldens, so its scores are contaminated. Run it
# only with `./run_eval_suite.sh codex` and label the result accordingly.
set -u
cd "$(dirname "$0")"
MODE=${1:-api}

case "$MODE" in
  api)
    python3 run_suite.py --configs configs_eval_api.json --forms eval_forms --budget 8
    ;;
  local)
    NAME=${2:?usage: run_eval_suite.sh local <served-model-name>}
    cat > /tmp/cfg_local_eval.json <<EOF
[{"provider":"local","model":"$NAME","mode":"perpage","endpoint":"http://localhost:8010/v1"}]
EOF
    python3 run_suite.py --configs /tmp/cfg_local_eval.json --forms eval_forms --budget 1
    ;;
  codex)
    python3 run_codex.py eval_forms/eval_*
    ;;
  *) echo "usage: $0 api|local <name>|codex"; exit 1;;
esac
