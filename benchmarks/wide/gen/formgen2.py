#!/usr/bin/env python3
"""Formgen v2 — ecology/field-survey form generator with REAL handwriting ink.

Round-1 (`formgen.py`) used handwriting fonts; models scored 0.93+ on it but
only ~0.70-0.80 on real scans. The gap is ink, not layout. v2 changes:

  * **Real glyphs.** Digits and single-letter code cells — exactly the cells
    cheap models misread — are composited from NIST SD-19 hand-printed
    samples (`assets/glyphs/`, built by build_glyphbank.py). One writer cohort
    per form, so a sheet looks like one person filled it.
  * **Real degradation.** Augraphy pipelines (bleed-through, dirty rollers,
    photocopy, folds, shadows) instead of blur+JPEG.
  * **Observed failure modes.** Corrections struck and rewritten, ditto lines
    down a column, circled values, asterisk footnote markers, ink blots,
    rotated marginal notes, row-spanning annotations, NA dashes, non-sequential
    IDs, partially-filled sheets, shaded column groups / alternating rows.
  * **Ecology archetypes** matching the real partner domain: phenology trail
    transects, growth & survival monitoring (printed + handwritten value
    pairs), litter biomass, germination code grids, regeneration tallies,
    GBH plot surveys, soil microclimate.

Goldens stay exact by construction — every injector records what it wrote.

Usage:
  python3 formgen2.py <out_root> <seed> [only_form] [--hard] [--count N]
"""
import math, random, sys
from pathlib import Path

import fitz
import numpy as np
import openpyxl
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE   = Path(__file__).parent
ASSETS = HERE.parent / "assets"
FONTS  = ASSETS / "fonts"
GLYPHS = ASSETS / "glyphs"
PRINT_FONT      = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PRINT_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PRINT_SERIF     = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
PRINT_SERIF_B   = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

CURSIVE_FONTS = [FONTS / f for f in [
    "Kalam-Regular.ttf", "Caveat.ttf", "PatrickHand.ttf", "Mynerve.ttf",
    "GochiHand.ttf", "ShadowsIntoLight.ttf", "Kalam-Light.ttf",
    "IndieFlower.ttf", "HomemadeApple.ttf", "ReenieBeanie.ttf",
]]

PORTRAIT, LANDSCAPE = (1488, 2105), (2105, 1488)
# Fraction of a table's rows that carry data. Mutable single-element list so
# generate() can set it per form without threading a parameter through every
# archetype signature. 1.0 == the old dense behaviour.
FILL_FRAC = [1.0]
INKS = [(20, 24, 84), (16, 16, 40), (28, 24, 120), (10, 10, 10), (40, 30, 90),
        (12, 40, 96), (30, 30, 60)]


# ── real-ink writer ───────────────────────────────────────────────
def _charname(ch):
    if ch.isdigit(): return f"d{ch}"
    if ch.isupper(): return f"u{ch}"
    return f"l{ch.upper()}"


PENCIL_INKS = [(104, 104, 110), (122, 120, 124), (88, 88, 96), (136, 134, 138)]


