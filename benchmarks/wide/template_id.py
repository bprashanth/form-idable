#!/usr/bin/env python3
"""Template fingerprinting — "have we seen this form's layout before?"

Two filled copies of the same template share their PRINTED layer (rules,
labels) and differ only in ink. So a fingerprint built from the printed
structure identifies the template regardless of what was written on it.

Signature = the normalised positions of long horizontal/vertical rules,
plus coarse shape stats. Handwriting does not produce page-spanning straight
lines, so the signature is stable across fills.

Matching runs locally (no model, no network) — only the one-time template
INDUCTION needs a strong model, so the privacy claim stays: one form per
template type leaves the device, the rest never do.

Usage:
  python3 template_id.py fingerprint <image_or_pdf> [...]
  python3 template_id.py cluster <dir_of_form_dirs>
"""
import json, math, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

try:
    import cv2
except ImportError:
    cv2 = None


def _load_gray(path: Path, max_dim=1400):
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        import fitz
        doc = fitz.open(str(p))
        pm = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
        doc.close()
    else:
        img = Image.open(p).convert("RGB")
    g = img.convert("L")
    s = max_dim / max(g.size)
    if s < 1:
        g = g.resize((int(g.width * s), int(g.height * s)), Image.LANCZOS)
    return np.asarray(g)


def _peaks(profile, min_frac=0.18, min_gap=3):
    """Locally-prominent peaks of a projection profile.

    An absolute coverage threshold fails on real forms: printed rules are often
    THIN and LIGHT (the partner's invoices, the pencil phenology sheet), so a
    fixed cut either misses them or floods on dark scans. Scale the threshold
    to the profile's own maximum and keep locally-dominant positions instead.
    """
    if profile.max() <= 0:
        return []
    p = profile / profile.max()
    thr = max(min_frac, float(np.median(p) + 3.0 * p.std()))
    idx = [i for i in range(len(p)) if p[i] >= thr]
    out, last = [], -99
    for i in idx:
        if i - last >= min_gap:
            out.append(i)
            last = i
        elif out and p[i] > p[out[-1]]:
            out[-1] = i
            last = i
    return out


