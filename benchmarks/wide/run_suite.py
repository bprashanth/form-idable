#!/usr/bin/env python3
"""Run a set of model configs over every form dir; accumulate results.csv/json.

Usage:
  python3 run_suite.py --configs configs.json [--forms forms] [--only form1,form2]
                       [--budget 20.0]

configs.json: list of {"provider","model","mode","endpoint"?} dicts.
Skips (provider,model,mode,form) combos whose outputs/<tag>.json already exists
(delete the json to re-run). Stops if cumulative recorded spend exceeds budget.
"""
import argparse, csv, json, sys, time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import wide_bench  # noqa: E402

RESULTS_CSV  = HERE / "results.csv"
RESULTS_JSON = HERE / "results.json"
FIELDS = ["sector", "form", "provider", "model", "mode", "passed",
          "cell_frac", "num_recall", "num_precision", "num_f1",
          "word_recall", "word_precision", "word_f1",
          "cost_usd", "latency_s", "in_tok", "out_tok", "error"]


def load_results():
    if RESULTS_JSON.exists():
        return json.loads(RESULTS_JSON.read_text())
    return []


def save_results(rows):
    RESULTS_JSON.write_text(json.dumps(rows, indent=2))
    with open(RESULTS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def total_spend(rows):
    return sum(r.get("cost_usd") or 0 for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", required=True)
    ap.add_argument("--forms", default=str(HERE / "forms"))
    ap.add_argument("--only", default=None)
    ap.add_argument("--budget", type=float, default=20.0)
    a = ap.parse_args()

    configs = json.loads(Path(a.configs).read_text())
    form_dirs = sorted(p for p in Path(a.forms).iterdir()
                       if (p / "input.pdf").exists() and (p / "golden.xlsx").exists())
    if a.only:
        keep = set(a.only.split(","))
        form_dirs = [f for f in form_dirs if f.name in keep]

    rows = load_results()
    done = {(r["form"], r["provider"], r["model"], r["mode"]) for r in rows}

    for fd in form_dirs:
        for cfg in configs:
            key = (fd.name, cfg["provider"], cfg["model"], cfg["mode"])
            if key in done:
                continue
            spend = total_spend(rows)
            if spend >= a.budget:
                print(f"BUDGET REACHED (${spend:.2f} >= ${a.budget}); stopping.")
                save_results(rows); return
            # ensure images exist
            if not wide_bench._images(fd, cfg["mode"]):
                (wide_bench.render_tiles if cfg["mode"] == "tiled"
                 else wide_bench.render_pages)(fd)
            print(f"--- {fd.name} | {cfg['provider']}/{cfg['model']} | {cfg['mode']} "
                  f"(spend so far ${spend:.3f})")
            try:
                row = wide_bench.run_one(fd, cfg["provider"], cfg["model"],
                                         cfg["mode"], cfg.get("endpoint"))
            except Exception as e:  # noqa: BLE001 — one bad combo must not kill the sweep
                row = {"form": fd.name, "provider": cfg["provider"],
                       "model": cfg["model"], "mode": cfg["mode"],
                       "error": str(e)[:300]}
                print(f"ERROR: {row['error']}")
            row.setdefault("error", "")
            row["sector"] = fd.name.split("__")[0]
            rows.append(row)
            done.add(key)
            save_results(rows)
            time.sleep(1)
    print(f"suite done. total recorded spend ${total_spend(rows):.3f}")


if __name__ == "__main__":
    main()