class Writer:
    """One 'person': a writer cohort of real glyphs + a cursive font for prose,
    one ink colour, one baseline slant, consistent sizing habits."""

    def __init__(self, rng, cohort=None, prose="hybrid", medium=None):
        self.rng = rng
        cohorts = sorted(p.name for p in GLYPHS.iterdir()) if GLYPHS.exists() else []
        self.cohort = cohort or (rng.choice(cohorts) if cohorts else None)
        # PENCIL is a real recording medium in this domain — the partner's
        # phenology sheet (eval_18) is entirely pencil: light grey, low
        # contrast, nothing like the blue/black ink the corpus had.
        self.medium = medium or ("pencil" if rng.random() < 0.22 else "ink")
        self.ink = rng.choice(PENCIL_INKS if self.medium == "pencil" else INKS)
        self.slant = rng.uniform(-4.0, 4.0)
        self.weight = (rng.uniform(0.40, 0.68) if self.medium == "pencil"
                       else rng.uniform(0.85, 1.25))   # stroke darkness
        self.prose_mode = prose                     # "glyph" | "hybrid"
        self.font_path = str(rng.choice(CURSIVE_FONTS))
        self._fcache, self._gcache = {}, {}

    # -- glyph access
    def _glyphs(self, ch):
        key = _charname(ch)
        if key not in self._gcache:
            d = GLYPHS / self.cohort / key if self.cohort else None
            files = sorted(d.glob("*.png")) if d and d.exists() else []
            self._gcache[key] = files
        return self._gcache[key]

    def _glyph_img(self, ch, h):
        files = self._glyphs(ch)
        if not files:
            return None
        f = files[self.rng.randrange(len(files))]
        if f not in self._fcache:
            self._fcache[f] = Image.open(f).convert("L")
        g = self._fcache[f]
        w = max(2, int(g.width * h / g.height))
        return g.resize((w, h), Image.LANCZOS)

    def _font(self, size):
        k = int(size)
        if k not in self._fcache:
            self._fcache[k] = ImageFont.truetype(self.font_path, k)
        return self._fcache[k]

    # -- symbol strokes (SD-19 has no punctuation)
    def _symbol(self, img, x, y, ch, size):
        d = ImageDraw.Draw(img)
        c = (*self.ink, int(225 * self.weight) % 256 or 225)
        r = self.rng
        if ch == ".":
            rr = size * 0.055
            cx, cy = x + size * 0.10, y + size * 0.92
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c)
            return size * 0.26
        if ch == ",":
            cx, cy = x + size * 0.10, y + size * 0.90
            d.line([(cx, cy), (cx - size * 0.06, cy + size * 0.16)], fill=c, width=3)
            return size * 0.26
        if ch in "-_":
            d.line([(x + size * 0.06, y + size * 0.62),
                    (x + size * 0.52, y + size * 0.60 + r.uniform(-2, 2))], fill=c, width=3)
            return size * 0.60
        if ch == "/":
            d.line([(x + size * 0.06, y + size * 1.0), (x + size * 0.42, y + size * 0.05)],
                   fill=c, width=3)
            return size * 0.50
        if ch == "*":
            cx, cy = x + size * 0.22, y + size * 0.30
            rr = size * 0.17
            for a in (0, 60, 120):
                dx, dy = rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a))
                d.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=c, width=2)
            return size * 0.48
        if ch in "()":
            k = 1 if ch == "(" else -1
            d.arc([x, y + size * 0.05, x + size * 0.45, y + size * 1.0],
                  start=90 if k > 0 else 270, end=270 if k > 0 else 90, fill=c, width=3)
            return size * 0.36
        if ch == ":":
            for yy in (0.35, 0.80):
                rr = size * 0.05
                cx, cy = x + size * 0.12, y + size * yy
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c)
            return size * 0.26
        if ch == "+":
            cx, cy = x + size * 0.24, y + size * 0.58
            rr = size * 0.16
            d.line([(cx - rr, cy), (cx + rr, cy)], fill=c, width=3)
            d.line([(cx, cy - rr), (cx, cy + rr)], fill=c, width=3)
            return size * 0.52
        if ch == " ":
            return size * 0.30
        return size * 0.30

    def _paste_glyph(self, img, g, x, y, size):
        ang = self.slant + self.rng.uniform(-3.5, 3.5)
        tile = Image.new("RGBA", g.size, (0, 0, 0, 0))
        alpha = g.point(lambda v: min(255, int(v * self.weight)))
        tile.putalpha(alpha)
        tile = Image.merge("RGBA", (*[Image.new("L", g.size, c) for c in self.ink],
                                    tile.getchannel("A")))
        tile = tile.rotate(ang, resample=Image.BICUBIC, expand=True)
        jy = y + self.rng.uniform(-0.05, 0.05) * size
        img.alpha_composite(tile, (int(x), int(jy)))

    def text(self, img, xy, s, size=44, max_w=None, force=None):
        """Write a string. Real SD-19 glyphs for alphanumerics (the 'glyph'
        path); cursive font for prose when prose_mode is hybrid and the string
        looks like prose. Returns the advance width used."""
        s = str(s)
        use_font = False
        if force == "font":
            use_font = True
        elif force != "glyph" and self.prose_mode == "hybrid":
            letters = sum(c.isalpha() for c in s)
            use_font = letters >= 4 and " " in s.strip()   # multi-word prose
        if use_font:
            return self._text_font(img, xy, s, size, max_w)
        return self._text_glyph(img, xy, s, size, max_w)

    def _measure_glyph(self, s, size):
        w = 0
        for ch in s:
            if ch.isalnum() and self._glyphs(ch):
                g = self._glyph_img(ch, int(size))
                w += (g.width if g else size * 0.5) + size * 0.06
            else:
                w += size * 0.35
        return w

    def _text_glyph(self, img, xy, s, size, max_w=None):
        if max_w:
            while self._measure_glyph(s, size) > max_w and size > 16:
                size *= 0.9
        x, y = xy
        x0 = x
        for ch in s:
            if ch.isalnum() and self._glyphs(ch):
                h = int(size * self.rng.uniform(0.92, 1.08))
                if ch.islower() and ch not in "bdfhklt":
                    h = int(h * 0.72)                     # x-height
                g = self._glyph_img(ch, max(6, h))
                if g is None:
                    x += size * 0.4; continue
                yy = y + (size - h) * (0.85 if ch.islower() else 0.0)
                self._paste_glyph(img, g, x, yy, size)
                x += g.width + size * self.rng.uniform(0.02, 0.11)
            else:
                x += self._symbol(img, x, y, ch, size)
        return x - x0

    def _text_font(self, img, xy, s, size, max_w=None):
        if max_w:
            f = self._font(int(size))
            while f.getbbox(s)[2] > max_w and size > 16:
                size *= 0.9
                f = self._font(int(size))
        x, y = xy
        x0 = x
        for ch in s:
            f = self._font(int(size * self.rng.uniform(0.93, 1.07)))
            bb = f.getbbox(ch)
            cw = max(1, bb[2] - bb[0]) if ch.strip() else int(size * 0.30)
            if ch.strip():
                pad = 8
                tile = Image.new("RGBA", (cw + 2 * pad, int(size * 2) + 2 * pad), (0, 0, 0, 0))
                ImageDraw.Draw(tile).text((pad - bb[0], pad), ch, font=f,
                                          fill=(*self.ink, self.rng.randint(195, 245)))
                tile = tile.rotate(self.slant + self.rng.uniform(-2, 2),
                                   resample=Image.BICUBIC, expand=True)
                img.alpha_composite(tile, (int(x - pad),
                                           int(y + self.rng.uniform(-.04, .04) * size - pad)))
            x += cw + self.rng.uniform(-1, 2.5)
        return x - x0

    def measure(self, s, size):
        return self._measure_glyph(str(s), size)

    # -- marks
    def stroke(self, img, pts, width=3, alpha=230):
        d = ImageDraw.Draw(img)
        j = [(x + self.rng.uniform(-2, 2), y + self.rng.uniform(-2, 2)) for x, y in pts]
        d.line(j, fill=(*self.ink, alpha), width=width, joint="curve")

    def tick(self, img, cx, cy, size=18):
        s = size * self.rng.uniform(0.8, 1.3)
        self.stroke(img, [(cx - s * .5, cy), (cx - s * .1, cy + s * .45),
                          (cx + s * .7, cy - s * .6)], width=3)

    def dot(self, img, cx, cy):
        r = self.rng.uniform(3, 5.5)
        ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r],
                                    fill=(*self.ink, 235))

    def strike(self, img, x0, x1, cy):
        n = 6
        self.stroke(img, [(x0 + (x1 - x0) * i / n, cy + self.rng.uniform(-3, 3))
                          for i in range(n + 1)], width=3)

    def circle(self, img, box):
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = (x1 - x0) * .62, (y1 - y0) * .60
        pts = []
        for i in range(19):
            a = 2 * math.pi * i / 18
            pts.append((cx + rx * math.cos(a) + self.rng.uniform(-2, 2),
                        cy + ry * math.sin(a) + self.rng.uniform(-2, 2)))
        self.stroke(img, pts, width=3, alpha=210)

    def tally(self, img, cx, cy, n, h=32, gap=14):
        x = cx - (min(n, 12) * gap * 0.45)
        i = 0
        while i < n:
            grp = min(4, n - i)
            gx = x
            for _ in range(grp):
                jx = self.rng.uniform(-1.5, 1.5)
                self.stroke(img, [(gx + jx, cy - h / 2),
                                  (gx + jx + self.rng.uniform(-2, 2), cy + h / 2)], width=3)
                gx += gap
            i += grp
            if grp == 4 and i < n:
                self.stroke(img, [(x - 5, cy + h / 2 - 2), (gx - gap + 5, cy - h / 2 + 2)],
                            width=3)
                i += 1
            x = gx + int(gap * 1.6)

    def blot(self, img, cx, cy, r=14):
        d = ImageDraw.Draw(img)
        for _ in range(9):
            rr = r * self.rng.uniform(.35, 1.0)
            ox, oy = self.rng.uniform(-r * .5, r * .5), self.rng.uniform(-r * .5, r * .5)
            d.ellipse([cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr],
                      fill=(*self.ink, 245))


# ── page canvas ───────────────────────────────────────────────────
class Page:
    def __init__(self, size, serif=False):
        self.img = Image.new("RGBA", size, (255, 255, 253, 255))
        self.d = ImageDraw.Draw(self.img)
        self.W, self.H = size
        self.serif = serif

    def _pf(self, size, bold):
        if self.serif:
            return ImageFont.truetype(PRINT_SERIF_B if bold else PRINT_SERIF, size)
        return ImageFont.truetype(PRINT_FONT_BOLD if bold else PRINT_FONT, size)

    def ptext(self, xy, s, size=30, bold=False, anchor=None, fill=(15, 15, 15)):
        self.d.text(xy, s, font=self._pf(size, bold), fill=fill, anchor=anchor)

    def pwidth(self, s, size=30, bold=False):
        return self._pf(size, bold).getbbox(s)[2]

    def line(self, a, b, w=2, fill=(60, 60, 60)):
        self.d.line([a, b], fill=fill, width=w)

    def rect(self, box, w=2, fill=None, outline=(60, 60, 60)):
        self.d.rectangle(box, outline=outline, width=w, fill=fill)

    def shade(self, box, v=232):
        self.d.rectangle(box, fill=(v, v, v))


