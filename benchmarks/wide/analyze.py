#!/usr/bin/env python3
"""Aggregate results.json into per-model and per-sector summary tables (markdown)."""
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
rows = [r for r in json.loads((HERE / "results.json").read_text()) if not r.get("error")]

def avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None

def fmt(v, nd=2):
    return "-" if v is None else f"{v:.{nd}f}"

def key(r):
    return f"{r['provider']}/{r['model'].split('/')[-1]}|{r['mode']}"

# ── per-model overall ─────────────────────────────────────────────
by_model = defaultdict(list)
for r in rows:
    by_model[key(r)].append(r)

print("## Per-model averages (over forms run)\n")
print("| model | mode | n | numR | numP | numF1 | wordR | wordP | wordF1 | cell | $/form | sec |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
def score(rs):
    return avg([r.get("num_f1") for r in rs]) or 0
for k, rs in sorted(by_model.items(), key=lambda kv: -score(kv[1])):
    name, mode = k.split("|")
    print(f"| {name} | {mode} | {len(rs)} | {fmt(avg([r.get('num_recall') for r in rs]))} "
          f"| {fmt(avg([r.get('num_precision') for r in rs]))} | {fmt(avg([r.get('num_f1') for r in rs]))} "
          f"| {fmt(avg([r.get('word_recall') for r in rs]))} | {fmt(avg([r.get('word_precision') for r in rs]))} "
          f"| {fmt(avg([r.get('word_f1') for r in rs]))} | {fmt(avg([r.get('cell_frac') for r in rs]))} "
          f"| {fmt(avg([r.get('cost_usd') for r in rs]), 4)} | {fmt(avg([r.get('latency_s') for r in rs]), 0)} |")

# ── per-sector winners ────────────────────────────────────────────
print("\n## Per-sector best (by num F1)\n")
by_sector = defaultdict(lambda: defaultdict(list))
for r in rows:
    by_sector[r.get("sector", r["form"].split("__")[0])][key(r)].append(r)
print("| sector | forms | best model | numF1 | runner-up | numF1 |")
print("|---|---|---|---|---|---|")
for sec, models in sorted(by_sector.items()):
    nf = len({r["form"] for ms in models.values() for r in ms})
    ranked = sorted(models.items(), key=lambda kv: -(score(kv[1])))
    (m1, r1), (m2, r2) = ranked[0], (ranked[1] if len(ranked) > 1 else (None, []))
    print(f"| {sec} | {nf} | {m1.split('|')[0]} | {fmt(score(r1))} "
          f"| {m2.split('|')[0] if m2 else '-'} | {fmt(score(r2)) if r2 else '-'} |")

# ── per-form detail for the winner set ────────────────────────────
print("\n## Errors / excluded rows\n")
for r in json.loads((HERE / "results.json").read_text()):
    if r.get("error"):
        print(f"- {r['form']} {r['provider']}/{r['model']} {r['mode']}: {r['error'][:120]}")
