#!/usr/bin/env python3
"""Fill a REAL blank field-datasheet template with synthetic handwriting.

Why this exists: our synthetic corpus so far uses layouts *I* invented, so both
the model and the template-matcher risk looking good on structures they have
effectively memorised. Real blank templates downloaded from the web supply
authentic structural diversity that nobody on this project designed.

The trick that makes the goldens exact and avoids a CV-parameter treadmill:
a blank template PDF is a VECTOR document. PyMuPDF gives us

  * the printed label text with exact positions  (page.get_text)
  * the printed rules as exact line segments      (page.get_drawings)

so the grid and the labels are read off the file rather than inferred from
pixels. Nothing to tune. We then fill only the cells that are EMPTY in the
blank — which needs no semantic understanding of the form at all — and the
golden is (printed labels, exactly) + (values we wrote, exactly).

Usage:
  python3 fill_template.py <blank.pdf> <out_dir> [--seed N] [--density 0.6]
                           [--page N] [--hard]
"""
import argparse, json, random, sys
from pathlib import Path

import fitz
import openpyxl
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import formgen2 as fg                                     # noqa: E402

MAX_DIM = 2000


# ── structure straight out of the PDF (no CV, no thresholds) ──────
def extract_structure(pdf: Path, page_no=0):
    doc = fitz.open(str(pdf))
    page = doc[page_no]
    R = page.rect
    words = [{"text": w[4], "bbox": (w[0], w[1], w[2], w[3])}
             for w in page.get_text("words")]
    # Real templates draw rules as THIN FILLED RECTANGLES, and one visual rule
    # is often several rectangles laid end to end with small gaps. So: reduce
    # each thin rect to a single segment along its long axis, then merge
    # collinear, nearly-touching segments into runs.
    hseg, vseg = [], []

    def add(x0, y0, x1, y1, thick=0.0):
        if abs(y1 - y0) <= max(2.5, thick) and abs(x1 - x0) > 4:
            hseg.append((min(x0, x1), max(x0, x1), (y0 + y1) / 2))
        elif abs(x1 - x0) <= max(2.5, thick) and abs(y1 - y0) > 4:
            vseg.append((min(y0, y1), max(y0, y1), (x0 + x1) / 2))

    for d in page.get_drawings():
        for item in d["items"]:
            if item[0] == "l":
                add(item[1].x, item[1].y, item[2].x, item[2].y)
            elif item[0] == "re":
                r = item[1]
                w, h = r.x1 - r.x0, r.y1 - r.y0
                if min(w, h) <= 2.5:                 # a rule, not a box
                    add(r.x0, r.y0, r.x1, r.y1)
                else:                                # a genuine box: 4 sides
                    hseg += [(r.x0, r.x1, r.y0), (r.x0, r.x1, r.y1)]
                    vseg += [(r.y0, r.y1, r.x0), (r.y0, r.y1, r.x1)]
    doc.close()
    return {"rect": (R.x0, R.y0, R.x1, R.y1), "words": words,
            "h": _merge(hseg), "v": _merge(vseg), "page_no": page_no}


def _merge(segs, coord_tol=1.6, gap_tol=4.0):
    """Join collinear segments that touch or nearly touch."""
    if not segs:
        return []
    segs = sorted(segs, key=lambda s: (round(s[2] / coord_tol), s[0]))
    out = []
    for a0, a1, c in segs:
        if out and abs(out[-1][2] - c) <= coord_tol and a0 <= out[-1][1] + gap_tol:
            out[-1] = (out[-1][0], max(out[-1][1], a1), (out[-1][2] + c) / 2)
        else:
            out.append((a0, a1, c))
    return out


def _cluster(vals, tol=2.0):
    vals = sorted(vals)
    out = []
    for v in vals:
        if not out or v - out[-1][-1] > tol:
            out.append([v])
        else:
            out[-1].append(v)
    return [sum(g) / len(g) for g in out]


