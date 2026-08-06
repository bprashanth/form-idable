#!/usr/bin/env bash
# v4 archetype corpus: sparse fill + phone-camera pipeline + pencil + vernacular
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python3
for s in $(seq 800 823); do $PY gen/formgen2.py train_forms_v4 "$s" 2>&1 | tail -1; done
for s in $(seq 860 871); do $PY gen/formgen2.py train_forms_v4 "$s" --hard 2>&1 | tail -1; done
echo CORPUS-V4-DONE
