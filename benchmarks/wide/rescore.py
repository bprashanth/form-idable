#!/usr/bin/env python3
"""Re-score every saved candidate .xlsx against the CURRENT golden.

Goldens get rebuilt as more converters land, so cached metrics in
outputs/<tag>.json go stale. This recomputes them in place from the stored
candidate spreadsheets — no model calls, no cost.

Usage: python3 rescore.py [root_dir ...]
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import wide_diff  # noqa: E402

roots = [Path(a) for a in sys.argv[1:]] or [HERE / "eval_forms", HERE / "forms"]
n_ok = n_skip = 0
for root in roots:
    if not root.exists():
        continue
    for form_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        golden = form_dir / "golden.xlsx"
        if not golden.exists():
            continue
        for xls in sorted((form_dir / "outputs").glob("*.xlsx")):
            meta_p = xls.with_suffix(".json")
            meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
            if meta.get("converter_only"):
                n_skip += 1
                continue
            try:
                r = wide_diff.compare(str(golden), str(xls))
            except Exception as e:  # noqa: BLE001
                print(f"  !! {form_dir.name}/{xls.stem}: {e}")
                continue
            m = r["metrics"]
            meta.update({"form": form_dir.name, "passed": r["passed"]})
            # carry every metric the scorer produces, so new buckets (codes,
            # all) propagate without another edit here
            for k, v in m.items():
                if k not in ("golden_cells", "candidate_cells"):
                    meta[k] = v
            meta.setdefault("mode", xls.stem.split("__")[-1])
            parts = xls.stem.split("__")
            meta.setdefault("provider", parts[0])
            meta.setdefault("model", parts[1].replace("_", "/", 1)
                            if parts[0] == "openrouter" else parts[1])
            meta_p.write_text(json.dumps(meta, indent=2))
            n_ok += 1
print(f"rescored {n_ok} results ({n_skip} converter-only skipped)")