def build_cells(st, min_w=14, min_h=8):
    """Lattice cells from the rule segments; keep only cells whose four sides
    are actually drawn, so we do not invent cells in whitespace."""
    ys = _cluster([s[2] for s in st["h"]])
    xs = _cluster([s[2] for s in st["v"]])
    if len(ys) < 2 or len(xs) < 2:
        return []

    def h_covers(y, x0, x1):
        return any(abs(s[2] - y) <= 2.5 and s[0] <= x0 + 3 and s[1] >= x1 - 3
                   for s in st["h"])

    def v_covers(x, y0, y1):
        return any(abs(s[2] - x) <= 2.5 and s[0] <= y0 + 3 and s[1] >= y1 - 3
                   for s in st["v"])

    # Require 3 of the 4 sides rather than all 4: real templates often leave the
    # outer edge of a table unruled, or draw it as a curve we do not parse, and
    # demanding all four silently discarded whole documents.
    cells = []
    for i in range(len(ys) - 1):
        for j in range(len(xs) - 1):
            y0, y1, x0, x1 = ys[i], ys[i + 1], xs[j], xs[j + 1]
            if (x1 - x0) < min_w or (y1 - y0) < min_h:
                continue
            sides = (h_covers(y0, x0, x1) + h_covers(y1, x0, x1)
                     + v_covers(x0, y0, y1) + v_covers(x1, y0, y1))
            # both horizontal rules must be present (rows are what get ruled);
            # one vertical may be missing
            if sides >= 3 and h_covers(y0, x0, x1) and h_covers(y1, x0, x1):
                cells.append({"row": i, "col": j, "bbox": (x0, y0, x1, y1)})
    return cells


def cell_text(st, bbox, pad=1.5):
    x0, y0, x1, y1 = bbox
    got = []
    for w in st["words"]:
        wx0, wy0, wx1, wy1 = w["bbox"]
        cx, cy = (wx0 + wx1) / 2, (wy0 + wy1) / 2
        if x0 - pad <= cx <= x1 + pad and y0 - pad <= cy <= y1 + pad:
            got.append((wx0, w["text"]))
    return " ".join(t for _, t in sorted(got))


# ── value generators, chosen per column ───────────────────────────
def _species(rng):    return rng.choice(fg.SPECIES)
def _vernacular(rng): return rng.choice(VERNACULAR)
def _int(rng):        return str(rng.randint(1, 250))
def _dec(rng):        return f"{rng.uniform(0.2, 180):.1f}"
def _code1(rng):      return rng.choice("TSCFNMXYLDR")
def _yn(rng):         return rng.choice(["Y", "N"])
def _date(rng):       return f"{rng.randint(1,28):02d}/{rng.randint(1,12):02d}/{rng.randint(19,25)}"
def _short(rng):      return rng.choice(fg.REMARKS)
def _person(rng):     return rng.choice(fg.FIRST)

# vernacular names mined from the partner's own transcriptions plus common
# South-Indian tree names — the class of token the corpus was missing entirely
VERNACULAR = ["Kage", "Boothahami", "Icoruu", "Korum", "Kislor", "Rongon",
              "Ulumai", "Selai", "Seengali", "Pusa", "Puli", "Pala", "Padhuva",
              "Mesdhini", "Maaki", "Kadukai", "Punga", "Athi", "Belai", "Eotti",
              "Nooli", "Sandan", "Karimaram", "Vengai", "Thembavu", "Mine",
              "Neem", "Sambrani", "Kanuvai", "Illupai", "Naval", "Vagai"]

COLTYPES = [("species", _species, 0.10), ("vernacular", _vernacular, 0.16),
            ("int", _int, 0.24), ("dec", _dec, 0.16), ("code1", _code1, 0.14),
            ("yn", _yn, 0.06), ("date", _date, 0.05), ("short", _short, 0.05),
            ("person", _person, 0.04)]


# Value kinds a column can hold, by how wide the column actually is. Real form
# designers size a column to its content, so assigning a long species name to a
# 30pt column produces text that overflows into the neighbouring printed label —
# which looks nothing like a real sheet and corrupts the eval image.
WIDTH_BANDS = [
    (38,  ["code1", "yn"]),
    (70,  ["code1", "yn", "int", "date"]),
    (120, ["int", "dec", "date", "person", "vernacular"]),
    (1e9, ["species", "vernacular", "short", "person", "int", "dec"]),
]


