#!/usr/bin/env python3
"""Extract a real-handwriting glyph bank from NIST SD-19 (by_class).

SD-19 holds isolated hand-PRINTED characters from ~3,600 writers — exactly the
kind of ink that fills the numeric and single-letter code cells of field
datasheets (the cells cheap OCR models get wrong). We crop each sample to its
ink bounding box, normalise height, and store it as an 8-bit ink/alpha map so
formgen can composite it into a form cell with any ink colour.

Layout preserved: `hsf_N` partitions are writer cohorts, so a generated form
can draw all its glyphs from ONE cohort and look like one person filled it.

Output: glyphs/<hsf_N>/<charname>/NNN.png   (mode 'L', ink=255, height=64)

Usage: python3 build_glyphbank.py <sd19_by_class_dir> <out_dir> [per_class]
"""
import random, sys
from pathlib import Path

import numpy as np
from PIL import Image

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
PER = int(sys.argv[3]) if len(sys.argv) > 3 else 60
H = 64

# SD-19 class dirs are hex ASCII codes. Filenames can't distinguish 'a' from
# 'A' on case-insensitive stores, so lowercase letters get a '_lc' suffix.
def charname(ch):
    if ch.isdigit():
        return f"d{ch}"
    if ch.isupper():
        return f"u{ch}"
    return f"l{ch.upper()}"


def extract(path):
    im = Image.open(path).convert("L")
    a = 255 - np.asarray(im, dtype=np.uint8)          # ink = high
    ys, xs = np.where(a > 60)
    if len(xs) < 8:
        return None
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = a[y0:y1, x0:x1]
    h, w = crop.shape
    if h < 4 or w < 2:
        return None
    new_w = max(2, int(round(w * H / h)))
    return Image.fromarray(crop).resize((new_w, H), Image.LANCZOS)


def main():
    rng = random.Random(0)
    classes = sorted(p for p in SRC.iterdir() if p.is_dir())
    total = 0
    for cdir in classes:
        try:
            ch = chr(int(cdir.name, 16))
        except ValueError:
            continue
        if not ch.isalnum():
            continue
        cname = charname(ch)
        for hsf in sorted(cdir.glob("hsf_*")):
            if hsf.suffix == ".mit" or not hsf.is_dir():
                continue
            files = sorted(hsf.glob("*.png"))
            if not files:
                continue
            picks = rng.sample(files, min(PER, len(files)))
            dst_dir = OUT / hsf.name / cname
            dst_dir.mkdir(parents=True, exist_ok=True)
            n = 0
            for f in picks:
                g = extract(f)
                if g is None:
                    continue
                g.save(dst_dir / f"{n:03d}.png")
                n += 1
            total += n
        print(f"{cname}: done", flush=True)
    print(f"glyph bank: {total} glyphs -> {OUT}")


if __name__ == "__main__":
    main()
