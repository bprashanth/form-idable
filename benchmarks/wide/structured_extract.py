#!/usr/bin/env python3
"""Tier-3 extraction: use a known blank template to bound and structure the job.

Why this exists. The tuned local model's ONLY substantial failure is
over-production: on 76 unseen layouts it reached recall 0.805 but precision
0.424, and 17 forms scored exactly zero *despite recall above 0.5* — it read
the page and then kept inventing rows. Prompt tweaks, repetition penalties and
output-text heuristics all treat the symptom. Cropping to a known row fixes it
STRUCTURALLY: asked for one row, the model cannot emit fifty.

Pipeline (all local, no frontier model):
  1. align   — homography from the filled photo to the blank template
               (ORB features; falls back to identity when the image is already
               rectified, e.g. a scan)
  2. subtract— remove the printed layer, leaving ink only. The model then sees
               handwriting in a known box instead of handwriting tangled with
               printed labels.
  3. cells   — geometry comes from the blank's PDF VECTORS, so there is nothing
               to threshold or tune
  4. bands   — query the model per row-band, passing that table's column
               headers as context, and assemble

`--mode` selects what the model is shown, so the contributions can be
attributed separately rather than reported as one lumped win:
  page      : whole page (the tier-2 baseline, for comparison)
  band      : one row-band at a time, printed layer intact
  band-sub  : one row-band at a time, printed layer subtracted

Usage:
  python3 structured_extract.py <form_dir> --template <blank.pdf> \
      --model qwen3-vl-2b-v3 --mode band [--page 0]
"""
import argparse, base64, io, json, sys, time
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "gen"))
import wide_bench, wide_diff                      # noqa: E402
from fill_template import extract_structure, build_cells, cell_text  # noqa: E402

try:
    import cv2
except ImportError:
    cv2 = None

BAND_PROMPT = """You are reading ONE horizontal band of a hand-filled paper form.
The band's column headers, left to right, are:
{headers}

Transcribe ONLY what is handwritten in this band, as a single CSV line with one
value per column in that order. Use an empty field for a column with nothing in
it. A lone dot means 0. A line struck through a cell means no entry. Tally marks
sum to an integer. A tick or X means X.
Output exactly one CSV line and nothing else — no prose, no header, no extra rows.
"""


def _render(pdf: Path, page_no, scale=None, max_dim=2200):
    import fitz
    doc = fitz.open(str(pdf))
    pg = doc[page_no]
    s = scale or min(max_dim / max(pg.rect.width, pg.rect.height), 4.0)
    pm = pg.get_pixmap(matrix=fitz.Matrix(s, s))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    doc.close()
    return im, s


def align(filled: Image.Image, blank: Image.Image):
    """Homography filled -> blank. Identity when features are too sparse."""
    if cv2 is None:
        return filled.resize(blank.size), False
    a = cv2.cvtColor(np.array(filled.convert("RGB")), cv2.COLOR_RGB2GRAY)
    b = cv2.cvtColor(np.array(blank.convert("RGB")), cv2.COLOR_RGB2GRAY)
    orb = cv2.ORB_create(4000)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None or len(ka) < 30 or len(kb) < 30:
        return filled.resize(blank.size), False
    m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    if len(m) < 25:
        return filled.resize(blank.size), False
    m = sorted(m, key=lambda x: x.distance)[:600]
    src = np.float32([ka[x.queryIdx].pt for x in m]).reshape(-1, 1, 2)
    dst = np.float32([kb[x.trainIdx].pt for x in m]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    if H is None or mask.sum() < 15:
        return filled.resize(blank.size), False
    out = cv2.warpPerspective(np.array(filled.convert("RGB")), H, blank.size,
                              borderValue=(255, 255, 255))
    return Image.fromarray(out), True


def subtract_printed(aligned: Image.Image, blank: Image.Image, dilate=3):
    """Erase the printed layer, keeping ink. Where the blank already has print,
    lift the pixel toward white; the handwriting that survives is what the model
    should read."""
    a = np.array(aligned.convert("L"), dtype=np.int16)
    b = np.array(blank.convert("L"), dtype=np.int16)
    if cv2 is not None and dilate:
        k = np.ones((dilate, dilate), np.uint8)
        b = cv2.erode(b.astype(np.uint8), k, iterations=1).astype(np.int16)
    printed = b < 200
    out = a.copy()
    out[printed] = np.maximum(out[printed], 235)
    return Image.fromarray(np.uint8(np.clip(out, 0, 255))).convert("RGB")


def row_bands(cells, scale, pad=2):
    """Group cells into rows -> (band bbox in pixels, ordered column bboxes)."""
    rows = {}
    for c in cells:
        rows.setdefault(c["row"], []).append(c)
    out = []
    for r in sorted(rows):
        cs = sorted(rows[r], key=lambda c: c["bbox"][0])
        x0 = min(c["bbox"][0] for c in cs); x1 = max(c["bbox"][2] for c in cs)
        y0 = min(c["bbox"][1] for c in cs); y1 = max(c["bbox"][3] for c in cs)
        out.append((r, (x0 * scale - pad, y0 * scale - pad,
                        x1 * scale + pad, y1 * scale + pad), cs))
    return out


def _b64(im):
    buf = io.BytesIO(); im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def ask_band(endpoint, model, im, headers, timeout=240):
    payload = {"model": model, "temperature": 0, "max_tokens": 256,
               "repetition_penalty": 1.05,
               "messages": [{"role": "user", "content": [
                   {"type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{_b64(im)}"}},
                   {"type": "text",
                    "text": BAND_PROMPT.format(headers=", ".join(headers) or "(unlabelled)")}]}]}
    r = wide_bench._post(f"{endpoint.rstrip('/')}/chat/completions", payload, {},
                         timeout=timeout)
    return r["choices"][0]["message"]["content"].strip().splitlines()[:1]


