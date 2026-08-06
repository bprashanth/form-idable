#!/usr/bin/env bash
# Score models on the structure-diverse eval. Idempotent.
set -u
cd "$(dirname "$0")"
MODE=${1:?usage: run_struct_eval.sh local <name> | gemini}
for f in struct_eval/*/; do
  [ -f "$f/golden.xlsx" ] || continue
  [ -d "$f/tiles" ] || python3 wide_bench.py tiles --form "$f" >/dev/null 2>&1
  case "$MODE" in
    local)  P=local; M=${2:?need model}; EP="--endpoint http://localhost:8010/v1";;
    gemini) P=gemini; M=gemini-2.5-flash; EP="";;
  esac
  tag="${P}__${M//\//_}__perpage"
  [ -f "$f/outputs/$tag.json" ] && continue
  python3 wide_bench.py run --form "$f" --provider $P --model "$M" --mode perpage $EP 2>&1 | tail -1
done
echo STRUCT-EVAL-DONE
