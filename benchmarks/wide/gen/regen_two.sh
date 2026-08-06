#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python3
for s in $(seq 200 219); do
  for f in ecology__growth_survival ecology__soil_micro; do
    rm -rf "train_forms2/${f}__${s}_0"
    $PY gen/formgen2.py train_forms2 "$s" "$f" >/dev/null 2>&1
  done
done
for s in $(seq 300 309); do
  for f in ecology__growth_survival ecology__soil_micro; do
    rm -rf "train_forms2/${f}__${s}_0_hard"
    $PY gen/formgen2.py train_forms2 "$s" "$f" --hard >/dev/null 2>&1
  done
done
echo REGEN-DONE
