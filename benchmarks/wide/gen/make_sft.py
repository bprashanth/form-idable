#!/usr/bin/env python3
"""Build an SFT JSONL for vision fine-tuning from generated train_forms.

Each sample: all page images of one form (rendered like the bench overview:
native res capped at 1568px longest edge) -> the golden transcription as CSV
text (identical format to what wide_bench's TRANSCRIBE_PROMPT requests, so the
tuned model is trained on exactly the eval task).

Usage: python3 make_sft.py <train_forms_root> <out_dir>
Writes <out_dir>/sft.jsonl and <out_dir>/images/...
"""
import json, sys
from pathlib import Path

import fitz
import openpyxl

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from wide_bench import TRANSCRIBE_PROMPT  # noqa: E402

MAX_DIM = 1568


def golden_to_csv(xlsx: Path) -> str:
    wb = openpyxl.load_workbook(xlsx)
    lines = ["### PAGE 1"]
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            cells = ["" if c is None else str(c) for c in row]
            while cells and cells[-1] == "":
                cells.pop()
            if cells:
                lines.append(",".join(
                    f'"{c}"' if ("," in c or '"' in c) else c
                    for c in (x.replace('"', "'") for x in cells)))
    return "\n".join(lines)


def render_pages(pdf: Path, out_dir: Path, stem: str) -> list[str]:
    out = []
    doc = fitz.open(str(pdf))
    for i, page in enumerate(doc, 1):
        # native embedded-image resolution, capped at MAX_DIM (as render_page.py)
        scale = 1.0
        imgs = page.get_images(full=True)
        if imgs:
            w = max(doc.extract_image(x[0]).get("width", 0) for x in imgs)
            if w and page.rect.width:
                scale = w / page.rect.width
        pix_w = page.rect.width * scale
        pix_h = page.rect.height * scale
        if max(pix_w, pix_h) > MAX_DIM:
            scale *= MAX_DIM / max(pix_w, pix_h)
        pm = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        dst = out_dir / f"{stem}_p{i}.png"
        pm.save(str(dst))
        out.append(str(dst))
    doc.close()
    return out


def main(root: Path, out_dir: Path):
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    # any directory holding input.pdf + golden.xlsx, at any depth
    form_dirs = sorted({p.parent for p in root.rglob("input.pdf")})
    with open(out_dir / "sft.jsonl", "w") as f:
        for form_dir in form_dirs:
            pdf, gold = form_dir / "input.pdf", form_dir / "golden.xlsx"
            if not (pdf.exists() and gold.exists()):
                continue
            rel = form_dir.relative_to(root)
            stem = "__".join(rel.parts)
            images = render_pages(pdf, img_dir, stem)
            f.write(json.dumps({"images": images,
                                "prompt": TRANSCRIBE_PROMPT,
                                "response": golden_to_csv(gold)}) + "\n")
            n += 1
    print(f"wrote {n} samples -> {out_dir/'sft.jsonl'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