# ── cell specs -> golden ──────────────────────────────────────────
# ("text"|"num", s) ("print", s) ("pair", printed, hand) ("dot",) ("strike",)
# ("dash",) ("tick",) ("tally", n) ("blank",) ("star", s) ("circle", s)
# ("corr", wrong, right) ("na",)
def golden_of(spec):
    """Return list of golden cell values for one drawn cell (usually one)."""
    k = spec[0]
    if k in ("text", "num", "print"): return [spec[1]]
    if k == "pair":   return [spec[1], spec[2]]
    if k == "dot":    return ["0"]
    if k == "tick":   return ["X"]
    if k == "tally":  return [str(spec[1])]
    if k == "star":   return [f"{spec[1]}*"]
    if k == "circle": return [spec[1]]
    if k == "corr":   return [spec[2]]
    if k == "na":     return ["NA"]
    return [None]                                    # strike / dash / blank


def draw_cell(pg, w, box, spec, size=40, pair_split=0.5):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    k = spec[0]
    if k == "print":
        pg.ptext((x0 + 10, cy), spec[1], size=int(size * 0.62), anchor="lm")
    elif k in ("text", "num"):
        s = str(spec[1])
        wd = w.measure(s, size)
        w.text(pg.img, (max(x0 + 8, cx - wd / 2), cy - size * 0.55), s,
               size=size, max_w=x1 - x0 - 14)
    elif k == "pair":                       # printed value + handwritten value
        mid = x0 + (x1 - x0) * pair_split
        pg.ptext((x0 + 8, cy), str(spec[1]), size=int(size * 0.62), anchor="lm")
        hs = str(spec[2])
        wd = w.measure(hs, size)
        w.text(pg.img, (max(mid + 4, (mid + x1) / 2 - wd / 2), cy - size * 0.55), hs,
               size=size, max_w=x1 - mid - 10)
    elif k == "dot":
        w.dot(pg.img, cx + w.rng.uniform(-6, 6), cy + w.rng.uniform(-4, 4))
    elif k == "strike":
        w.strike(pg.img, x0 + 8, x1 - 8, cy)
    elif k == "dash":
        w.stroke(pg.img, [(cx - (x1 - x0) * .18, cy), (cx + (x1 - x0) * .18, cy)], width=3)
    elif k == "tick":
        w.tick(pg.img, cx, cy)
    elif k == "tally":
        w.tally(pg.img, cx, cy, spec[1])
    elif k == "na":
        s = "NA"
        wd = w.measure(s, size)
        w.text(pg.img, (cx - wd / 2, cy - size * 0.55), s, size=size, force="glyph")
    elif k == "star":
        s = f"{spec[1]}*"
        wd = w.measure(s, size)
        w.text(pg.img, (max(x0 + 6, cx - wd / 2), cy - size * 0.55), s,
               size=size, max_w=x1 - x0 - 10)
    elif k == "circle":
        s = str(spec[1])
        wd = w.measure(s, size)
        w.text(pg.img, (cx - wd / 2, cy - size * 0.55), s, size=size)
        w.circle(pg.img, (cx - wd / 2 - 8, y0 + 4, cx + wd / 2 + 8, y1 - 4))
    elif k == "corr":                        # struck wrong value + rewrite above
        wrong, right = str(spec[1]), str(spec[2])
        wd = w.measure(wrong, size * .95)
        sx = max(x0 + 6, cx - wd / 2)
        w.text(pg.img, (sx, cy - size * 0.45), wrong, size=size * .95)
        w.strike(pg.img, sx - 4, sx + wd + 4, cy + size * 0.05)
        w.text(pg.img, (sx + 4, y0 - size * 0.42), right, size=size * .82)


def draw_table(pg, w, top, left, right, col_fracs, header, rows, *,
               row_h=64, header_h=None, hand_size=40, header_size=24,
               shade_cols=(), alt_shade=False, group_every=None,
               spans=None, pair_split=0.5, header_rows=None, pair_cols=()):
    """Grid with printed header(s) + filled cells. Returns (bottom_y, golden).

    shade_cols  : column indices with a grey background (as in real forms)
    alt_shade   : shade every other data row
    group_every : draw a thick rule every N rows (block grouping)
    spans       : {row_index: text} — a row-spanning handwritten annotation
                  drawn across the table instead of that row's cells
    header_rows : optional list of extra printed header rows above `header`
                  as (text, col_start, col_end) tuples (grouped column titles)
    """
    W = right - left
    xs = [left]
    for f in col_fracs:
        xs.append(xs[-1] + f * W)
    xs[-1] = right
    header_h = header_h or row_h
    y = top
    golden = []

    if header_rows:
        gh = int(header_h * 0.62)
        for text, c0, c1 in header_rows:
            pg.line((xs[c0], y), (xs[c1 + 1], y))
            pg.ptext(((xs[c0] + xs[c1 + 1]) / 2, y + gh / 2), text,
                     size=header_size, bold=True, anchor="mm")
            for cc in (c0, c1 + 1):
                pg.line((xs[cc], y), (xs[cc], y + gh))
        golden.append([t for t, _, _ in header_rows])
        y += gh

    hy = y
    for i, h in enumerate(header):
        pg.ptext(((xs[i] + xs[i + 1]) / 2, y + header_h / 2), h,
                 size=header_size, bold=True, anchor="mm")
    # A "pair" column prints ONE merged label above two sub-cells (as on the
    # real sheets), so the golden header needs a blank for the second sub-cell
    # to stay aligned with the data rows.
    hdr = []
    for i, h in enumerate(header):
        hdr.append(h)
        if i in pair_cols:
            hdr.append(None)
    golden.append(hdr)
    y += header_h

    # Sparse fill. Every v2 training form was densely filled, so the model
    # learned "keep emitting rows" and over-produces on real sheets (measured:
    # recall 0.96-1.00 with precision 0.04-0.10 on sparse forms). Real sheets
    # are filled from the top and trail off — the partner's seed-germination
    # form is ~90% empty ruled rows.
    if FILL_FRAC[0] < 1.0:
        keep = max(1, int(round(len(rows) * FILL_FRAC[0])))
        blank_row = [("blank",)] * (max(len(r) for r in rows) if rows else 1)
        rows = [r if i < keep else list(blank_row[:len(r)])
                for i, r in enumerate(rows)]

    data_top = y
    for ri, row in enumerate(rows):
        if alt_shade and ri % 2 == 1:
            pg.shade([left, y, right, y + row_h], v=234)
        for ci in shade_cols:
            if ci + 1 < len(xs):
                pg.shade([xs[ci], y, xs[ci + 1], y + row_h], v=230)
        if spans and ri in spans:
            txt = spans[ri]
            w.text(pg.img, (left + W * 0.28, y + row_h * 0.12), txt,
                   size=hand_size * 0.95, force="font")
            golden.append([txt])
        else:
            grow = []
            for ci, spec in enumerate(row):
                if ci + 1 >= len(xs):
                    break
                draw_cell(pg, w, (xs[ci], y, xs[ci + 1], y + row_h), spec,
                          size=hand_size, pair_split=pair_split)
                grow += golden_of(spec)
            golden.append(grow)
        y += row_h

    # grid lines
    for gx in xs:
        pg.line((gx, hy), (gx, y))
    pg.line((left, hy), (right, hy))
    yy = hy + header_h
    ri = 0
    while yy <= y + 1:
        thick = 4 if (group_every and ri and ri % group_every == 0) else 2
        pg.line((left, yy), (right, yy), w=thick)
        yy += row_h
        ri += 1
    return y, golden


