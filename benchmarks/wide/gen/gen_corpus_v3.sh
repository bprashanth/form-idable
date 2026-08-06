#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python3
for s in $(seq 600 615); do $PY gen/formgen2.py train_forms_v3 "$s" 2>&1 | tail -1; done
for s in $(seq 700 707); do $PY gen/formgen2.py train_forms_v3 "$s" --hard 2>&1 | tail -1; done
echo CORPUS-V3-DONE
