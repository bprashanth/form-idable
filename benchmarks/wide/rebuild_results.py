#!/usr/bin/env python3
"""Rebuild results.json/csv from the per-run outputs/<tag>.json files.

Multiple suite runners write results.json concurrently and can clobber each
other's appends; the per-run JSONs are the durable source of truth. Error-only
rows (no metrics) are dropped — reruns supersede them.
"""
import csv, json
from pathlib import Path

HERE = Path(__file__).parent
FIELDS = ["sector", "form", "provider", "model", "mode", "passed",
          "cell_frac", "num_recall", "num_precision", "num_f1",
          "word_recall", "word_precision", "word_f1",
          "cost_usd", "latency_s", "in_tok", "out_tok", "error"]

rows = []
for p in sorted(HERE.glob("forms/*/outputs/*.json")):
    r = json.loads(p.read_text())
    if r.get("error") and "num_recall" not in r:
        continue
    r.setdefault("form", p.parent.parent.name)
    r["sector"] = r["form"].split("__")[0]
    r.setdefault("error", "")
    rows.append(r)

rows.sort(key=lambda r: (r["form"], r["provider"], r["model"], r.get("mode", "")))
(HERE / "results.json").write_text(json.dumps(rows, indent=2))
with open(HERE / "results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"rebuilt {len(rows)} rows from per-run files")