def draw_header_fields(pg, w, top, left, right, fields, per_row=2, row_h=70,
                       hand_size=42, label_size=28, rule=True):
    golden, colw, y = [], (right - left) / per_row, top
    for i in range(0, len(fields), per_row):
        for j, (label, spec) in enumerate(fields[i:i + per_row]):
            x = left + j * colw
            pg.ptext((x, y + row_h / 2 - 14), label + ":", size=label_size)
            lx = x + pg.pwidth(label + ":", label_size) + 12
            if rule:
                pg.line((lx, y + row_h - 18), (x + colw - 30, y + row_h - 18),
                        w=1, fill=(120, 120, 120))
            draw_cell(pg, w, (lx, y, x + colw - 30, y + row_h - 10), spec, size=hand_size)
            golden.append([label] + [g for g in golden_of(spec) if g is not None])
        y += row_h
    return y, golden


def ditto_line(pg, w, x, y0, y1):
    """The vertical squiggle field workers draw to mean 'same as above'."""
    n = 14
    pts = [(x + w.rng.uniform(-7, 7), y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    w.stroke(pg.img, pts, width=3, alpha=215)


def rotated_note(pg, w, text, x, y, size=34):
    """90-degree rotated marginal writing along the bottom edge."""
    tmp = Image.new("RGBA", (int(w.measure(text, size) + 60), int(size * 2.2)), (0, 0, 0, 0))
    w.text(tmp, (10, 10), text, size=size)
    tmp = tmp.rotate(90, expand=True)
    pg.img.alpha_composite(tmp, (int(x), int(y)))


# ── data pools (fictional; Indian field-ecology flavoured) ────────
FIRST = ["Ramesh", "Sunita", "Lakshmi", "Arjun", "Priya", "Manoj", "Kavita",
         "Suresh", "Anita", "Vijay", "Meena", "Ravi", "Geeta", "Prakash",
         "Radha", "Santosh", "Deepa", "Mahesh", "Savita", "Ganesh", "Rekha",
         "Dinesh", "Pooja", "Ashok", "Sarita", "Rajesh", "Usha", "Kiran",
         "Shanta", "Mohan", "Vinod", "Latha", "Bhaskar", "Nandini", "Selvam"]
LAST = ["Kumar", "Devi", "Bai", "Patil", "Naik", "Reddy", "Sharma", "Yadav",
        "Gowda", "Das", "Mandal", "Singh", "Rao", "Nayak", "Pawar", "More",
        "Shinde", "Kale", "Menon", "Pillai", "Iyer", "Shetty"]
SITES = ["Kotagiri", "Valparai", "Agumbe", "Sirsi", "Bhimashankar", "Munnar",
         "Wayanad", "Thattekad", "Kudremukh", "Anamalai", "Silent Valley",
         "Sakleshpur", "Coorg", "Nelliampathy", "Peppara", "Sharavathi"]
TRAILS = ["Left Bank", "Ridge Line", "Stream Side", "Upper Slope", "North Trail",
          "Old Estate", "Bamboo Patch", "Swamp Edge", "Canopy Walk", "Boundary Line"]
SPECIES = [
    "Myristica beddomei", "Dimocarpus longan", "Diospyros sylvatica",
    "Vateria indica", "Mesua ferrea", "Cullenia exarillata", "Litsea nigrescens",
    "Beilschmiedia dalzelli", "Syzygium densiflorum", "Drypetes wightii",
    "Knema attenuata", "Palaquium ravii", "Persea macrantha", "Holigarna nigra",
    "Ficus nervosa", "Elaeocarpus munroii", "Antidesma menasu", "Celtis sp.",
    "Macaranga indica", "Aglaia elaeagnoidea", "Garcinia gummi-gutta",
    "Hopea parviflora", "Artocarpus hirsutus", "Toona ciliata", "Olea dioica",
    "Actinodaphne bourdillonii", "Glochidion malabaricum", "Neolitsea sp.",
    "Litsea wightiana", "Prunus ceylanica", "Aphanamixis polystachya",
]
SPP_ABBR = ["Act mal", "Art het", "Ela tub", "Kne att", "Vat ind", "Mes fer",
            "Cul exa", "Myr bed", "Dry wig", "Hop par"]
WEATHER = ["Cloudy", "Sunny", "Light rain", "Overcast", "Drizzle", "Clear",
           "Misty", "Humid"]
REMARKS = ["top broken", "leaning", "termite damage", "epiphytes present",
           "bark peeled", "new flush", "dead branch", "climber load",
           "browsed by deer", "fallen", "resprouting", "canopy gap"]


# Vernacular / local names. On the partner's real sheets the species column is
# HANDWRITTEN in a local name and the Latin column is often blank — the corpus
# previously printed Latin binomials, which is a wrong and strong prior.
# Seeded from names mined out of our own transcriptions of their forms.
VERNACULAR = ["Kage", "Boothahami", "Icoruu", "Korum", "Kislor", "Rongon",
              "Ulumai", "Selai", "Seengali", "Pusa", "Puli", "Pala", "Padhuva",
              "Mesdhini", "Maaki", "Kadukai", "Punga", "Athi", "Belai", "Eotti",
              "Nooli", "Sandan", "Karimaram", "Vengai", "Thembavu", "Mine",
              "Neem", "Sambrani", "Kanuvai", "Illupai", "Naval", "Vagai",
              "Icodalai", "Peshini", "Cherumini", "Koregu", "Bothahami",
              "Thanng", "Maesa", "Unknown", "C.A", "Kobuum", "Dennifloruun"]


def _species_or_local(r, p_local=0.5):
    """Real sheets mix Latin and vernacular, often with Latin left blank."""
    return r.choice(VERNACULAR) if r.random() < p_local else r.choice(SPECIES)


def _name(r): return f"{r.choice(FIRST)} {r.choice(LAST)}"
def _team(r, n=3): return ", ".join(_name(r).split()[0] for _ in range(n))
def _date(r, y=2025): return f"{r.randint(1,28):02d}-{r.randint(1,12):02d}-{y}"
def _date2(r, y=25):  return f"{r.randint(1,28):02d}/{r.randint(1,12):02d}/{y}"
def _time(r): return f"{r.randint(6,11)}:{r.randint(0,59):02d} am"


def maybe(rng, p): return rng.random() < p


def _numcell(rng, val, p_dot=0.0, p_star=0.0, p_corr=0.0, p_strike=0.0):
    """Wrap a value in a randomly-chosen real-world annotation."""
    r = rng.random()
    if r < p_dot:  return ("dot",)
    if r < p_dot + p_strike: return ("strike",)
    if r < p_dot + p_strike + p_star: return ("star", val)
    if r < p_dot + p_strike + p_star + p_corr:
        wrong = str(rng.randint(1, 99))
        return ("corr", wrong, val)
    return ("num", str(val))


# ── ecology archetypes ────────────────────────────────────────────
def form_phenology(rng, w):
    """Landscape trail transect; grouped phenology columns of single chars."""
    pg = Page(LANDSCAPE)
    golden = {}
    pg.ptext((90, 60), f"Trail: {rng.choice(TRAILS)}", size=30, bold=True)
    y, gh = draw_header_fields(pg, w, 95, 90, pg.W - 90, [
        ("Date", ("text", _date(rng, rng.choice([2024, 2025])))),
        ("Observers", ("text", _team(rng, 2))),
        ("Weather", ("text", rng.choice(WEATHER))),
        ("Start time", ("text", _time(rng))),
    ], per_row=4, row_h=64, hand_size=38, label_size=24)
    golden["header"] = gh

    header = ["Tree No", "Species", "H (m)", "GBH (cm)", "Multistem",
              "Flush", "Mature", "Fallen", "Buds", "Open", "Fallen",
              "Unripe", "Ripe", "Fallen", "Notes"]
    hrows = [("LEAVES", 5, 7), ("FLOWERS", 8, 10), ("FRUITS", 11, 13)]
    fr = [0.055, 0.175, 0.045, 0.055, 0.075] + [0.042] * 9 + [0.11]
    rows, tn = [], 0
    for _ in range(rng.randint(18, 24)):
        tn += rng.choice([1, 1, 1, 2, 2, 3])            # non-sequential IDs
        multi = ("text", ", ".join(str(rng.randint(15, 300))
                                   for _ in range(rng.randint(2, 4)))) \
            if maybe(rng, 0.12) else ("blank",)
        leaf = [("num", str(rng.choice([0, 1, 2, 3, 4]))) for _ in range(2)]
        leaf.append(("text", rng.choice(["Y", "N"])))
        flw = [("num", str(rng.choice([0, 0, 0, 1, 2]))) for _ in range(2)]
        flw.append(("text", rng.choice(["Y", "N", "N"])))
        frt = [("num", str(rng.choice([0, 0, 1, 2, 3]))) for _ in range(2)]
        frt.append(("text", rng.choice(["Y", "N", "N"])))
        rows.append([("print", str(tn)), ("print", rng.choice(SPECIES)),
                     ("print", str(rng.randint(4, 32))),
                     ("print", str(rng.randint(20, 500)))] + [multi]
                    + leaf + flw + frt
                    + [("text", rng.choice(REMARKS)) if maybe(rng, 0.12) else ("blank",)])
    spans = {}
    if maybe(rng, 0.5) and len(rows) > 6:
        spans[rng.randrange(3, len(rows) - 2)] = \
            f"DEAD/DRY tree ({rng.choice(['Mar','May','Aug','Nov'])} {rng.randint(2017,2024)})"
    yb, gt = draw_table(pg, w, y + 16, 90, pg.W - 90, fr, header, rows,
                        row_h=48, header_h=44, hand_size=32, header_size=19,
                        shade_cols=(7, 10, 13), header_rows=hrows, spans=spans)
    golden["table"] = gt
    if maybe(rng, 0.4):
        w.blot(pg.img, rng.uniform(400, 900), rng.uniform(y + 100, yb - 60), r=13)
    return [pg], golden


def form_growth_survival(rng, w):
    """Landscape; each measurement column holds a printed old value + a
    handwritten new one — the pattern real monitoring sheets use."""
    pg = Page(LANDSCAPE, serif=True)
    pg.ptext((pg.W / 2, 62), "Growth and Survival Monitoring Datasheet",
             size=34, bold=True, anchor="mm")
    grid = f"{rng.choice('ABCDEFGHIJK')}{rng.randint(1,26)}"
    y, gh = draw_header_fields(pg, w, 105, 100, pg.W - 100, [
        ("Grid ID", ("print", grid)),
        ("Starting date", ("text", _date(rng))),
        ("Ending date", ("text", _date(rng))),
        ("Observers", ("text", _team(rng, 4))),
    ], per_row=2, row_h=62, hand_size=38, label_size=25)
    golden = {"header": gh}
    header = ["S.no", "T_no", "Species", "Basal_Dia_1 (cm)", "Basal_Dia_2 (cm)",
              "Shoot_L (cm)", "Crown_Dia (cm)", "Survival (A/B/Dr/D)", "Remarks"]
    fr = [0.045, 0.05, 0.20, 0.115, 0.115, 0.115, 0.115, 0.115, 0.13]
    rows = []
    n = rng.randint(14, 18)
    for i in range(1, n + 1):
        dead = maybe(rng, 0.16)
        sp = rng.choice(SPECIES)
        if dead:
            # dead stems: printed NA in every measurement column, plus the
            # handwritten dash field workers add to show "nothing recorded"
            row = [("print", str(i)), ("print", f"A{i:02d}"), ("print", sp)]
            for _ in range(4):
                row.append(("pair", "NA", None))
            row.append(("text", "D"))
        else:
            row = [("print", str(i)), ("print", f"A{i:02d}"), ("print", sp)]
            for lo, hi in ((0.5, 2.0), (0.5, 2.0)):
                old = round(rng.uniform(lo, hi), 1)
                new = round(old + rng.uniform(0.0, 0.6), 1)
                row.append(("pair", f"{old:.1f}", f"{new:.1f}"))
            for lo, hi in ((30, 180), (14, 110)):
                old = rng.randint(lo, hi)
                new = old + rng.randint(-6, 30)
                row.append(("pair", str(old), str(new)))
            row.append(("text", rng.choice(["A", "A", "A", "B", "Dr"])))
        row.append(("text", rng.choice(REMARKS)) if maybe(rng, 0.14) else ("blank",))
        rows.append(row)
    yb, gt = draw_table(pg, w, y + 24, 100, pg.W - 100, fr, header, rows,
                        row_h=56, header_h=64, hand_size=34, header_size=19,
                        pair_split=0.42, pair_cols=(3, 4, 5, 6))
    golden["table"] = gt
    return [pg], golden


def form_litter_biomass(rng, w):
    """Portrait decimal grid: the zeros/decimals/asterisk/ditto form."""
    pg = Page(PORTRAIT)
    loc = rng.choice(SITES)
    y, gh = draw_header_fields(pg, w, 80, 80, pg.W - 80, [
        ("Date of Collection", ("text", _date2(rng))),
        ("Date of Fresh Measurement", ("text", _date2(rng))),
        ("Date of Dry Measurement", ("text", _date2(rng))),
        ("Location", ("text", loc)),
        ("Data collectors", ("text", _team(rng, 3))),
        ("Avg Packet Wt (10 covers)", ("num", f"{rng.uniform(30,70):.3f}")),
    ], per_row=2, row_h=64, hand_size=40, label_size=23)
    header = ["Trap ID", "Fresh/Dry", "Leaf", "Twig", "Flower", "Fruit",
              "Seed", "Other", "Remarks"]
    fr = [0.085, 0.10, 0.115, 0.10, 0.095, 0.095, 0.095, 0.09, 0.225]
    n = rng.randint(18, 25)
    pref = rng.choice("CDLMT")
    rows = []
    for i in range(1, n + 1):
        leaf = f"{rng.uniform(60,199):.2f}"
        twig = f"{rng.uniform(3,48):.2f}" if maybe(rng, .9) else "0"
        def small():
            if maybe(rng, 0.72): return ("dot",) if maybe(rng, .5) else ("num", "0")
            v = f"{rng.uniform(0.03,9.9):.2f}"
            return ("star", v) if maybe(rng, .35) else ("num", v)
        rows.append([("text", f"{pref} {i}"), ("blank",), ("num", leaf),
                     ("num", twig), small(), small(), small(), small(),
                     ("blank",)])
    # a few genuinely empty trailing rows, as on real sheets
    for _ in range(rng.randint(2, 4)):
        rows.append([("blank",)] * 9)
    yb, gt = draw_table(pg, w, y + 20, 80, pg.W - 80, fr, header, rows,
                        row_h=56, header_h=68, hand_size=34, header_size=21)
    # ditto line down the Fresh/Dry column + its single written value at top
    x_fd = 80 + (pg.W - 160) * (fr[0] + fr[1] / 2)
    top_data = y + 20 + 68
    w.text(pg.img, (x_fd - 10, top_data + 8), "F", size=34)
    ditto_line(pg, w, x_fd, top_data + 58, top_data + 56 * (n - 1))
    for gi in range(1, min(len(gt), n + 1)):
        if len(gt[gi]) > 1:
            gt[gi][1] = "F"
    # legend + note go BELOW the grid so they never collide with data cells
    legend = "* = w/o cover"
    w.text(pg.img, (110, yb + 30), legend, size=34, force="font")
    note = "Note = Take avg wt of Dry cloth bags as well"
    w.text(pg.img, (110, yb + 92), note, size=32, force="font",
           max_w=pg.W - 260)
    golden = {"header": gh, "table": gt, "notes": [[legend], [note]]}
    if maybe(rng, 0.6):
        vals = [f"{rng.uniform(1,11):.2f}" for _ in range(rng.randint(5, 9))]
        for k, v in enumerate(vals):
            rotated_note(pg, w, v, 120 + k * 62, pg.H - 300, size=30)
        golden["margin"] = [[v] for v in vals]
    return [pg], golden


def form_germination(rng, w):
    """Two side-by-side code grids; single-letter cells over shaded rows."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 72), "SEED AND SEEDLING EXPERIMENT DATA SHEET",
             size=30, bold=True, anchor="mm")
    treat = rng.choice(["Low Shade Treatment", "High Shade Treatment",
                        "Open Canopy Treatment", "Gap Treatment"])
    pg.ptext((pg.W / 2, 112), treat, size=25, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, w, 140, 120, pg.W - 120, [
        ("Date", ("text", _date(rng, rng.choice([2023, 2024])))),
        ("Observers", ("text", _name(rng).upper())),
    ], per_row=2, row_h=64, hand_size=42, label_size=26)
    CODES = ["L", "L", "L", "D", "D", "R", "S", "C", "N"]
    header = ["Species", "Soil", "1", "2", "3", "4", "5", "6", "7", "8"]
    fr = [0.30, 0.13] + [0.0713] * 8
    golden = {"header": gh, "table": []}
    yy = y + 16
    for side, x0, x1 in (("A", 90, pg.W / 2 - 12), ("B", pg.W / 2 + 12, pg.W - 90)):
        pg.ptext(((x0 + x1) / 2, yy - 8), side, size=26, bold=True, anchor="mm")
        rows = []
        for blk in range(4):
            for _ in range(5):
                sp = rng.choice(SPP_ABBR)
                row = [("print", sp), ("print", rng.choice("REU"))]
                for _ in range(8):
                    if maybe(rng, 0.10):
                        row.append(("blank",))
                    else:
                        c = rng.choice(CODES)
                        if maybe(rng, 0.06): c = c + rng.choice("RSC")
                        row.append(("text", c))
                rows.append(row)
        yb, gt = draw_table(pg, w, yy + 16, x0, x1, fr, header, rows,
                            row_h=44, header_h=40, hand_size=30, header_size=17,
                            alt_shade=True, group_every=5)
        golden["table"] += gt if side == "A" else gt[1:]
    legend = ("Codes: N = Not germinated | C = Cotyledon split | "
              "R = Root emerged | S = Shoot emerged | L = First leaf")
    pg.ptext((90, yb + 26), legend, size=21)
    golden["notes"] = [[legend]]
    return [pg], golden


def form_regeneration(rng, w):
    """Quadrat regeneration counts with tally marks."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 68), "REGENERATION PLOT 5m x 5m — SEEDLING COUNTS",
             size=30, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, w, 120, 80, pg.W - 80, [
        ("Site", ("text", rng.choice(SITES))),
        ("Plot No", ("text", f"{rng.choice('PQR')}{rng.randint(1,40)}")),
        ("Date", ("text", _date(rng))),
        ("Recorder", ("text", _name(rng))),
    ], per_row=2, row_h=66, hand_size=40, label_size=25)
    header = ["S.No", "Species", "Seedlings", "Saplings", "Height class", "Remarks"]
    fr = [0.07, 0.31, 0.15, 0.15, 0.16, 0.16]
    rows = []
    for i in range(1, rng.randint(11, 15)):
        rows.append([("num", str(i)), ("print", rng.choice(SPECIES)),
                     ("tally", rng.randint(1, 14)),
                     ("tally", rng.randint(1, 8)) if maybe(rng, .75) else ("dot",),
                     ("text", rng.choice(["<50cm", "50-100", ">100cm"])),
                     ("text", rng.choice(REMARKS)) if maybe(rng, .2) else ("blank",)])
    yb, gt = draw_table(pg, w, y + 24, 80, pg.W - 80, fr, header, rows,
                        row_h=84, header_h=60, hand_size=38, header_size=22)
    return [pg], {"header": gh, "table": gt}


def form_gbh_plot(rng, w):
    """Dense GBH/height plot enumeration — the classic tree-plot datasheet."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 66), "TREE PLOT 20m x 20m — ENUMERATION SHEET",
             size=30, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, w, 118, 80, pg.W - 80, [
        ("Plot ID", ("text", f"{rng.choice('NSEW')}{rng.randint(1,60)}")),
        ("Date", ("text", _date2(rng))),
        ("GPS", ("text", f"{rng.uniform(8,15):.4f} N {rng.uniform(74,78):.4f} E")),
        ("Team", ("text", _team(rng, 3))),
        ("Altitude (m)", ("num", str(rng.randint(200, 2100)))),
        ("Slope (deg)", ("num", str(rng.randint(0, 45)))),
    ], per_row=2, row_h=62, hand_size=38, label_size=24)
    header = ["S.No", "Tag No", "Species", "GBH (cm)", "Height (m)",
              "Canopy", "Remarks"]
    fr = [0.07, 0.10, 0.30, 0.13, 0.12, 0.12, 0.16]
    rows = []
    for i in range(1, rng.randint(16, 22)):
        rows.append([
            ("num", str(i)), ("num", f"{rng.randint(100,999)}"),
            ("print", rng.choice(SPECIES)),
            _numcell(rng, f"{rng.uniform(10,220):.1f}", p_corr=0.07),
            _numcell(rng, str(rng.randint(3, 40)), p_dot=0.04),
            ("text", rng.choice(["D", "CoD", "I", "S"])),
            ("text", rng.choice(REMARKS)) if maybe(rng, .18) else ("blank",)])
    yb, gt = draw_table(pg, w, y + 22, 80, pg.W - 80, fr, header, rows,
                        row_h=66, header_h=58, hand_size=36, header_size=21)
    return [pg], {"header": gh, "table": gt}


def form_soil_microclimate(rng, w):
    """Soil/microclimate readings — temperature, moisture, pH, canopy."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 66), "SOIL AND MICROCLIMATE MONITORING", size=32,
             bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, w, 118, 80, pg.W - 80, [
        ("Site name", ("text", rng.choice(SITES))),
        ("Date", ("text", _date(rng))),
        ("Team", ("text", _team(rng, 3))),
        ("Start time", ("text", _time(rng))),
        ("Weather", ("text", rng.choice(WEATHER))),
        ("Elevation (m)", ("num", str(rng.randint(300, 2000)))),
    ], per_row=2, row_h=62, hand_size=40, label_size=24)
    header = ["Point", "Soil temp (C)", "Air temp (C)", "Soil moisture (%)",
              "pH", "Canopy cover (%)", "Litter depth (cm)", "Remarks"]
    fr = [0.065, 0.12, 0.115, 0.13, 0.075, 0.135, 0.125, 0.235]
    rows = []
    for i in range(1, rng.randint(12, 17)):
        rows.append([
            ("text", f"P{i}"),
            ("num", f"{rng.uniform(18,31):.1f}"),
            ("num", f"{rng.uniform(20,34):.1f}"),
            _numcell(rng, f"{rng.uniform(10,60):.1f}", p_strike=0.05),
            ("num", f"{rng.uniform(4.5,7.6):.1f}"),
            ("num", str(rng.randint(20, 98))),
            _numcell(rng, f"{rng.uniform(0.5,9):.1f}", p_dot=0.06),
            ("text", rng.choice(["shaded", "gap", "rocky", "wet", "leaf mat",
                                 "bare", "root mat"]))
            if maybe(rng, .3) else ("blank",)])
    yb, gt = draw_table(pg, w, y + 22, 80, pg.W - 80, fr, header, rows,
                        row_h=72, header_h=76, hand_size=36, header_size=19)
    return [pg], {"header": gh, "table": gt}


