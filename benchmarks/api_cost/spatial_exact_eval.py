#!/usr/bin/env python3
"""Score canonical output against synthetic writable cells by page geometry.

Alignment is visual only: values never influence matching.  A ground-truth
cell is assigned to the smallest canonical region containing its centre (or
the region with greatest overlap), which makes omissions and false fills
visible without requiring the model to reproduce source spreadsheet indexes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def norm(value) -> str:
    text = "" if value is None else " ".join(str(value).strip().split()).casefold()
    if not text:
        return ""
    try:
        number = float(text)
        return str(int(number)) if math.isfinite(number) and number.is_integer() else str(number)
    except ValueError:
        return text


def area(box) -> float:
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def overlap(a, b) -> float:
    intersection = (max(0, min(a[2], b[2]) - max(a[0], b[0]))
                    * max(0, min(a[3], b[3]) - max(a[1], b[1])))
    return intersection / area(a) if area(a) else 0.0


def predictions(document: dict) -> list[dict]:
    out = []
    for page in document.get("pages") or []:
        number = page["page_number"]
        for item in [*(page.get("metadata_fields") or []),
                     *(page.get("free_text_regions") or [])]:
            out.append({"page": number, "bbox": item.get("bbox"),
                        "value": item.get("value"), "status": item.get("status"),
                        "confidence": item.get("confidence")})
        for table in page.get("tables") or []:
            for row in table.get("rows") or []:
                for cell in row.get("cells") or []:
                    out.append({"page": number, "bbox": cell.get("bbox"),
                                "value": cell.get("value"), "status": cell.get("status"),
                                "confidence": cell.get("confidence")})
    return [item for item in out if item.get("bbox") and len(item["bbox"]) == 4]


def evaluate(form_dir: Path, canonical_path: Path) -> dict:
    truth_payload = json.loads((form_dir / "ground_truth.json").read_text())
    truth = [cell for cell in truth_payload["cells"]
             if cell.get("source") in {"written", "blank"}]
    predicted = predictions(json.loads(canonical_path.read_text()))
    truth_pages = sorted({cell["page"] for cell in truth})
    predicted_pages = sorted({item["page"] for item in predicted})
    page_map = ({truth_pages[0]: predicted_pages[0]}
                if len(truth_pages) == len(predicted_pages) == 1 else {})
    matches = []
    for cell in truth:
        box = cell["bbox_norm"]
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        candidates = []
        for index, item in enumerate(predicted):
            if item["page"] != page_map.get(cell["page"], cell["page"]):
                continue
            pbox = item["bbox"]
            contains = pbox[0] <= cx <= pbox[2] and pbox[1] <= cy <= pbox[3]
            covered = overlap(box, pbox)
            if contains or covered >= .25:
                # Prefer full centre containment, then specific/small regions.
                candidates.append(((int(contains), covered, -area(pbox)), index, item))
        selected = max(candidates, default=None)
        item = selected[2] if selected else None
        expected, observed = norm(cell.get("value")), norm(item.get("value") if item else None)
        reviewed = bool(item and (float(item.get("confidence") or 0) <= .8
                                  or item.get("status") not in {None, "agreement"}))
        matches.append({
            "cell_id": f"r{cell['row']}_c{cell['col']}", "source": cell["source"],
            "expected": expected, "observed": observed, "matched": item is not None,
            "correct": observed == expected, "reviewed": reviewed,
        })
    written = [item for item in matches if item["source"] == "written" and item["expected"]]
    blanks = [item for item in matches if item["source"] == "blank"]
    errors = [item for item in matches if not item["correct"]]
    reviewed = [item for item in matches if item["reviewed"]]
    caught = [item for item in errors if item["reviewed"]]
    correct_written = sum(item["correct"] for item in written)
    false_fills = sum(bool(item["observed"]) for item in blanks)
    return {
        "version": "formidable-spatial-exact-eval-v1", "form": form_dir.name,
        "truth_cells": len(matches), "written": len(written), "blanks": len(blanks),
        "geometry_match_rate": round(sum(x["matched"] for x in matches) / len(matches), 4)
        if matches else None,
        "written_exact_recall": round(correct_written / len(written), 4) if written else None,
        "blank_specificity": round((len(blanks) - false_fills) / len(blanks), 4)
        if blanks else None,
        "errors": len(errors), "false_fills": false_fills,
        "reviewed": len(reviewed), "caught_errors": len(caught),
        "review_fraction": round(len(reviewed) / len(matches), 4) if matches else None,
        "error_capture": round(len(caught) / len(errors), 4) if errors else None,
        "queue_precision": round(len(caught) / len(reviewed), 4) if reviewed else None,
        "error_examples": [item for item in errors[:30]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("form", type=Path)
    parser.add_argument("canonical", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(args.form, args.canonical)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
