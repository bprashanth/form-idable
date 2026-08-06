#!/usr/bin/env bash
# Run only the CLEAN eval models (models never used as golden converters, so
# their scores on this eval are unbiased) over every eval form. Skips any
# (form, model) pair that already has a result — idempotent, safe to re-run
# after an interruption.
set -u
cd "$(dirname "$0")"

run_pair() {
  local f=$1 prov=$2 model=$3
  local tag="${prov}__${model//\//_}__perpage"
  [ -f "$f/outputs/$tag.json" ] && return 0
  echo "--- $(basename "$f") $model"
  python3 wide_bench.py run --form "$f" --provider "$prov" --model "$model" \
      --mode perpage 2>&1 | tail -1
}

for f in eval_forms/eval_*; do
  run_pair "$f" gemini     gemini-2.5-flash
  run_pair "$f" openrouter qwen/qwen3-vl-8b-instruct
done
echo CLEAN-EVAL-DONE