def pick_coltypes(cells, ncols, rng):
    """Choose a value kind per column, constrained by that column's width."""
    widths = {}
    for c in cells:
        w = c["bbox"][2] - c["bbox"][0]
        widths.setdefault(c["col"], []).append(w)
    out = []
    for col in range(ncols):
        ws = sorted(widths.get(col, [60]))
        med = ws[len(ws) // 2]
        allowed = next(kinds for lim, kinds in WIDTH_BANDS if med <= lim)
        if col == 0 and med <= 70 and rng.random() < 0.6:
            out.append("int")                      # serial-number column
        else:
            out.append(rng.choice(allowed))
    return out


GEN = {k: f for k, f, _ in COLTYPES}


def fill(pdf: Path, out_dir: Path, seed=0, density=0.6, page_no=0, hard=False):
    rng = random.Random(seed)
    st = extract_structure(pdf, page_no)
    cells = build_cells(st)
    if len(cells) < 8:
        return None, f"only {len(cells)} cells found — not a gridded form page"

    # Render the blank at high resolution; we draw handwriting onto this.
    doc = fitz.open(str(pdf))
    page = doc[page_no]
    scale = min(MAX_DIM / max(page.rect.width, page.rect.height), 4.0)
    pm = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples).convert("RGBA")
    doc.close()

    writer = fg.Writer(rng, prose=rng.choice(["hybrid", "hybrid", "glyph"]))
    ncols = max(c["col"] for c in cells) + 1
    coltypes = pick_coltypes(cells, ncols, rng)

    # Cells that already contain printed text are labels/headers -> leave them,
    # and record them in the golden. Empty cells are fillable. This needs no
    # semantic understanding of the form.
    printed, blanks = [], []
    for c in cells:
        t = cell_text(st, c["bbox"])
        (printed if t.strip() else blanks).append((c, t))

    golden_printed = [t for _, t in printed if t.strip()]
    rows_written = {}
    n_fill = int(len(blanks) * density)
    # fill top-down so the sheet looks partially completed, like a real one
    blanks.sort(key=lambda ct: (ct[0]["row"], ct[0]["col"]))
    for c, _ in blanks[:n_fill]:
        if rng.random() > 0.93:
            continue                                   # occasional skipped cell
        kind = coltypes[c["col"]]
        val = GEN[kind](rng)
        x0, y0, x1, y1 = [v * scale for v in c["bbox"]]
        box = (x0, y0, x1, y1)
        size = max(14, min(38, (y1 - y0) * 0.62))
        spec = ("text", val)
        if kind in ("int", "dec") and rng.random() < 0.05:
            spec = ("dot",)                            # dot == 0 convention
        elif rng.random() < 0.04:
            spec = ("strike",)                         # struck == no entry
        fg.draw_cell(type("P", (), {"img": img, "d": None, "ptext": lambda *a, **k: None})(),
                     writer, box, spec, size=size)
        g = fg.golden_of(spec)[0]
        if g is not None:
            rows_written.setdefault(c["row"], []).append((c["col"], g))

    out_dir.mkdir(parents=True, exist_ok=True)
    final = fg.degrade(img, rng, hard=hard)
    tmp = out_dir / "_t.jpg"; final.save(tmp, "JPEG", quality=90)
    d2 = fitz.open()
    r = fitz.Rect(0, 0, final.width * 72 / 180, final.height * 72 / 180)
    d2.new_page(width=r.width, height=r.height).insert_image(r, filename=str(tmp))
    d2.save(out_dir / "input.pdf"); d2.close(); tmp.unlink(missing_ok=True)

    wb = openpyxl.Workbook(); wb.remove(wb.active)
    ws = wb.create_sheet("printed")
    for t in golden_printed:
        ws.append([t])
    ws2 = wb.create_sheet("written")
    for r_i in sorted(rows_written):
        ws2.append([v for _, v in sorted(rows_written[r_i])])
    wb.save(out_dir / "golden.xlsx")

    meta = {"template": pdf.name, "page": page_no, "seed": seed,
            "density": density, "hard": hard, "cells": len(cells),
            "printed_cells": len(printed), "filled": sum(len(v) for v in rows_written.values()),
            "coltypes": coltypes, "writer_cohort": writer.cohort}
    (out_dir / "provenance.md").write_text(
        f"# {out_dir.name}\n\nREAL blank template `{pdf.name}` (page {page_no+1}) "
        f"filled with synthetic handwriting.\nStructure and printed labels read "
        f"directly from the PDF's vector text/line data — exact, no CV "
        f"thresholds.\nGolden is exact by construction: printed labels from the "
        f"file + the values written here.\n\n```json\n{json.dumps(meta, indent=2)}\n```\n")
    return meta, None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--density", type=float, default=0.6)
    ap.add_argument("--page", type=int, default=0)
    ap.add_argument("--hard", action="store_true")
    a = ap.parse_args()
    m, err = fill(Path(a.pdf), Path(a.out), a.seed, a.density, a.page, a.hard)
    print(json.dumps(m) if m else f"SKIP: {err}")
