#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python3
for s in $(seq 400 419); do $PY gen/formgen2.py train_forms2 "$s" 2>&1 | tail -1; done
for s in $(seq 500 509); do $PY gen/formgen2.py train_forms2 "$s" --hard 2>&1 | tail -1; done
echo CORPUS2-DONE
