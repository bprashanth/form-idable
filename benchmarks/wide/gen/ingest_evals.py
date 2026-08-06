#!/usr/bin/env python3
"""Blind-ingest eval forms: copy every PDF/image under a source dir into
anonymized eval_forms/eval_NN/input.pdf dirs.

Prints ONLY aggregate facts (counts, page counts, image dimensions) — never
filenames or content. The original-name mapping goes to source_map.json inside
each dir for human traceability; the driving agent does not read it.

Ordering is by content hash, so eval_NN numbering leaks nothing about names.

Usage: python3 ingest_evals.py <src_dir> <out_root>
"""
import hashlib, json, sys
from pathlib import Path

import fitz

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}

files = sorted((p for p in SRC.rglob("*") if p.suffix.lower() in EXTS),
               key=lambda p: hashlib.sha256(p.read_bytes()).hexdigest())
if not files:
    print("0 eval files found"); sys.exit(1)

OUT.mkdir(parents=True, exist_ok=True)
report = []
for i, src in enumerate(files, 1):
    d = OUT / f"eval_{i:02d}"
    d.mkdir(exist_ok=True)
    dst = d / "input.pdf"
    if src.suffix.lower() == ".pdf":
        dst.write_bytes(src.read_bytes())
    else:
        img = fitz.open(str(src))
        pdf = fitz.open()
        rect = img[0].rect
        page = pdf.new_page(width=rect.width, height=rect.height)
        page.insert_image(rect, filename=str(src))
        pdf.save(str(dst)); pdf.close(); img.close()
    doc = fitz.open(str(dst))
    n_pages = doc.page_count
    dims = [(round(p.rect.width), round(p.rect.height)) for p in doc]
    doc.close()
    (d / "source_map.json").write_text(json.dumps(
        {"original_path": str(src), "sha256": hashlib.sha256(src.read_bytes()).hexdigest()},
        indent=2))
    (d / "provenance.md").write_text(
        f"# {d.name}\n\nReal partner eval form (tree/ecology domain), ingested "
        f"blind from the project evals directory (original name withheld from "
        f"the driving agent; see source_map.json).\nGolden: multi-converter "
        f"consensus (gemini-3.6-flash, qwen3-vl-32b, codex CLI) adjudicated "
        f"cell-by-cell by an Opus 5 agent against the scan; QA spot-checked.\n"
        f"FROZEN EVAL — never used for training.\n")
    report.append({"id": d.name, "pages": n_pages, "dims": dims})

print(f"{len(files)} eval files ingested -> {OUT}")
for r in report:
    print(f"  {r['id']}: {r['pages']} page(s) {r['dims']}")
