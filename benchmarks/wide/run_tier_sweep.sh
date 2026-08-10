#!/usr/bin/env bash
# Re-benchmark the tier candidates on the SAME 6 forms, with reasoning
# correctly disabled for gemini 3.x, plus the 72B and OCR-specialist options.
set -u
cd "$(dirname "$0")"
FORMS="eval_05 eval_09 eval_11 eval_13 eval_16 eval_21"
for f in $FORMS; do
  for spec in "gemini:gemini-3.5-flash:perpage" "gemini:gemini-3.6-flash:perpage" \
              "openrouter:qwen/qwen2.5-vl-72b-instruct:perpage"; do
    IFS=: read prov model mode <<< "$spec"
    tag="${prov}__${model//\//_}__${mode}"
    [ -f "eval_forms/$f/outputs/$tag.json" ] && continue
    echo "--- $f $model"
    timeout 900 python3 wide_bench.py run --form "eval_forms/$f" \
      --provider "$prov" --model "$model" --mode "$mode" 2>&1 | tail -1 | cut -c1-170
  done
done
echo TIER-SWEEP-DONE
