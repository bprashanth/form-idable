#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
M=${1:-qwen3-vl-2b-v2}
for f in eval_forms/eval_*; do
  tag="local__${M}__perpage"
  [ -f "$f/outputs/$tag.json" ] && continue
  echo "--- $(basename $f)"
  python3 wide_bench.py run --form "$f" --provider local --model "$M" \
    --mode perpage --endpoint http://localhost:8010/v1 2>&1 | tail -1
done
echo TUNED-EVAL-DONE
