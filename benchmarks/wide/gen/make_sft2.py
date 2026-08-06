#!/usr/bin/env python3
"""Build the v2 SFT JSONL — trained on exactly the prompts used at eval time.

The benchmark runs two request shapes:
  * whole-form  (`TRANSCRIBE_PROMPT`, target keeps the `### PAGE N` markers)
  * per-page    (`PAGE_PROMPT`, one request per page; the harness adds the
                 `### PAGE N` marker itself, so the target must NOT repeat it)

Multi-page eval forms are scored per page, so most training weight goes to the
per-page shape; a share of whole-form samples keeps the model usable either way.

Each sample pairs the page image(s) with the golden transcription as CSV.

Usage: python3 make_sft2.py <corpus_root> <out_dir> [--perpage-frac 0.7]
"""
import json, random, sys
from pathlib import Path

import fitz
import openpyxl

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from wide_bench import TRANSCRIBE_PROMPT, PAGE_PROMPT  # noqa: E402

MAX_DIM = 1568


def golden_rows(xlsx: Path):
    wb = openpyxl.load_workbook(xlsx)
    lines = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cells = ["" if c is None else str(c) for c in row]
            while cells and cells[-1] == "":
                cells.pop()
            if cells:
                lines.append(",".join(
                    f'"{c}"' if ("," in c or '"' in c) else c
                    for c in (x.replace('"', "'") for x in cells)))
    return lines


def render_pages(pdf: Path, out_dir: Path, stem: str):
    out = []
    doc = fitz.open(str(pdf))
    for i, page in enumerate(doc, 1):
        scale = 1.0
        imgs = page.get_images(full=True)
        if imgs:
            w = max(doc.extract_image(x[0]).get("width", 0) for x in imgs)
            if w and page.rect.width:
                scale = w / page.rect.width
        pw, ph = page.rect.width * scale, page.rect.height * scale
        if max(pw, ph) > MAX_DIM:
            scale *= MAX_DIM / max(pw, ph)
        dst = out_dir / f"{stem}_p{i}.png"
        page.get_pixmap(matrix=fitz.Matrix(scale, scale)).save(str(dst))
        out.append(str(dst))
    doc.close()
    return out


def render_tiles(pdf: Path, out_dir: Path, stem: str):
    """Top/bottom halves at the vision cap — the shape the harness sends."""
    out = []
    doc = fitz.open(str(pdf))
    for i, page in enumerate(doc, 1):
        r = page.rect
        halves = []
        for h, (y0, y1) in enumerate([(0.0, 0.55), (0.45, 1.0)]):
            clip = fitz.Rect(r.x0, r.y0 + y0 * r.height, r.x1, r.y0 + y1 * r.height)
            scale = MAX_DIM / max(clip.width, clip.height)
            dst = out_dir / f"{stem}_p{i}_h{h}.png"
            page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip).save(str(dst))
            halves.append(str(dst))
        out.append(halves)
    doc.close()
    return out


def main(root: Path, out_dir: Path, perpage_frac=0.7):
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(0)
    n_form = n_samp = 0
    with open(out_dir / "sft.jsonl", "w") as f:
        for form_dir in sorted({p.parent for p in root.rglob("input.pdf")}):
            gold = form_dir / "golden.xlsx"
            if not gold.exists():
                continue
            stem = "__".join(form_dir.relative_to(root).parts)
            lines = golden_rows(gold)
            if not lines:
                continue
            if rng.random() < perpage_frac:
                # per-page shape: tiles of ONE page -> CSV without page marker
                tiles = render_tiles(form_dir / "input.pdf", img_dir, stem)
                # single-page corpus: the whole golden belongs to page 1
                for pi, halves in enumerate(tiles, 1):
                    if pi > 1:
                        break
                    f.write(json.dumps({"images": halves, "prompt": PAGE_PROMPT,
                                        "response": "\n".join(lines)}) + "\n")
                    n_samp += 1
            else:
                imgs = render_pages(form_dir / "input.pdf", img_dir, stem)
                f.write(json.dumps({
                    "images": imgs, "prompt": TRANSCRIBE_PROMPT,
                    "response": "### PAGE 1\n" + "\n".join(lines)}) + "\n")
                n_samp += 1
            n_form += 1
    print(f"{n_samp} samples from {n_form} forms -> {out_dir/'sft.jsonl'}")


if __name__ == "__main__":
    frac = 0.7
    for a in sys.argv:
        if a.startswith("--perpage-frac"):
            frac = float(a.split("=")[1])
    main(Path(sys.argv[1]), Path(sys.argv[2]), frac)
