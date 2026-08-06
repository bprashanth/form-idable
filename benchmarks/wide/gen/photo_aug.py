#!/usr/bin/env python3
"""Phone-camera degradation — the real submission channel.

The partner's actual uploads are not scans. They are photos taken on a phone in
the field: the page is a trapezoid, the paper bows, a thumb intrudes at the
edge, one side is in shadow, and a second sheet or a table top is visible
behind. `formgen2.degrade()` (augraphy) models a SCANNER; none of this.

Everything here is derived from the partner's own images:
  eval_15 (WhatsApp)   — page photographed at an angle, second sheet behind
  eval_16 (segmented)  — thumb visible at the left edge, crumpled paper
  eval_17 (segmented)  — strong trapezoid, marginal annotation outside the form
  eval_18 (form1)      — PENCIL: light grey, low contrast, not ink
  eval_21 (form4)      — page bow, ~90% empty rows

Applied to the rendered page BEFORE augraphy, so paper texture and ink bleed
land on top of the geometry, as they do physically.
"""
import math, random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

try:
    import cv2
except ImportError:
    cv2 = None


def perspective(img, rng, strength=0.06):
    """Photograph the page off-axis: corners move independently."""
    if cv2 is None:
        return img
    w, h = img.size
    s = strength
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[rng.uniform(0, s) * w, rng.uniform(0, s) * h],
                      [w - rng.uniform(0, s) * w, rng.uniform(0, s) * h],
                      [w - rng.uniform(0, s) * w, h - rng.uniform(0, s) * h],
                      [rng.uniform(0, s) * w, h - rng.uniform(0, s) * h]])
    M = cv2.getPerspectiveTransform(src, dst)
    a = cv2.warpPerspective(np.array(img.convert("RGB")), M, (w, h),
                            borderValue=(238, 236, 232))
    return Image.fromarray(a)


def curvature(img, rng, amp=0.02):
    """Paper does not lie flat — a page held or resting on a curved surface
    bows, which is why printed rules in the partner's photos are not straight."""
    if cv2 is None:
        return img
    a = np.array(img.convert("RGB"))
    h, w = a.shape[:2]
    A = amp * h * rng.uniform(0.4, 1.0)
    phase = rng.uniform(0, math.pi)
    ys, xs = np.indices((h, w), dtype=np.float32)
    ys = ys + A * np.sin(2 * math.pi * xs / max(w, 1) + phase)
    return Image.fromarray(cv2.remap(a, xs, ys, cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_REPLICATE))


def finger(img, rng):
    """A thumb holding the sheet, as in the partner's segmented_000."""
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    side = rng.choice("lrb")
    skin = rng.choice([(196, 150, 118), (168, 124, 96), (142, 102, 78),
                       (214, 176, 146)])
    fw, fh = rng.uniform(0.05, 0.11) * w, rng.uniform(0.10, 0.20) * h
    if side == "l":
        cx, cy = -fw * 0.2, rng.uniform(0.25, 0.75) * h
    elif side == "r":
        cx, cy = w - fw * 0.8, rng.uniform(0.25, 0.75) * h
    else:
        cx, cy = rng.uniform(0.2, 0.8) * w, h - fh * 0.75
    d.rounded_rectangle([cx, cy, cx + fw, cy + fh], radius=int(fw * 0.45),
                        fill=(*skin, 255))
    d.rounded_rectangle([cx + fw * 0.18, cy + fh * 0.06,
                         cx + fw * 0.72, cy + fh * 0.30],
                        radius=int(fw * 0.2), fill=(*skin, 90))
    return img.filter(ImageFilter.GaussianBlur(0.4))


def directional_shadow(img, rng):
    """Hand/phone shadow across part of the sheet."""
    w, h = img.size
    m = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(m)
    ang = rng.uniform(0, math.pi)
    cx, cy = rng.uniform(0.2, 0.8) * w, rng.uniform(0.2, 0.8) * h
    L = max(w, h)
    dx, dy = math.cos(ang) * L, math.sin(ang) * L
    md.polygon([(cx - dx, cy - dy), (cx + dy, cy - dx),
                (cx + dx + dy, cy + dy - dx), (cx + dx, cy + dy)],
               fill=rng.randint(40, 105))
    m = m.filter(ImageFilter.GaussianBlur(rng.uniform(w * .02, w * .07)))
    return Image.composite(Image.new("RGB", (w, h), (58, 56, 54)),
                           img.convert("RGB"), m)


def background(img, rng):
    """Put the sheet on a surface: table, cloth, or another sheet behind."""
    w, h = img.size
    pad = int(min(w, h) * rng.uniform(0.02, 0.07))
    bg_kind = rng.random()
    if bg_kind < 0.45:
        base = rng.choice([(96, 74, 52), (120, 96, 66), (66, 60, 56)])   # table
    elif bg_kind < 0.75:
        base = rng.choice([(180, 176, 168), (208, 204, 196)])            # paper
    else:
        base = rng.choice([(48, 52, 60), (30, 34, 38)])                  # dark
    canvas = Image.new("RGB", (w + 2 * pad, h + 2 * pad), base)
    n = np.array(canvas, dtype=np.int16)
    n += np.random.RandomState(rng.randint(0, 1 << 30)).randint(-9, 9, n.shape)
    canvas = Image.fromarray(np.uint8(np.clip(n, 0, 255)))
    canvas.paste(img.convert("RGB"), (pad, pad))
    return canvas


def apply(img, rng, level="field"):
    """Full phone-photo pipeline. level: 'mild' | 'field' | 'rough'."""
    p = {"mild": (0.03, 0.010, 0.05, 0.25, 0.35),
         "field": (0.06, 0.020, 0.25, 0.55, 0.70),
         "rough": (0.10, 0.032, 0.45, 0.80, 0.85)}[level]
    warp, bow, fing, shade, bg = p
    out = img.convert("RGB")
    if rng.random() < 0.85:
        out = perspective(out, rng, strength=warp)
    if rng.random() < 0.70:
        out = curvature(out, rng, amp=bow)
    if rng.random() < bg:
        out = background(out, rng)
    if rng.random() < shade:
        out = directional_shadow(out, rng)
    if rng.random() < fing:
        out = finger(out, rng)
    return out