def form_nursery(rng, w):
    """Nursery / plantation upkeep register — livelihoods-adjacent ecology."""
    pg = Page(LANDSCAPE)
    pg.ptext((pg.W / 2, 60), "NURSERY SEEDLING STOCK AND UPKEEP REGISTER",
             size=34, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, w, 105, 90, pg.W - 90, [
        ("Nursery", ("text", rng.choice(SITES))),
        ("Month", ("text", rng.choice(["Jan", "Feb", "Jun", "Jul", "Sep"]) + " 2025")),
        ("In charge", ("text", _name(rng))),
        ("Beds", ("num", str(rng.randint(4, 30)))),
    ], per_row=4, row_h=62, hand_size=38, label_size=24)
    header = ["Bed", "Species", "Sown", "Germinated", "Alive", "Dead",
              "Watered", "Weeded", "Ready", "Remarks"]
    fr = [0.05, 0.20, 0.08, 0.095, 0.08, 0.07, 0.08, 0.075, 0.08, 0.19]
    rows = []
    for i in range(1, rng.randint(13, 18)):
        sown = rng.randint(50, 600)
        germ = int(sown * rng.uniform(.4, .95))
        dead = int(germ * rng.uniform(0, .3))
        rows.append([("num", str(i)), ("print", rng.choice(SPECIES)),
                     ("num", str(sown)), ("num", str(germ)),
                     ("num", str(germ - dead)),
                     ("dot",) if dead == 0 else ("num", str(dead)),
                     ("tick",) if maybe(rng, .8) else ("strike",),
                     ("tick",) if maybe(rng, .6) else ("strike",),
                     ("num", str(int((germ - dead) * rng.uniform(.2, .8)))),
                     ("text", rng.choice(["shade net torn", "aphids seen",
                                          "repotted", "good growth"]))
                     if maybe(rng, .25) else ("blank",)])
    yb, gt = draw_table(pg, w, y + 20, 90, pg.W - 90, fr, header, rows,
                        row_h=62, header_h=56, hand_size=34, header_size=20,
                        alt_shade=maybe(rng, .5))
    return [pg], {"header": gh, "table": gt}


