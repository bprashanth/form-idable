#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
EP=http://localhost:8021/v1
# assert we are talking to the model we think we are (see GPU_COORDINATION.md)
curl -s --max-time 5 $EP/models | grep -q qwen3-vl-8b-v4 || { echo "WRONG MODEL ON $EP"; exit 1; }
for f in eval_05 eval_09 eval_11 eval_13 eval_16 eval_21; do
  for m in agentic tiles; do
    if [ "$m" = agentic ]; then
      [ -f "eval_forms/$f/outputs/local__qwen3-vl-8b-v4__agentic-pp.json" ] && continue
      timeout 900 python3 agentic_bench.py --form "eval_forms/$f" --provider local \
        --model qwen3-vl-8b-v4 --endpoint $EP --per-page --max-turns 3 2>&1 | tail -1 | cut -c1-180
    else
      [ -f "eval_forms/$f/outputs/local__qwen3-vl-8b-v4__perpage.json" ] && continue
      LOCAL_ENDPOINT=$EP timeout 900 python3 wide_bench.py run --form "eval_forms/$f" \
        --provider local --model qwen3-vl-8b-v4 --mode perpage --endpoint $EP 2>&1 | tail -1 | cut -c1-180
    fi
  done
done
echo 8B-SWEEP-DONE
