#!/usr/bin/env python3
"""Row-band extraction at high zoom, for API models, with no blank template.

Rationale
---------
On the phenology form the printed columns (Tree No / Species / H / GBH) are read
essentially perfectly by everything, and the nine narrow hand-filled columns are
where all the error is. Those columns are single characters in ~30px-wide cells
at page zoom. Whole-page prompting gives the model too few pixels per glyph and
it falls back to stamping the column's modal value.

So: detect the table's ruled rows, cut the table into horizontal bands of a few
rows each, render each band at high zoom, and staple the table's header strip on
top of every band so the model always knows which column is which.

Unlike structured_extract.py this needs NO blank template and does NO printed-
layer subtraction (measured at -0.114 — handwriting overlaps the rules).

Bands deliberately overlap and are NOT required to align to row boundaries: the
scorer keys rows by the printed Tree No, so a row read twice is deduped and a
row split across bands is recovered from whichever band saw it whole.
"""
import argparse, base64, io, json, sys, time
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import wide_bench                                  # noqa: E402  (providers, keys)


def render(pdf: Path, page_no: int, dpi: int = 300) -> Image.Image:
    import fitz
    d = fitz.open(str(pdf))
    p = d[page_no]
    pix = p.get_pixmap(dpi=dpi)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def hlines(im: Image.Image, min_frac: float = 0.55) -> list[int]:
    """y positions of long horizontal rules, via a darkness projection."""
    a = np.asarray(im.convert("L"))
    dark = (a < 160).sum(axis=1) / a.shape[1]
    ys = np.where(dark > min_frac)[0]
    if len(ys) == 0:
        return []
    # collapse runs of adjacent rows into one line each
    out, run = [], [ys[0]]
    for y in ys[1:]:
        if y - run[-1] <= 3:
            run.append(y)
        else:
            out.append(int(np.mean(run)))
            run = [y]
    out.append(int(np.mean(run)))
    return out


def bands(im: Image.Image, rows_per_band: int = 8, overlap: int = 1):
    """(header_box, [band_box,...]) in pixel coords.

    The header strip is the band between the last two rules ABOVE the widest
    run of evenly-spaced rules — i.e. the table's column-header row.
    """
    ls = hlines(im)
    if len(ls) < 4:
        h = im.height
        return (0, int(h * .10), im.width, int(h * .18)), [
            (0, int(h * (.16 + i * .12)), im.width, int(h * (.16 + (i + 1) * .12 + .02)))
            for i in range(7)]
    gaps = np.diff(ls)
    med = float(np.median(gaps))
    # data rules = those separated by roughly the modal row height
    data_idx = [i for i, g in enumerate(gaps) if 0.6 * med <= g <= 1.6 * med]
    if not data_idx:
        data_idx = list(range(len(gaps)))
    first = data_idx[0]
    hdr_top = ls[max(first - 1, 0)]
    hdr_box = (0, max(hdr_top - int(2.2 * med), 0), im.width, ls[first])
    rules = [ls[i] for i in range(first, len(ls))]
    # Uniform stepping over the table extent. Rule detection is only used for
    # the extent and the row pitch: on skewed/faint scans hlines() silently
    # misses rules, and stepping rule-to-rule then skipped whole rows (measured:
    # 65% row coverage, and the model renumbered the gaps it was handed).
    top, bot = rules[0], rules[-1]
    px = med * rows_per_band
    step = med * max(rows_per_band - overlap, 1)
    out, y = [], float(top)
    while y < bot - med * 0.5:
        out.append((0, max(int(y) - 4, 0), im.width,
                    min(int(y + px) + 4, im.height)))
        y += step
    return hdr_box, out


