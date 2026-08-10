#!/usr/bin/env bash
# agentic per-page sweep: does forcing page coverage + letting the model zoom
# beat fixed tiles, and does it help the tuned local 2B too?
set -u
cd "$(dirname "$0")"
FORMS="eval_05 eval_09 eval_11 eval_13 eval_16 eval_21"
for f in $FORMS; do
  for spec in "$@"; do
    prov="${spec%%:*}"; model="${spec#*:}"
    tag="${prov}__${model//\//_}__agentic-pp"
    [ -f "eval_forms/$f/outputs/$tag.json" ] && continue
    echo "--- $f $model"
    timeout 900 python3 agentic_bench.py --form "eval_forms/$f" \
      --provider "$prov" --model "$model" --per-page --max-turns 3 2>&1 | tail -1 | cut -c1-190
  done
done
echo AGENTIC-SWEEP-DONE