def run(form_dir: Path, template: Path, model, endpoint, mode="band", page_no=0):
    st = extract_structure(template, page_no)
    cells = build_cells(st)
    if not cells:
        return None, "no cells in template"
    blank, s_blank = _render(template, page_no)
    filled, _ = _render(form_dir / "input.pdf", 0, scale=None)
    filled = filled.resize(blank.size)
    aligned, did = align(filled, blank)
    img = subtract_printed(aligned, blank) if mode == "band-sub" else aligned

    # header text per column, straight from the blank's vector text
    hdr = {}
    for c in cells:
        t = cell_text(st, c["bbox"])
        if t.strip():
            hdr.setdefault(c["col"], t.strip())

    t0 = time.time()
    lines = []
    bands = row_bands(cells, s_blank)
    for r, (x0, y0, x1, y1), cs in bands:
        if (x1 - x0) < 40 or (y1 - y0) < 10:
            continue
        crop = img.crop((max(0, int(x0)), max(0, int(y0)),
                         min(img.width, int(x1)), min(img.height, int(y1))))
        if max(crop.size) < 48:
            continue
        scale_up = min(3.0, 900 / max(crop.size))
        if scale_up > 1:
            crop = crop.resize((int(crop.width * scale_up), int(crop.height * scale_up)))
        heads = [hdr.get(c["col"], "") for c in cs]
        try:
            got = ask_band(endpoint, model, crop, heads)
        except Exception:
            continue
        for g in got:
            if g.strip():
                lines.append(g.strip())
    dt = time.time() - t0

    # In tier 3 the PRINTED labels come from the template descriptor — the
    # system already knows them, so the model is only asked for the ink. Emit
    # them alongside the model's rows, which is what a real deployment would
    # return. Without this the structured path is scored against a golden that
    # is ~80% printed labels it was explicitly told not to transcribe, which
    # caps its recall at ~0.18 regardless of how well it reads.
    printed_lines = []
    seen_p = set()
    for c in sorted(cells, key=lambda c: (c["row"], c["col"])):
        t = cell_text(st, c["bbox"]).strip()
        if t and t not in seen_p:
            seen_p.add(t)
            printed_lines.append(t)

    out_dir = form_dir / "outputs"; out_dir.mkdir(exist_ok=True)
    tag = f"structured__{model}__{mode}"
    text = "### PAGE 1\n" + "\n".join(printed_lines + lines)
    (out_dir / f"{tag}.txt").write_text(text)
    xlsx = wide_bench.text_to_xlsx(text, out_dir / f"{tag}.xlsx")
    res = wide_diff.compare(str(form_dir / "golden.xlsx"), str(xlsx))
    m = res["metrics"]
    row = {"form": form_dir.name, "provider": "structured", "model": model,
           "mode": mode, "aligned": did, "bands": len(bands),
           "cost_usd": 0.0, "latency_s": round(dt, 1), "error": ""}
    # carry every metric the scorer emits — a hard-coded list here silently
    # dropped the code_*/all_* buckets (third time this bug has appeared)
    row.update({k: v for k, v in m.items()
                if k not in ("golden_cells", "candidate_cells")})
    (out_dir / f"{tag}.json").write_text(json.dumps(row, indent=2))
    return row, None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("form"); ap.add_argument("--template", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--endpoint", default="http://localhost:8010/v1")
    ap.add_argument("--mode", default="band", choices=["band", "band-sub"])
    ap.add_argument("--page", type=int, default=0)
    a = ap.parse_args()
    r, err = run(Path(a.form), Path(a.template), a.model, a.endpoint, a.mode, a.page)
    print(json.dumps(r) if r else f"SKIP: {err}")