def vlines(im: Image.Image, y0: int, y1: int, min_frac: float = 0.7) -> list[int]:
    """x positions of the table's vertical rules, measured over the data area."""
    a = np.asarray(im.convert("L"))[y0:y1]
    dark = (a < 160).sum(axis=0) / max(a.shape[0], 1)
    xs = np.where(dark > min_frac)[0]
    if len(xs) == 0:
        return []
    out, run = [], [xs[0]]
    for x in xs[1:]:
        if x - run[-1] <= 3:
            run.append(x)
        else:
            out.append(int(np.mean(run))); run = [x]
    out.append(int(np.mean(run)))
    return out


def narrow_cols(rules: list[int]) -> list[tuple[int, int]]:
    """Key column + every column narrower than the median.

    Wide columns on these forms are free-text (species, notes) and every model
    already reads them ~perfectly; the narrow ones hold the single-character
    hand-filled codes where all the error lives. Dropping the wide ones is what
    buys back the pixels-per-glyph that the 1568px vision cap takes away.
    """
    if len(rules) < 4:
        return []
    cols = list(zip(rules, rules[1:]))
    w = [b - a for a, b in cols]
    med = float(np.median(w))
    keep = [cols[0]]                                   # printed key column
    keep += [c for c, ww in zip(cols[1:], w[1:]) if ww <= med]
    return keep


def stack(im: Image.Image, hdr_box, band_box, zoom: float, cap: int = 1560,
          keep: list[tuple[int, int]] | None = None):
    """Header strip stapled above the band, scaled to the vision cap.

    With `keep`, only those x-ranges are retained and are pasted side by side,
    so the surviving columns get the whole width budget.
    """
    def slice_(box):
        im2 = im.crop(box)
        if not keep:
            return im2
        parts = [im.crop((x0, box[1], x1, box[3])) for x0, x1 in keep]
        w = sum(p.width for p in parts)
        out = Image.new("RGB", (w, im2.height), "white")
        x = 0
        for p in parts:
            out.paste(p, (x, 0)); x += p.width
        return out

    hdr, bnd = slice_(hdr_box), slice_(band_box)
    w = max(hdr.width, bnd.width)
    out = Image.new("RGB", (w, hdr.height + bnd.height), "white")
    out.paste(hdr, (0, 0)); out.paste(bnd, (0, hdr.height))
    s = min(zoom, cap / max(out.width, out.height))
    if s != 1.0:
        out = out.resize((max(int(out.width * s), 1), max(int(out.height * s), 1)),
                         Image.LANCZOS)
    return out


PROMPT = """You are reading ONE HORIZONTAL SLICE of a hand-filled paper table.

The image has the table's COLUMN HEADER at the top, and below it a few DATA
ROWS from further down the same table. The header is there so you know which
column is which — do NOT transcribe the header as a data row.

The printed leftmost column is the row's ID. Every output line MUST start with
that printed ID, so the row can be matched back to the form.

COPY EACH ID EXACTLY AS PRINTED. On these forms the IDs are frequently NOT
consecutive — rows are skipped, so 5 may be followed by 7, and 25 by 27. Never
renumber, never "repair" a gap, never emit a row whose ID you cannot actually
see printed on this slice.

READING THE HANDWRITING IS THE ENTIRE TASK. The printed columns are easy and
are not the point. The handwritten cells are the data.

NEVER INVENT A VALUE. If you cannot read a cell, emit an EMPTY field for it.
An empty field is an honest signal that a human must look; a guess silently
corrupts the dataset. Do not copy the value from the row above, and do not fall
back on whatever value is most common in that column.

If the table prints a legend or scoring key, use it to constrain each column's
legal values. Columns under one group heading may still hold different value
types — work each column out from its own sub-header.

Output ONLY CSV, one line per DATA ROW.

FIXED WIDTH: count the columns in the header, then emit EXACTLY that many
comma-separated fields on EVERY line, in left-to-right order — the ID first,
then one field per remaining column. Emit empty fields for cells you cannot
read, so that every line has the same number of fields and the columns stay
aligned. A line with a different field count cannot be matched to the form and
is discarded. No prose, no fences, no header line.
"""