ECO_FORMS = {
    "ecology__phenology":       form_phenology,
    "ecology__growth_survival": form_growth_survival,
    "ecology__litter_biomass":  form_litter_biomass,
    "ecology__germination":     form_germination,
    "ecology__regeneration":    form_regeneration,
    "ecology__gbh_plot":        form_gbh_plot,
    "ecology__soil_micro":      form_soil_microclimate,
    "ecology__nursery":         form_nursery,
}


def page_furniture(pg, rng):
    """Physical artefacts of a photographed field notebook: spiral binding,
    a bulldog clip, a curl shadow at one edge. Real partner scans have these
    and they occlude/darken the margins, so the model should expect them."""
    d = ImageDraw.Draw(pg.img)
    W, H = pg.W, pg.H
    kind = rng.random()
    if kind < 0.28:                                   # spiral binding, left edge
        n = rng.randint(14, 24)
        for i in range(n):
            cy = H * (i + 0.5) / n
            x = rng.uniform(6, 26)
            d.arc([x, cy - 16, x + 42, cy + 16], start=95, end=265,
                  fill=(70, 70, 75, 255), width=rng.randint(5, 8))
            d.ellipse([x + 30, cy - 5, x + 42, cy + 5], fill=(245, 245, 245, 255))
    elif kind < 0.42:                                 # bulldog clip, top edge
        cw = rng.uniform(W * 0.10, W * 0.18)
        cx = rng.uniform(W * 0.12, W * 0.62)
        d.rectangle([cx, 0, cx + cw, rng.uniform(60, 105)], fill=(28, 28, 32, 255))
        d.line([(cx + cw * .2, 8), (cx + cw * .2, 96)], fill=(120, 120, 130, 255), width=4)
    elif kind < 0.5:                                  # staple
        sx, sy = rng.uniform(40, 110), rng.uniform(40, 110)
        d.line([(sx, sy), (sx + 34, sy - 8)], fill=(90, 90, 95, 255), width=5)
    # edge curl shadow
    if rng.random() < 0.45:
        side = rng.choice("lrtb")
        band = int(min(W, H) * rng.uniform(0.04, 0.10))
        sh = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(sh)
        for i in range(band):
            v = int(90 * (1 - i / band))
            if side == "l":   sd.line([(i, 0), (i, H)], fill=v)
            elif side == "r": sd.line([(W - i, 0), (W - i, H)], fill=v)
            elif side == "t": sd.line([(0, i), (W, i)], fill=v)
            else:             sd.line([(0, H - i), (W, H - i)], fill=v)
        pg.img.paste(Image.new("RGBA", (W, H), (40, 40, 45, 255)), (0, 0), sh)