def _rule_positions(gray):
    """Normalised positions of long horizontal and vertical rules."""
    if cv2 is None:
        return _rule_positions_numpy(gray)
    # local contrast normalisation first — phone photos have strong lighting
    # gradients that swamp a global threshold
    gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 25, 10)
    h, w = bw.shape
    out = {}
    for axis, key in ((1, "h"), (0, "v")):
        span = w if axis == 1 else h
        # keep only strokes that run a long way along `axis`
        k = (max(15, span // 20), 1) if axis == 1 else (1, max(15, span // 20))
        ker = cv2.getStructuringElement(cv2.MORPH_RECT, k)
        line = cv2.morphologyEx(bw, cv2.MORPH_OPEN, ker)
        prof = (line.sum(axis=axis) / 255.0) / span
        n = h if axis == 1 else w
        out[key] = sorted(float(i / n) for i in _peaks(prof))
    return out


def _longest_true_run(values):
    """Length of the longest contiguous True run in a one-dimensional mask."""
    false = np.flatnonzero(~values)
    if not len(false):
        return len(values)
    boundaries = np.concatenate(([-1], false, [len(values)]))
    return int(np.max(np.diff(boundaries) - 1))


def _bridge_gaps(mask, axis, gap=2):
    """Join anti-aliasing pinholes without joining neighbouring text glyphs."""
    out = mask.copy()
    shifted = np.moveaxis(out, axis, 0)
    for index in range(shifted.shape[0]):
        line = shifted[index]
        false = np.flatnonzero(~line)
        if len(false) == 0:
            continue
        numeric = line.astype(np.int8)
        starts = np.flatnonzero(np.diff(np.concatenate(([1], numeric))) == -1)
        ends = np.flatnonzero(np.diff(np.concatenate((numeric, [1]))) == 1)
        for start, end in zip(starts, ends):
            if start > 0 and end < len(line) and end - start <= gap:
                line[start:end] = True
    return np.moveaxis(shifted, 0, axis)


def _rule_positions_numpy(gray):
    """Dependency-free printed-rule detector using local contrast and run length.

    Dense handwriting can have a high projection sum, but it rarely creates a
    near-contiguous stroke over a substantial fraction of the page.  Longest
    run is therefore a safer signal than raw ink coverage for this fallback.
    """
    image = Image.fromarray(gray.astype(np.uint8), mode="L")
    radius = max(4, min(gray.shape) // 90)
    local_mean = np.asarray(image.filter(ImageFilter.BoxBlur(radius)), dtype=np.int16)
    source = gray.astype(np.int16)
    ink = ((local_mean - source) >= 5) & (source < 252)
    h, w = ink.shape

    def opening_profile(axis, span):
        oriented = ink if axis == 1 else ink.T
        window = max(15, span // 20)
        cumulative = np.pad(np.cumsum(oriented, axis=1, dtype=np.int32),
                            ((0, 0), (1, 0)))
        sums = cumulative[:, window:] - cumulative[:, :-window]
        # A rule may have anti-aliasing gaps and intersections; text almost
        # never keeps 75% of a long window dark.
        return (sums >= 0.75 * window).mean(axis=1)

    def local_peaks(profile):
        threshold = max(0.03, 0.2 * float(profile.max()))
        candidates = [i for i, value in enumerate(profile)
                      if value >= threshold
                      and value >= profile[max(0, i - 2):min(len(profile), i + 3)].max()]
        out = []
        for index in candidates:
            if not out or index - out[-1] >= 3:
                out.append(index)
            elif profile[index] > profile[out[-1]]:
                out[-1] = index
        return out

    horizontal = opening_profile(axis=1, span=w)
    vertical = opening_profile(axis=0, span=h)
    return {
        "h": sorted(float(i / h) for i in local_peaks(horizontal)),
        "v": sorted(float(i / w) for i in local_peaks(vertical)),
    }


def _dedupe(vals, tol=0.006):
    """Collapse adjacent detections of the same physical rule."""
    out = []
    for v in vals:
        if not out or v - out[-1] > tol:
            out.append(v)
        else:
            out[-1] = (out[-1] + v) / 2
    return out


def fingerprint(path):
    g = _load_gray(path)
    r = _rule_positions(g)
    hs, vs = _dedupe(r["h"]), _dedupe(r["v"])
    return {"path": str(path), "aspect": round(g.shape[1] / g.shape[0], 3),
            "n_h": len(hs), "n_v": len(vs), "h": [round(x, 4) for x in hs],
            "v": [round(x, 4) for x in vs]}


def _align_score(a, b, tol=0.018):
    """Best agreement between two rule sets under a 1-D similarity transform.

    Two photos of the same template are cropped and zoomed differently, so raw
    normalised positions do not line up. Search scale+offset the way a 1-D
    RANSAC would: every pair of rules in `a` mapped onto every pair in `b`
    proposes a transform; keep the one with the most inliers.
    """
    if len(a) < 2 or len(b) < 2:
        return 0.0
    # Exhaustive rule-pair RANSAC is quartic and becomes impractical on dense
    # forms. Six evenly spaced anchors retain page extent and internal rules
    # while bounding each comparison to at most 225 transforms.
    def anchors(values, limit=6):
        if len(values) <= limit:
            return values
        indices = sorted({round(i * (len(values) - 1) / (limit - 1))
                          for i in range(limit)})
        return [values[index] for index in indices]

    def inliers(mapped, target):
        hits = i = j = 0
        while i < len(mapped) and j < len(target):
            delta = mapped[i] - target[j]
            if abs(delta) <= tol:
                hits += 1
                i += 1
                j += 1
            elif delta < 0:
                i += 1
            else:
                j += 1
        return hits

    aa, bb = anchors(a), anchors(b)
    best = 0.0
    for i in range(len(aa)):
        for j in range(i + 1, len(aa)):
            da = aa[j] - aa[i]
            if da < 0.05:
                continue
            for p in range(len(bb)):
                for q in range(p + 1, len(bb)):
                    db = bb[q] - bb[p]
                    if db < 0.05:
                        continue
                    s = db / da
                    if not (0.75 < s < 1.33):        # implausible zoom
                        continue
                    off = bb[p] - s * aa[i]
                    hit = inliers([s * x + off for x in a], b)
                    best = max(best, hit / max(len(a), len(b)))
    return best


def geometry_similarity(f1, f2):
    """Layout similarity in [0,1] from printed rules alone. Column structure
    (vertical rules) outweighs row count: the number of ROWS varies with how
    much the field worker wrote; column positions are fixed by the template."""
    if min(f1["aspect"], f2["aspect"]) / max(f1["aspect"], f2["aspect"]) < 0.80:
        return 0.0
    return round(0.6 * _align_score(f1["v"], f2["v"])
                 + 0.4 * _align_score(f1["h"], f2["h"]), 3)


def text_similarity(t1: set, t2: set):
    """Jaccard over PRINTED label vocabulary — the decisive channel.

    Measured on the partner's own forms: two copies of one template score
    0.667, two sheets from one project 0.309, everything else <=0.073.
    Geometry alone produced three false positives at >0.75 that this rejects.

    Build these sets from the LOCAL VLM's own extraction output, not from
    tesseract. Tested on eval_23/eval_24 (two copies of one invoice template):
    tesseract's `conf>=75` filter does cleanly isolate printed labels WITHIN an
    image, but its coverage swings with photo quality (13 high-conf tokens on
    one copy, 5 on the other, 0 on the pencil phenology sheet), so the two sets
    intersect on a single word. The 0.667 separation above was measured on VLM
    transcriptions. Since we run the local model for extraction anyway, its
    output is a free fingerprint and stays on-device.

    Robustness note: handwriting differs between two copies of a template, so
    its tokens land in the UNION but never the INTERSECTION. Handwriting noise
    can dilute a true match slightly; it cannot manufacture a false one.
    """
    if not t1 or not t2:
        return 0.0
    return round(len(t1 & t2) / len(t1 | t2), 3)


def match(f1, t1, f2, t2):
    """Combined verdict. -> (label, score)

    text >= 0.40                      : same template
    0.15 <= text < 0.40 and geom>=0.6 : same template, lower confidence
    otherwise                         : different (fall back to general path)
    """
    txt = text_similarity(t1, t2)
    geo = geometry_similarity(f1, f2)
    if txt >= 0.40:
        return "same", round(0.7 * txt + 0.3 * geo, 3)
    if txt >= 0.15 and geo >= 0.60:
        return "same_low_conf", round(0.7 * txt + 0.3 * geo, 3)
    return "different", round(0.7 * txt + 0.3 * geo, 3)


# kept for the CLI clustering demo
def similarity(f1, f2):
    return geometry_similarity(f1, f2)


def cluster(root: Path, thresh=0.62):
    forms = sorted(p for p in root.iterdir() if (p / "input.pdf").exists())
    fps = {}
    for f in forms:
        try:
            fps[f.name] = fingerprint(f / "input.pdf")
        except Exception as e:  # noqa: BLE001
            print(f"  !! {f.name}: {e}")
    names = sorted(fps)
    print(f"\nfingerprinted {len(names)} forms "
          f"(rules: h/v)\n")
    for n in names:
        print(f"  {n:9s} {fps[n]['n_h']:>3d}h {fps[n]['n_v']:>3d}v  aspect {fps[n]['aspect']}")
    print("\npairs above threshold (same template candidates):")
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            s = similarity(fps[a], fps[b])
            if s >= thresh:
                pairs.append((s, a, b))
    for s, a, b in sorted(pairs, reverse=True):
        print(f"  {s:.3f}  {a}  <->  {b}")
    if not pairs:
        print("  (none)")
    (root.parent / "template_fingerprints.json").write_text(json.dumps(fps, indent=2))
    return fps


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "fingerprint":
        for p in sys.argv[2:]:
            print(json.dumps(fingerprint(Path(p)))[:200])
    else:
        cluster(Path(sys.argv[2]))
