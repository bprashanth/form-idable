#!/usr/bin/env python3
"""Does template fingerprinting (a) work and (b) cheat?

Protocol, designed so it cannot flatter itself:
  * Positive pair  = two fills of the SAME template page (different writer
    cohort, different values, one clean + one degraded).
  * Negative pair  = two different template pages.
  * Thresholds are chosen on the DEV template split ONLY and then applied
    unchanged to the TEST split, whose templates were never looked at.
    Reporting a similarity number without this split is how a matcher looks
    good on templates it has effectively memorised.

Two methods compared:
  geometry  — hand-built rule-position matching (~8 tuned constants)
  embedding — a pretrained vision model, cosine similarity, ZERO tuned
              constants (the user explicitly does not want a CV-parameter
              treadmill)

Usage: python3 fingerprint_eval.py <struct_eval_dir> [--model facebook/dinov2-base]
"""
import argparse, itertools, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import template_id as tid  # noqa: E402


def _pr_curve(scores, labels):
    """Average precision + best-F1 threshold."""
    order = np.argsort(-np.asarray(scores))
    y = np.asarray(labels)[order]
    tp = np.cumsum(y)
    fp = np.cumsum(1 - y)
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / max(y.sum(), 1)
    ap = float(np.sum(np.diff(np.concatenate([[0], rec])) * prec))
    f1 = 2 * prec * rec / np.maximum(prec + rec, 1e-9)
    b = int(np.argmax(f1))
    return {"ap": round(ap, 3), "best_f1": round(float(f1[b]), 3),
            "thr": round(float(np.asarray(scores)[order][b]), 4),
            "prec_at_best": round(float(prec[b]), 3),
            "rec_at_best": round(float(rec[b]), 3)}


def _apply(scores, labels, thr):
    s, y = np.asarray(scores), np.asarray(labels)
    pred = s >= thr
    tp = int((pred & (y == 1)).sum()); fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    p = tp / max(tp + fp, 1); r = tp / max(tp + fn, 1)
    return {"precision": round(p, 3), "recall": round(r, 3),
            "f1": round(2 * p * r / max(p + r, 1e-9), 3),
            "tp": tp, "fp": fp, "fn": fn}


def embed_all(forms, model_name):
    """Pretrained-embedding fingerprints. No tuned parameters."""
    import torch
    from transformers import AutoImageProcessor, AutoModel
    from PIL import Image
    proc = AutoImageProcessor.from_pretrained(model_name)
    mdl = AutoModel.from_pretrained(model_name).eval()
    out = {}
    with torch.no_grad():
        for name, d in forms.items():
            page = next(iter(sorted((d / "pages").glob("page_*.png"))), None)
            if page is None:
                continue
            im = Image.open(page).convert("RGB")
            v = mdl(**proc(images=im, return_tensors="pt")).last_hidden_state
            v = v.mean(1)[0]                      # mean-pooled patch tokens
            out[name] = (v / v.norm()).numpy()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--model", default="facebook/dinov2-base")
    ap.add_argument("--skip-embed", action="store_true")
    a = ap.parse_args()
    root = Path(a.root)
    man = json.loads((root / "manifest.json").read_text())
    forms = {m["name"]: root / m["name"] for m in man if (root / m["name"]).exists()}
    tid_of = {m["name"]: m["template_id"] for m in man}
    split_of = {m["name"]: m["split"] for m in man}

    print(f"forms: {len(forms)}  template-pages: {len(set(tid_of.values()))}")

    # ── geometry fingerprints
    geo = {}
    for name, d in forms.items():
        try:
            geo[name] = tid.fingerprint(d / "input.pdf")
        except Exception as e:  # noqa: BLE001
            print(f"  !! geo {name}: {e}")

    emb = {} if a.skip_embed else embed_all(forms, a.model)

    def pairs(split):
        ns = [n for n in forms if split_of[n] == split]
        for x, y in itertools.combinations(sorted(ns), 2):
            yield x, y, int(tid_of[x] == tid_of[y])

    results = {}
    for method in (["geometry"] + ([] if a.skip_embed else ["embedding"])):
        res = {}
        for split in ("dev", "test"):
            sc, lb = [], []
            for x, y, lab in pairs(split):
                if method == "geometry":
                    if x not in geo or y not in geo:
                        continue
                    s = tid.geometry_similarity(geo[x], geo[y])
                else:
                    if x not in emb or y not in emb:
                        continue
                    s = float(np.dot(emb[x], emb[y]))
                sc.append(s); lb.append(lab)
            res[split] = {"n_pairs": len(sc), "n_pos": int(sum(lb)),
                          "scores": sc, "labels": lb}
        dev = _pr_curve(res["dev"]["scores"], res["dev"]["labels"])
        applied = _apply(res["test"]["scores"], res["test"]["labels"], dev["thr"])
        results[method] = {"dev_curve": dev, "test_at_dev_threshold": applied,
                           "test_curve": _pr_curve(res["test"]["scores"],
                                                   res["test"]["labels"]),
                           "n_pairs": {k: res[k]["n_pairs"] for k in res},
                           "n_pos": {k: res[k]["n_pos"] for k in res}}

    print("\n" + "=" * 72)
    for m, r in results.items():
        print(f"\n## {m}")
        print(f"   pairs dev={r['n_pairs']['dev']} (pos {r['n_pos']['dev']}) "
              f"test={r['n_pairs']['test']} (pos {r['n_pos']['test']})")
        print(f"   DEV  : AP {r['dev_curve']['ap']}  bestF1 {r['dev_curve']['best_f1']} "
              f"@thr {r['dev_curve']['thr']}")
        t = r["test_at_dev_threshold"]
        print(f"   TEST (held-out templates, dev threshold applied unchanged):")
        print(f"          precision {t['precision']}  recall {t['recall']}  "
              f"F1 {t['f1']}   (tp {t['tp']} fp {t['fp']} fn {t['fn']})")
        print(f"   TEST ceiling (if threshold were tuned on test): "
              f"AP {r['test_curve']['ap']} bestF1 {r['test_curve']['best_f1']}")
    (root.parent / "fingerprint_eval.json").write_text(json.dumps(
        {m: {k: v for k, v in r.items()} for m, r in results.items()}, indent=2))


if __name__ == "__main__":
    main()
