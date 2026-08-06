#!/usr/bin/env python3
"""Build the v3 TRAINING corpus.

Two changes that the evidence demands:

1. **Sparse fill is first-class.** Every v2 training form was densely filled, so
   the model learned "keep emitting rows" and over-produces on real sheets
   (measured: recall 0.96-1.00 with precision 0.04-0.10 on sparse forms; the
   partner's own seed-germination sheet is ~90% empty). Densities here are drawn
   from a distribution weighted toward SPARSE, and a share of forms are almost
   entirely blank.

2. **Real template structures**, not only layouts we invented — overfitting to
   our own 17 archetypes is exactly what the structure-diverse eval exposed
   (numF1 0.668 on familiar forms vs 0.337 on unseen layouts).

STRICT SPLIT: only templates whose deterministic split is `dev` may be trained
on. `test` templates are eval-only, forever. This is what keeps the v3 numbers
honest — the same hash function is used by build_struct_eval.py, so the two
scripts cannot disagree.

Usage: python3 build_train_corpus_v3.py <templates_dir> <out_dir> [--per 6]
"""
import argparse, hashlib, json, random, sys
from pathlib import Path

import fitz

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from fill_template import fill  # noqa: E402


def split_of(p: Path):
    """MUST match build_struct_eval.split_of exactly."""
    h = int(hashlib.sha256(p.stem.encode()).hexdigest()[:8], 16)
    return "test" if h % 100 < 40 else "dev"


# UNIFORM density. v3 weighted this toward sparse and the model then UNDER-
# produced on densely-filled real sheets (partner scans: recall 0.774 -> 0.630).
# The training fill distribution must MATCH DEPLOYMENT, not favour either end.
DENSITY_CHOICES = [0.08, 0.18, 0.30, 0.42, 0.55, 0.68, 0.80, 0.90, 1.0]
DENSITY_WEIGHTS = [1, 1, 1, 1, 1, 1, 1, 1, 1]   # UNIFORM: v3 was sparse-heavy and under-produced on dense forms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("templates"); ap.add_argument("out")
    ap.add_argument("--per", type=int, default=6, help="fills per template page")
    ap.add_argument("--cap-pages", type=int, default=3)
    a = ap.parse_args()
    tdir, out = Path(a.templates), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    train_tpls = [p for p in sorted(tdir.glob("*.pdf")) if split_of(p) == "dev"]
    held_out = [p.stem for p in sorted(tdir.glob("*.pdf")) if split_of(p) == "test"]
    print(f"train-eligible templates: {len(train_tpls)}  "
          f"HELD OUT (never trained on): {len(held_out)}")
    print("  held out:", ", ".join(held_out))

    made, skipped, manifest = 0, 0, []
    for pdf in train_tpls:
        try:
            npages = min(fitz.open(str(pdf)).page_count, a.cap_pages)
        except Exception:
            continue
        for pg in range(npages):
            for k in range(a.per):
                seed = abs(hash((pdf.stem, pg, k, "v3"))) % 1000000
                rng = random.Random(seed)
                dens = rng.choices(DENSITY_CHOICES, DENSITY_WEIGHTS)[0]
                hard = rng.random() < 0.45
                name = f"{pdf.stem}__p{pg}__k{k}"
                meta, err = fill(pdf, out / name, seed=seed, density=dens,
                                 page_no=pg, hard=hard)
                if err:
                    skipped += 1
                    continue
                meta["name"] = name
                manifest.append(meta)
                made += 1
                if made % 25 == 0:
                    print(f"  … {made} forms", flush=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    if manifest:
        ds = sorted(m["density"] for m in manifest)
        fills = sorted(m["filled"] for m in manifest)
        print(f"\nbuilt {made} training forms ({skipped} skipped) from "
              f"{len({m['template'] for m in manifest})} templates")
        print(f"  density  p10 {ds[len(ds)//10]:.2f}  median {ds[len(ds)//2]:.2f}  "
              f"p90 {ds[-max(1,len(ds)//10)]:.2f}")
        print(f"  filled cells  min {fills[0]}  median {fills[len(fills)//2]}  "
              f"max {fills[-1]}")
        print(f"  near-empty forms (<8 filled cells): "
              f"{sum(1 for f in fills if f < 8)}")


if __name__ == "__main__":
    main()
