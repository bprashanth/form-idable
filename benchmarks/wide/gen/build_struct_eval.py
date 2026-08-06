#!/usr/bin/env python3
"""Build the structure-diverse eval from real blank templates.

Design goals (user directive 2026-08-01):
  * STRUCTURE diversity comes from real downloaded templates, not layouts we
    invented — so neither the model nor the template-matcher can be judged on
    structures it effectively memorised.
  * The three axes vary INDEPENDENTLY so they can be attributed separately:
      structure  = which template
      handwriting = writer cohort / prose mode (seed)
      conditions = clean vs `--hard` degradation
  * Every template gets >=2 fills with different seeds. Those are POSITIVE
    pairs for template matching; different templates are negatives.
  * Templates are split dev/test. Anything used to build or tune the matcher
    must come from dev only; test is held out, which is what stops the
    fingerprint evaluation from cheating.

Usage: python3 build_struct_eval.py <templates_dir> <out_dir> [--per 2]
"""
import argparse, hashlib, json, random, sys
from pathlib import Path

import fitz

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from fill_template import fill  # noqa: E402


def usable_pages(pdf: Path, cap=3):
    """Pages that actually contain a grid worth filling."""
    try:
        n = fitz.open(str(pdf)).page_count
    except Exception:
        return []
    return list(range(min(n, cap)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("templates"); ap.add_argument("out")
    ap.add_argument("--per", type=int, default=2, help="fills per template page")
    a = ap.parse_args()
    tdir, out = Path(a.templates), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(p for p in tdir.glob("*.pdf"))
    # deterministic dev/test split by filename hash — stable as templates are added
    def split_of(p):
        h = int(hashlib.sha256(p.stem.encode()).hexdigest()[:8], 16)
        return "test" if h % 100 < 40 else "dev"

    manifest, made, skipped = [], 0, []
    for pdf in pdfs:
        sp = split_of(pdf)
        for pg in usable_pages(pdf):
            for k in range(a.per):
                seed = abs(hash((pdf.stem, pg, k))) % 100000
                rng = random.Random(seed)
                hard = (k % 2 == 1)          # one clean + one degraded per pair
                dens = rng.choice([0.25, 0.45, 0.6, 0.8])   # sparse..dense
                name = f"{sp}__{pdf.stem}__p{pg}__v{k}"
                meta, err = fill(pdf, out / name, seed=seed, density=dens,
                                 page_no=pg, hard=hard)
                if err:
                    skipped.append((name, err))
                    continue
                meta.update({"split": sp, "template_id": f"{pdf.stem}__p{pg}",
                             "variant": k, "name": name})
                manifest.append(meta)
                made += 1
                print(f"  {name}  cells={meta['cells']} filled={meta['filled']} "
                      f"dens={dens} hard={hard}", flush=True)

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    tids = {m["template_id"] for m in manifest}
    print(f"\nbuilt {made} forms from {len(tids)} template-pages "
          f"({len(pdfs)} template files)")
    for s in ("dev", "test"):
        n = sum(1 for m in manifest if m["split"] == s)
        t = len({m["template_id"] for m in manifest if m["split"] == s})
        print(f"  {s}: {n} forms / {t} template-pages")
    pos = sum(1 for t in tids
              if sum(1 for m in manifest if m["template_id"] == t) >= 2)
    print(f"  positive-pair template-pages (>=2 fills): {pos}")
    if skipped:
        print(f"  skipped {len(skipped)} (no usable grid): "
              + ", ".join(n for n, _ in skipped[:6]) + (" …" if len(skipped) > 6 else ""))


if __name__ == "__main__":
    main()
