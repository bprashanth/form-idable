#!/usr/bin/env python3
"""Reread only canonical cells on which independent extractors disagree."""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import canonical  # noqa: E402
import structured_pipeline as pipeline  # noqa: E402


DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "decisions": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "table_id": {"type": "string"},
                "row_id": {"type": "string"},
                "column_id": {"type": "string"},
                "value": {"type": ["string", "null"]},
                "confidence": {"type": "number"},
                "evidence": {"type": "string"},
            },
            "required": ["table_id", "row_id", "column_id", "value",
                         "confidence", "evidence"],
            "additionalProperties": False,
        }},
    }, "required": ["decisions"], "additionalProperties": False,
}


PROMPT = """You are the targeted visual reread stage of a paper-form digitizer.
Two independent extractors disagreed on the cells listed below. Reread ONLY
those cells from the high-resolution column strips. Every strip shows the full
page height: a left anchor panel containing printed row identifiers/species and
a right panel containing a small group of disputed columns. First locate the
literal target row_id in the anchor panel, then follow the same ruled row into
the disputed column panel. Account for page skew; do not use a model-estimated
row number or choose a neighbouring row. The candidates are hints to locate
ambiguity, not facts.

Return exactly one decision for every listed target. Copy the literal mark as
the form intends: lone dot used as a value is 0, continuous strike-through is
blank, tally marks are counted, and checked boxes are X. Preserve multi-value
notations. Never choose a candidate because it is common, sequential,
ecologically plausible, or inside an expected domain. If the pixels do not
support a reading, return null with evidence `unreadable`. This stage performs
no ecological correction.

Targets use zero-based image_index into the attached images:
{targets}
"""


def _clip(page, region, scale=4.0) -> Image.Image:
    x0, y0, x1, y1 = region
    rect = page.rect
    clip = fitz.Rect(rect.x0 + x0 * rect.width, rect.y0 + y0 * rect.height,
                     rect.x0 + x1 * rect.width, rect.y0 + y1 * rect.height)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def _row_image(page, table, row, target_indices) -> Image.Image:
    columns = table["columns"]
    # Model-estimated row boxes can be displaced by one ruled row after a
    # skipped/non-consecutive identifier. Keep enough vertical context for the
    # adjudicator to recover via the printed row ID instead of guessing an
    # offset. The identical y-range on both panels preserves horizontal
    # alignment.
    row_height = row["bbox"][3] - row["bbox"][1]
    pad_y = max(0.006, row_height * 1.5)
    y0, y1 = max(0, row["bbox"][1] - pad_y), min(1, row["bbox"][3] + pad_y)
    anchor_end = columns[min(1, len(columns) - 1)]["x1"]
    anchor = [table["bbox"][0], y0, anchor_end, y1]
    target = [max(0, min(columns[index]["x0"] for index in target_indices) - .008), y0,
              min(1, max(columns[index]["x1"] for index in target_indices) + .008), y1]
    regions = [anchor]
    if target[0] > anchor[2] - .01:
        regions.append(target)
    else:
        regions = [[min(anchor[0], target[0]), y0, max(anchor[2], target[2]), y1]]
    crops = [_clip(page, region) for region in regions]
    separator = 12 if len(crops) > 1 else 0
    width = sum(image.width for image in crops) + separator
    height = max(image.height for image in crops)
    content = Image.new("RGB", (width, height), "white")
    x = 0
    for crop in crops:
        content.paste(crop, (x, 0))
        x += crop.width + separator
    max_width = 1800
    if content.width > max_width:
        ratio = max_width / content.width
        content = content.resize((max_width, max(1, int(content.height * ratio))), Image.LANCZOS)
    label = (f"TARGET row_id={row['id']} (find in left panel; ignore neighbours) | disputed: "
             + ", ".join(columns[index]["label"] for index in target_indices))
    header_h = 28
    output = Image.new("RGB", (content.width, content.height + header_h), "white")
    output.paste(content, (0, header_h))
    ImageDraw.Draw(output).text((6, 6), label, fill="black", font=ImageFont.load_default())
    return output


