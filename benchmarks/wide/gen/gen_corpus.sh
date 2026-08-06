#!/usr/bin/env bash
# Generate the v2 training corpus: 17 archetypes x seeds, normal + hard.
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python3
OUT=${1:-train_forms2}
for s in $(seq 200 219); do
  $PY gen/formgen2.py "$OUT" "$s" 2>&1 | tail -1
done
for s in $(seq 300 309); do
  $PY gen/formgen2.py "$OUT" "$s" --hard 2>&1 | tail -1
done
echo CORPUS-DONE