def run(form_dir: Path, provider: str, model: str, rows_per_band: int,
        zoom: float, dpi: int, pages: list[int] | None = None,
        keep_frac: list[tuple[float, float]] | None = None):
    pdf = form_dir / "input.pdf"
    import fitz
    n = fitz.open(str(pdf)).page_count
    todo = pages or list(range(n))
    lines, cost, in_tok, out_tok = [], 0.0, 0, 0
    t0 = time.time()
    sender = wide_bench.PROVIDERS[provider]
    saved = wide_bench.TRANSCRIBE_PROMPT
    wide_bench.TRANSCRIBE_PROMPT = PROMPT
    tmp = form_dir / "_bands"; tmp.mkdir(exist_ok=True)
    try:
        for pno in todo:
            im = render(pdf, pno, dpi)
            hdr, bs = bands(im, rows_per_band)
            keep = ([(int(a * im.width), int(b * im.width)) for a, b in keep_frac]
                    if keep_frac else None)
            for i, b in enumerate(bs):
                f = tmp / f"p{pno+1}_b{i:02}.png"
                stack(im, hdr, b, zoom, keep=keep).save(f)
                for attempt in range(3):
                    try:
                        text, meta = sender(model, [f], endpoint=None)
                        break
                    except Exception as e:               # noqa: BLE001
                        if attempt == 2:
                            raise
                        time.sleep(4)
                cost += meta.get("cost_usd") or 0
                in_tok += meta.get("in_tok") or 0
                out_tok += meta.get("out_tok") or 0
                lines.append(text.strip())
    finally:
        wide_bench.TRANSCRIBE_PROMPT = saved
    return "\n".join(lines), {"cost_usd": round(cost, 5), "in_tok": in_tok,
                              "out_tok": out_tok,
                              "latency_s": round(time.time() - t0, 1),
                              "bands": len(lines)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--provider", default="gemini")
    ap.add_argument("--model", required=True)
    ap.add_argument("--rows-per-band", type=int, default=8)
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--pages", default=None, help="comma list, 0-based")
    ap.add_argument("--tag", default="band")
    ap.add_argument("--keep-frac", default=None,
                    help="x-ranges to keep as fractions, e.g. '.108-.155,.40-.808'. "
                         "Drops wide text columns so the narrow code columns get "
                         "the width budget. Blind vertical-rule detection does NOT "
                         "work on skewed scans (see narrow_cols/vlines), so for now "
                         "this is supplied per form.")
    ap.add_argument("--dry-run", action="store_true",
                    help="write band crops and stop — inspect before paying")
    a = ap.parse_args()
    fd = Path(a.form).resolve()
    pages = [int(x) for x in a.pages.split(",")] if a.pages else None
    if a.dry_run:
        im = render(fd / "input.pdf", (pages or [0])[0], a.dpi)
        hdr, bs = bands(im, a.rows_per_band)
        tmp = fd / "_bands"; tmp.mkdir(exist_ok=True)
        print(f"header box {hdr}, {len(bs)} bands")
        for i, b in enumerate(bs[:3]):
            p = tmp / f"dry_b{i:02}.png"
            stack(im, hdr, b, a.zoom).save(p)
            print(" ", p, Image.open(p).size)
        raise SystemExit
    kf = ([tuple(float(v) for v in seg.split("-"))
           for seg in a.keep_frac.split(",")] if a.keep_frac else None)
    text, meta = run(fd, a.provider, a.model, a.rows_per_band, a.zoom, a.dpi,
                     pages, kf)
    out = fd / "outputs"; out.mkdir(exist_ok=True)
    tag = f"{a.provider}__{a.model.replace('/','_')}__{a.tag}"
    (out / f"{tag}.txt").write_text(text)
    wide_bench.text_to_xlsx(text, out / f"{tag}.xlsx")
    print(json.dumps({"tag": tag, **meta}))