# ── degradation ───────────────────────────────────────────────────
def degrade(img, rng, hard=False, photo=None):
    """Scan/photocopy degradation. `photo` in {None,'mild','field','rough'}
    first applies the phone-camera pipeline (perspective, page bow, finger,
    shadow, background) — the real submission channel, which augraphy alone
    does not model because it simulates a SCANNER."""
    im = img.convert("RGB")
    if photo:
        try:
            import photo_aug
            im = photo_aug.apply(im, rng, level=photo)
        except Exception:
            pass
    if hard:
        im = im.resize((int(im.width * rng.uniform(.62, .78)),
                        int(im.height * rng.uniform(.62, .78))), Image.BICUBIC)
    try:
        from augraphy import (AugraphyPipeline, InkBleed, BleedThrough, LowInkRandomLines,
                              DirtyDrum, Folding, SubtleNoise, Brightness, BadPhotoCopy,
                              LightingGradient, DirtyRollers, Jpeg, ShadowCast)
        ink = [InkBleed(intensity_range=(.3, .7), p=.6),
               LowInkRandomLines(count_range=(2, 8), p=.35 if not hard else .6)]
        paper = [BleedThrough(alpha_range=(.05, .2), p=.35),
                 LightingGradient(p=.5)]
        post = [DirtyRollers(p=.25), DirtyDrum(p=.2),
                Folding(fold_count=rng.randint(1, 3), p=.3),
                ShadowCast(p=.3), SubtleNoise(p=.6),
                Brightness(brightness_range=(.85, 1.05), p=.5),
                Jpeg(quality_range=(45, 75) if hard else (65, 92), p=.8)]
        if hard:
            post.insert(0, BadPhotoCopy(p=.5))
        arr = AugraphyPipeline(ink_phase=ink, paper_phase=paper,
                               post_phase=post).augment(np.asarray(im))["output"]
        im = Image.fromarray(np.uint8(np.clip(arr, 0, 255)))
    except Exception:
        im = im.filter(ImageFilter.GaussianBlur(rng.uniform(.4, .9)))
    im = im.rotate(rng.uniform(-1.1, 1.1) * (2.0 if hard else 1.0),
                   resample=Image.BICUBIC, fillcolor=(250, 250, 248))
    from io import BytesIO
    b = BytesIO(); im.convert("RGB").save(b, "JPEG",
                                          quality=rng.randint(45, 60) if hard else rng.randint(66, 88))
    return Image.open(BytesIO(b.getvalue())).convert("RGB")


