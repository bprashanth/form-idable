#!/usr/bin/env python3
"""Run structured (tier-3) extraction across struct_eval and report the lift.

struct_eval forms were generated FROM blank templates, so every blank is
available — which lets us measure the tier-3 ceiling on 76 forms without asking
the partner for anything.

Reports `page` (tier-2 baseline, already scored) against `band` and `band-sub`
so the contribution of cropping and of printed-layer subtraction can be
attributed separately.

Usage: python3 run_structured_suite.py <served_model> [--limit N] [--modes band,band-sub]
"""
import argparse, json, statistics as st, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import structured_extract as se  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--endpoint", default="http://localhost:8010/v1")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--modes", default="band,band-sub")
a = ap.parse_args()

root = HERE / "struct_eval"
man = json.loads((root / "manifest.json").read_text())
tpl_dir = HERE / "downloads" / "templates"

done = []
for i, m in enumerate(man):
    if a.limit and i >= a.limit:
        break
    fd = root / m["name"]
    tpl = tpl_dir / m["template"]
    if not (fd / "golden.xlsx").exists() or not tpl.exists():
        continue
    for mode in a.modes.split(","):
        tag = f"structured__{a.model}__{mode}"
        if (fd / "outputs" / f"{tag}.json").exists():
            done.append(json.loads((fd / "outputs" / f"{tag}.json").read_text()))
            continue
        try:
            row, err = se.run(fd, tpl, a.model, a.endpoint, mode, m["page"])
        except Exception as e:  # noqa: BLE001
            print(f"  !! {m['name']} {mode}: {str(e)[:120]}", flush=True)
            continue
        if err:
            print(f"  skip {m['name']}: {err}", flush=True)
            continue
        done.append(row)
        print(f"  {m['name'][:44]:44s} {mode:9s} F1 {row['num_f1']:.3f} "
              f"R {row['num_recall']:.2f} P {row['num_precision']:.2f} "
              f"cf {row['cell_frac']:.1f} bands {row['bands']} "
              f"aligned={row['aligned']}", flush=True)

# ── comparison against the tier-2 page baseline ──────────────────
def load_page(name):
    p = root / name / "outputs" / f"local__{a.model}__perpage.json"
    if not p.exists():
        # fall back to whatever page-mode result exists
        for q in (root / name / "outputs").glob("local__*__perpage.json"):
            return json.loads(q.read_text())
        return None
    return json.loads(p.read_text())

print("\n" + "=" * 70)
by_mode = {}
for r in done:
    by_mode.setdefault(r["mode"], []).append(r)
for mode, rs in sorted(by_mode.items()):
    names = {r["form"] for r in rs}
    base = [load_page(n) for n in names]
    base = [b for b in base if b]
    print(f"\n{mode}: n={len(rs)}")
    print(f"  structured  numF1 {st.mean(r['num_f1'] for r in rs):.3f} | "
          f"recall {st.mean(r['num_recall'] for r in rs):.3f} | "
          f"precision {st.mean(r['num_precision'] for r in rs):.3f} | "
          f"cell_frac {st.mean(r['cell_frac'] for r in rs):.2f} | "
          f"{st.mean(r['latency_s'] for r in rs):.0f}s")
    if base:
        print(f"  page (t2)   numF1 {st.mean(b['num_f1'] for b in base):.3f} | "
              f"recall {st.mean(b['num_recall'] for b in base):.3f} | "
              f"precision {st.mean(b['num_precision'] for b in base):.3f} | "
              f"cell_frac {st.mean(b['cell_frac'] for b in base):.2f}")
        print(f"  LIFT        {st.mean(r['num_f1'] for r in rs) - st.mean(b['num_f1'] for b in base):+.3f} numF1")
    print(f"  aligned by homography: {sum(1 for r in rs if r['aligned'])}/{len(rs)}")
