#!/usr/bin/env bash
# Full 24-form run for the trained 8B on deterministic tiles (the best local
# config). Free — local model — so there is no reason to sub-sample.
set -u
cd "$(dirname "$0")"
EP=http://localhost:8021/v1
curl -s --max-time 5 $EP/models | grep -q qwen3-vl-8b-v4 || { echo "WRONG MODEL"; exit 1; }
for f in eval_forms/eval_*; do
  [ -f "$f/outputs/local__qwen3-vl-8b-v4__perpage.json" ] && continue
  [ -d "$f/tiles" ] || python3 wide_bench.py tiles --form "$f" >/dev/null 2>&1
  timeout 1800 python3 wide_bench.py run --form "$f" --provider local \
    --model qwen3-vl-8b-v4 --mode perpage --endpoint $EP 2>&1 | tail -1 | cut -c1-120
done
echo FULL-LOCAL-DONE