def _column_image(page, table, target_indices) -> Image.Image:
    """Render all rows for anchor + disputed columns; never trust model row y."""
    columns = table["columns"]
    anchor_end = columns[min(1, len(columns) - 1)]["x1"]
    anchor = [max(0, table["bbox"][0] - .008), 0, min(1, anchor_end + .008), 1]
    target = [max(0, min(columns[index]["x0"] for index in target_indices) - .012), 0,
              min(1, max(columns[index]["x1"] for index in target_indices) + .012), 1]
    regions = [anchor]
    if target[0] > anchor[2] - .01:
        regions.append(target)
    else:
        regions = [[min(anchor[0], target[0]), 0, max(anchor[2], target[2]), 1]]
    crops = [_clip(page, region) for region in regions]
    separator = 16 if len(crops) > 1 else 0
    width = sum(image.width for image in crops) + separator
    height = max(image.height for image in crops)
    content = Image.new("RGB", (width, height), "white")
    x = 0
    for crop in crops:
        content.paste(crop, (x, 0))
        x += crop.width + separator
    # Keep enough resolution for small handwriting while staying below common
    # multimodal image limits. Most strips are narrower than this already.
    max_width, max_height = 2400, 4200
    ratio = min(1.0, max_width / content.width, max_height / content.height)
    if ratio < 1:
        content = content.resize((max(1, int(content.width * ratio)),
                                  max(1, int(content.height * ratio))), Image.LANCZOS)
    labels = ", ".join(columns[index]["label"] for index in target_indices)
    header_h = 32
    output = Image.new("RGB", (content.width, content.height + header_h), "white")
    output.paste(content, (0, header_h))
    ImageDraw.Draw(output).text(
        (6, 7), f"FULL-HEIGHT ANCHOR + DISPUTED COLUMNS: {labels}",
        fill="black", font=ImageFont.load_default())
    if len(crops) > 1:
        draw = ImageDraw.Draw(output)
        split_x = crops[0].width + separator // 2
        draw.line((split_x, header_h, split_x, output.height), fill=(220, 0, 0), width=3)
    return output


def _composite(images: list[Image.Image]) -> Image.Image:
    width = max(image.width for image in images)
    height = sum(image.height for image in images) + 4 * (len(images) - 1)
    output = Image.new("RGB", (width, height), "white")
    y = 0
    draw = ImageDraw.Draw(output)
    for image in images:
        output.paste(image, (0, y))
        y += image.height
        draw.line((0, y + 1, width, y + 1), fill=(220, 0, 0), width=2)
        y += 4
    return output


def build_crops(document, pdf_path: Path, output: Path, columns_per_image=4):
    """Build full-height evidence strips and map every disputed cell to one."""
    doc = fitz.open(pdf_path)
    targets, images = [], []
    for page_data in document["pages"]:
        page = doc[page_data["page_number"] - 1]
        for table in page_data["tables"]:
            disputed_indices = set()
            for row in table["rows"]:
                disputed_indices.update(index for index, cell in enumerate(row["cells"])
                                          if cell.get("status") == "disagreement")
            image_for_column = {}
            ordered = sorted(disputed_indices)
            for start in range(0, len(ordered), columns_per_image):
                indices = ordered[start:start + columns_per_image]
                image_index = len(images)
                strip = _column_image(page, table, indices)
                path = output / (f"page_{page_data['page_number']}__columns_"
                                 f"{indices[0]:02d}_{indices[-1]:02d}.png")
                strip.save(path)
                images.append(path)
                for index in indices:
                    image_for_column[index] = image_index
            for row in table["rows"]:
                for index, cell in enumerate(row["cells"]):
                    if cell.get("status") == "disagreement":
                        cell = row["cells"][index]
                        targets.append({
                            "page": page_data["page_number"],
                            "table_id": table["id"],
                            "row_id": row["id"],
                            "column_id": cell["column_id"],
                            "header": table["columns"][index]["label"],
                            "parent": table["columns"][index].get("parent"),
                            "candidates": [reading.get("value") for reading in cell["readings"]],
                            "image_index": image_for_column[index],
                        })
    doc.close()
    return targets, images