# ── golden writer ─────────────────────────────────────────────────
def write_golden(golden, dst):
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    for sheet in ("header", "checkboxes", "table", "notes", "margin"):
        rows = golden.get(sheet)
        if not rows:
            continue
        ws = wb.create_sheet(sheet)
        for r in rows:
            ws.append([c for c in r] if isinstance(r, list) else [r])
    wb.save(dst)


# The v1 social-sector archetypes (health / education / livelihoods /
# agriculture) are good layouts that only lacked real ink — re-run them with
# the v2 Writer and augraphy so the corpus keeps sector breadth.
def _social_forms():
    try:
        sys.path.insert(0, str(HERE))
        import formgen as fg1
        return {n: fn for n, (fn, _desc) in fg1.FORMS.items()}
    except Exception as e:  # noqa: BLE001
        print(f"(social archetypes unavailable: {e})")
        return {}


def all_forms():
    forms = dict(ECO_FORMS)
    forms.update(_social_forms())
    return forms


def generate(out_root: Path, seed=100, only=None, hard=False, count=1):
    made = 0
    for name, fn in all_forms().items():
        if only and name != only:
            continue
        for k in range(count):
            tag = f"{seed}_{k}"
            rng = random.Random(f"{seed}:{name}:{k}:{'H' if hard else 'N'}")
            # weighted toward sparse — the measured cause of over-production
            FILL_FRAC[0] = rng.choices(
                [0.08, 0.15, 0.25, 0.40, 0.55, 0.70, 0.85, 1.0],
                [8,    9,    8,    7,    6,    5,    4,    5])[0]
            w = Writer(rng, prose=rng.choice(["hybrid", "hybrid", "glyph"]))
            pages, golden = fn(rng, w)
            d = out_root / f"{name}__{tag}{'_hard' if hard else ''}"
            d.mkdir(parents=True, exist_ok=True)
            # Most real uploads are phone photos, so most training forms should
            # be too; keep a share of clean "scans" for the tier that has them.
            photo = rng.choices([None, "mild", "field", "rough"],
                                [3, 3, 4, 2])[0]
            doc = fitz.open()
            for pg in pages:
                if rng.random() < 0.55:
                    page_furniture(pg, rng)
                im = degrade(pg.img, rng, hard=hard, photo=photo)
                tmp = d / "_t.jpg"; im.save(tmp, "JPEG", quality=90)
                rect = fitz.Rect(0, 0, im.width * 72 / 180, im.height * 72 / 180)
                doc.new_page(width=rect.width, height=rect.height).insert_image(
                    rect, filename=str(tmp))
            doc.save(d / "input.pdf"); doc.close()
            (d / "_t.jpg").unlink(missing_ok=True)
            write_golden(golden, d / "golden.xlsx")
            (d / "provenance.md").write_text(
                f"# {d.name}\n\nSYNTHETIC (formgen2.py seed {seed}/{k}"
                f"{', hard' if hard else ''}). Real SD-19 hand-print glyphs "
                f"(cohort {w.cohort}) + cursive font {Path(w.font_path).name} "
                f"for prose; augraphy degradation. Golden exact by "
                f"construction. All values fictional.\n")
            made += 1
            print(f"  {d.name}", flush=True)
    print(f"generated {made} forms -> {out_root}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    hard = "--hard" in sys.argv
    cnt = 1
    for a in sys.argv[1:]:
        if a.startswith("--count"):
            cnt = int(a.split("=")[1]) if "=" in a else 1
    out = Path(args[0]) if args else HERE.parent / "train_forms2"
    seed = int(args[1]) if len(args) > 1 else 100
    only = args[2] if len(args) > 2 else None
    generate(out, seed, only, hard=hard, count=cnt)
