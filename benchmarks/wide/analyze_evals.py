#!/usr/bin/env python3
"""Summarise results on the frozen tree-eval set, separating models that helped
build the goldens (contaminated) from those that did not (clean).

Usage: python3 analyze_evals.py [eval_forms_dir]
"""
import json, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "eval_forms"

# models used as golden converters — their scores here are inflated
CONTAMINATED = {"gemini-3.6-flash", "qwen/qwen3-vl-32b-instruct", "codex-cli",
                "qwen/qwen3-vl-235b-a22b-instruct", "z-ai/glm-4.6v"}

rows = []
for p in sorted(ROOT.glob("*/outputs/*.json")):
    r = json.loads(p.read_text())
    if r.get("converter_only") or "num_f1" not in r:
        continue
    r["form"] = p.parent.parent.name
    rows.append(r)

if not rows:
    print("no scored results yet"); sys.exit(0)


def avg(k, rs):
    v = [x[k] for x in rs if x.get(k) is not None]
    return sum(v) / len(v) if v else None


def fmt(v, n=3):
    return "-" if v is None else f"{v:.{n}f}"


by = defaultdict(list)
for r in rows:
    by[(r["provider"], r["model"], r["mode"])].append(r)

print("## Tree-eval results (frozen ecology eval set)\n")
print("| model | mode | forms | numF1 | numR | numP | wordF1 | $/form | sec | note |")
print("|---|---|---|---|---|---|---|---|---|---|")
for k, rs in sorted(by.items(), key=lambda kv: -(avg("num_f1", kv[1]) or 0)):
    prov, model, mode = k
    tag = "CONTAMINATED (built goldens)" if model in CONTAMINATED else "clean"
    print(f"| {prov}/{model.split('/')[-1]} | {mode} | {len(rs)} | "
          f"**{fmt(avg('num_f1', rs))}** | {fmt(avg('num_recall', rs))} | "
          f"{fmt(avg('num_precision', rs))} | {fmt(avg('word_f1', rs))} | "
          f"{fmt(avg('cost_usd', rs), 4)} | {fmt(avg('latency_s', rs), 0)} | {tag} |")

print("\n## Per-form numF1 (clean models only)\n")
clean = sorted({(r["provider"], r["model"], r["mode"]) for r in rows
                if r["model"] not in CONTAMINATED},
               key=lambda k: -(avg("num_f1", by[k]) or 0))
forms = sorted({r["form"] for r in rows})
print("| form | " + " | ".join(m.split("/")[-1] for _, m, _ in clean) + " |")
print("|---" * (len(clean) + 1) + "|")
for f in forms:
    cells = []
    for k in clean:
        hit = [r for r in by[k] if r["form"] == f]
        cells.append(fmt(hit[0]["num_f1"]) if hit else "-")
    print(f"| {f} | " + " | ".join(cells) + " |")