def apply_decisions(document, decisions, model):
    lookup = {}
    for page in document["pages"]:
        for table in page["tables"]:
            for row in table["rows"]:
                for cell in row["cells"]:
                    lookup[(page["page_number"], table["id"], row["id"],
                            cell["column_id"])] = cell
    applied = missing = 0
    for decision in decisions:
        page_number = int(decision.get("page") or 0)
        # The response schema omits page because calls are made per page; the
        # caller injects it before this function.
        key = (page_number, canonical.slug(decision.get("table_id"), ""),
               str(decision.get("row_id") or ""),
               canonical.slug(decision.get("column_id"), ""))
        cell = lookup.get(key)
        if cell is None:
            missing += 1
            continue
        try:
            confidence = max(0.0, min(1.0, float(decision.get("confidence") or 0)))
        except (TypeError, ValueError):
            confidence = 0.0
        cell["readings"].append({
            "model": f"{model}:targeted_reread",
            "value": decision.get("value"),
            "confidence": round(confidence, 4),
            "illegible": decision.get("evidence") == "unreadable",
            "bbox": cell["bbox"],
        })
        applied += 1
    canonical.resolve(document)
    return applied, missing


def run(form_dir: Path, source_tag: str, model: str, tag: str, thinking="low"):
    source = form_dir / "canonical_outputs" / source_tag
    output = form_dir / "canonical_outputs" / tag
    output.mkdir(parents=True, exist_ok=True)
    document = json.loads((source / "canonical.json").read_text())
    # Re-resolve in case normalization changed since the source run.
    canonical.resolve(document)

    targets, images = build_crops(document, form_dir / "input.pdf", output)
    by_page = defaultdict(list)
    for target in targets:
        by_page[target["page"]].append(target)
    decisions, calls = [], []
    for page_number, page_targets in sorted(by_page.items()):
        image_ids = sorted({target["image_index"] for target in page_targets})
        local_index = {global_id: index for index, global_id in enumerate(image_ids)}
        prompt_targets = []
        for target in page_targets:
            item = dict(target)
            item["image_index"] = local_index[item["image_index"]]
            item.pop("page", None)
            prompt_targets.append(item)
        response_path = output / f"page_{page_number}__reread__{model}.json"
        meta_path = output / f"page_{page_number}__reread__{model}.meta.json"
        if response_path.exists() and meta_path.exists():
            raw = json.loads(response_path.read_text())
            meta = json.loads(meta_path.read_text())
            print(f"page {page_number}: resuming saved response", flush=True)
        else:
            raw, meta = pipeline.gemini_json(
                model, PROMPT.format(targets=json.dumps(prompt_targets, ensure_ascii=False)),
                [images[index] for index in image_ids], DECISION_SCHEMA, thinking=thinking)
            response_path.write_text(json.dumps(raw, indent=2))
            meta_path.write_text(json.dumps(meta, indent=2))
        calls.append({"stage": "targeted_reread", "page": page_number, **meta})
        page_decisions = raw.get("decisions") or []
        for decision in page_decisions:
            decision["page"] = page_number
        decisions.extend(page_decisions)
        print(f"page {page_number}: requested {len(page_targets)}, returned "
              f"{len(page_decisions)} decisions", flush=True)

    applied, missing = apply_decisions(document, decisions, model)
    report = {
        "form": form_dir.name, "source_tag": source_tag, "tag": tag,
        "model": model, "thinking": thinking,
        "targets": len(targets), "decisions": len(decisions),
        "applied": applied, "missing": missing,
        "calls": calls,
        "cost_usd": round(sum(call.get("cost_usd") or 0 for call in calls), 5),
        "latency_s": round(sum(call.get("latency_s") or 0 for call in calls), 1),
        "disagreement": pipeline.disagreement_stats(document),
        "validation_errors": canonical.validate(document),
    }
    document["reread_run"] = report
    canonical.dump(document, output / "canonical.json")
    canonical.write_xlsx(document, output / "output.xlsx")
    (output / "run.json").write_text(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--form", required=True)
    parser.add_argument("--source-tag", default="canonical_v1_full")
    parser.add_argument("--model", default="gemini-3.1-pro-preview")
    parser.add_argument("--thinking", default="low")
    parser.add_argument("--tag", default="canonical_v1_reread_pro")
    args = parser.parse_args()
    print(json.dumps(run(Path(args.form).resolve(), args.source_tag, args.model,
                         args.tag, args.thinking), indent=2))


if __name__ == "__main__":
    main()
