#!/usr/bin/env python3
"""Convert a FUNSD sample into a wide-bench form dir.

FUNSD annotations carry the ground-truth text of every field (question/answer/
header/other) — we build the golden xlsx from them programmatically:
question->answer linked pairs become [q, a] rows (matching the prompt's
"label,value" CSV shape); headers and unlinked text become single-cell rows.
The PNG scan is embedded as input.pdf.

Usage: python3 funsd_to_form.py <image.png> <annotation.json> <out_form_dir> "<provenance note>"
"""
import json, sys
from pathlib import Path

import fitz
import openpyxl


def convert(img_path: Path, ann_path: Path, out_dir: Path, note: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    ann = json.loads(ann_path.read_text())["form"]
    by_id = {e["id"]: e for e in ann}

    answered = set()          # answer ids consumed by a question link
    rows = []
    for e in ann:
        if e["label"] != "question":
            continue
        answers = [l[1] for l in e.get("linking", []) if l[0] == e["id"] and l[1] in by_id]
        texts = [by_id[a]["text"] for a in answers if by_id[a]["text"].strip()]
        answered.update(answers)
        if e["text"].strip():
            rows.append([e["text"]] + texts)
    for e in ann:
        if e["label"] == "question" or e["id"] in answered:
            continue
        if e["text"].strip():
            rows.append([e["text"]])

    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "form"
    for r in rows:
        ws.append(r)
    wb.save(out_dir / "golden.xlsx")

    doc = fitz.open()
    img = fitz.open(str(img_path))
    rect = img[0].rect
    page = doc.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, filename=str(img_path))
    doc.save(out_dir / "input.pdf"); doc.close(); img.close()

    (out_dir / "provenance.md").write_text(
        f"# {out_dir.name}\n\nSource: FUNSD dataset (Jaume et al., ICDAR-OST 2019), "
        f"sample {img_path.name}.\nReal scanned business form (RVL-CDIP subset); "
        f"non-commercial research use.\nGolden built programmatically from FUNSD "
        f"annotations (question->answer links).\n\n{note}\n")
    print(f"{out_dir.name}: {len(rows)} golden rows")


if __name__ == "__main__":
    convert(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]),
            sys.argv[4] if len(sys.argv) > 4 else "")
