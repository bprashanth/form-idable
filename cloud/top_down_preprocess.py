"""
Pre-process forms top down. See ../docs/ppalgorithms.md for details.

Usage: 
$ aws textract analyze-document   --region ap-south-1   --document '{"S3Object": {"Bucket":"<bucketname>","Name":"<dirname>/<filename>.jpg"}}'   --feature-types '["TABLES", "FORMS", "LAYOUT"]'   --output json > 001_layout.json

$ python3 ./top_down_preprocess.py --input 001_layout.json
"""
#!/usr/bin/env python3

import json
import argparse
import statistics
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# IO utils


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Text utils


def to_snake_case(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace("#", " number ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def join_clean(parts: List[str]) -> str:
    parts = [p for p in parts if p and p.strip()]
    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Geometry helpers


def bbox_center_x(bbox: Dict[str, float]) -> float:
    return bbox["x"] + bbox["w"] / 2.0


def bbox_bottom(bbox: Dict[str, float]) -> float:
    return bbox["y"] + bbox["h"]


def bbox_right(bbox: Dict[str, float]) -> float:
    return bbox["x"] + bbox["w"]


def vertical_overlap(a: Dict[str, float], b: Dict[str, float]) -> float:
    y1, y2 = a["y"], a["y"] + a["h"]
    Y1, Y2 = b["y"], b["y"] + b["h"]
    inter = max(0.0, min(y2, Y2) - max(y1, Y1))
    return inter / max(a["h"], b["h"], 1e-6)


def horizontal_gap(a: Dict[str, float], b: Dict[str, float]) -> float:
    # positive if b is to the right of a
    return b["x"] - (a["x"] + a["w"])

# Textract extraction


def extract_cells(textract_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    block_map = {b["Id"]: b for b in textract_data["Blocks"]}
    cells: List[Dict[str, Any]] = []
    for block in textract_data["Blocks"]:
        if block["BlockType"] != "CELL":
            continue

        text = ""
        if "Relationships" in block:
            for rel in block["Relationships"]:
                if rel["Type"] == "CHILD":
                    words = []
                    for w_id in rel["Ids"]:
                        w = block_map.get(w_id)
                        if w and w["BlockType"] == "WORD":
                            words.append(w.get("Text", ""))
                    text = " ".join(words).strip()

        bb = block["Geometry"]["BoundingBox"]
        cells.append({
            "row": block.get("RowIndex", -1),
            "col": block.get("ColumnIndex", -1),
            "colspan": block.get("ColumnSpan", 1),
            "text": text,
            "bbox": {"x": bb["Left"], "y": bb["Top"], "w": bb["Width"], "h": bb["Height"]},
            "confidence": block.get("Confidence", 100.0)
        })
    cells.sort(key=lambda c: (c["row"], c["col"]))
    return cells


def extract_lines(textract_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    lines: List[Dict[str, Any]] = []
    for block in textract_data["Blocks"]:
        if block["BlockType"] != "LINE":
            continue
        text = block.get("Text", "") or ""
        bb = block["Geometry"]["BoundingBox"]
        lines.append({
            "text": text.strip(),
            "bbox": {"x": bb["Left"], "y": bb["Top"], "w": bb["Width"], "h": bb["Height"]},
            "confidence": block.get("Confidence", 0.0)
        })
    # keep only meaningful lines
    lines = [l for l in lines if l["text"]]
    return lines

# Header detection


def detect_header_rows(cells: List[Dict[str, Any]], header_row_density: float) -> List[int]:
    row_cells = defaultdict(list)
    for c in cells:
        row_cells[c["row"]].append(c)

    if not row_cells:
        return [1]

    total_cols = max((c["col"] + c["colspan"] - 1) for c in cells)
    header_rows: List[int] = []

    for r in sorted(row_cells.keys()):
        row = row_cells[r]
        filled = sum(c["colspan"] for c in row if (c["text"] or "").strip())
        density = filled / max(1, total_cols)
        avg_conf = statistics.mean(c["confidence"] for c in row)
        has_span = any(c["colspan"] > 1 for c in row)
        texts = [c["text"] for c in row if (c["text"] or "").strip()]
        alpha_ratio = (sum(1 for t in texts if re.search(
            r"[A-Za-z]", t)) / (len(texts) or 1))
        avg_len = statistics.mean(len(t) for t in texts) if texts else 0
        text_rich = (alpha_ratio > 0.5 or avg_len > 3)

        if has_span or (avg_conf >= 85 and (density >= header_row_density or text_rich)):
            header_rows.append(r)
            continue

        if header_rows:
            # stop once we enter data zone
            break

    return sorted(set(header_rows)) or [1]

# Stitch split header fragments inside a header cell


def stitch_header_fragments(leaf_cell: Dict[str, Any], all_lines: List[Dict[str, Any]],
                            max_right_dx: float, min_v_overlap: float) -> str:
    base = (leaf_cell["text"] or "").strip()
    if not base or len(base) > 6:
        return base  # only attempt to stitch very short bases like "Soil"

    b = leaf_cell["bbox"]
    fragments = [base]
    for ln in all_lines:
        if ln["confidence"] < 85:
            continue
        # accept lines horizontally to the right, close by
        if 0.0 <= horizontal_gap(b, ln["bbox"]) <= max_right_dx:
            if vertical_overlap(b, ln["bbox"]) >= min_v_overlap:
                fragments.append(ln["text"])
    return join_clean(fragments)

# Header map (with floating parents)


def build_header_map(cells: List[Dict[str, Any]],
                     header_rows: List[int],
                     lines: List[Dict[str, Any]]) -> Dict[int, str]:
    header_map: Dict[int, str] = {}
    row_cells = defaultdict(list)
    for c in cells:
        if c["row"] in header_rows:
            row_cells[c["row"]].append(c)

    if not header_rows:
        return {}

    # tiers by row (top->bottom)
    tiers = []
    for r in sorted(header_rows):
        tier = []
        for c in row_cells[r]:
            tier.append({
                "start": c["col"],
                "end": c["col"] + c["colspan"] - 1,
                "text": c["text"],
                "bbox": c["bbox"]
            })
        tiers.append(tier)

    # bottom-most header row
    leaf_row = max(header_rows)
    leaf_cells = sorted(row_cells[leaf_row], key=lambda c: c["col"])
    total_cols = max(c["col"] for c in cells)

    # First pass: use cell text, with stitching for tiny bases
    leaf_texts: Dict[int, str] = {}
    # estimate a reasonable dx to the right (page-space) and vertical overlap
    avg_leaf_h = statistics.mean(c["bbox"]["h"]
                                 for c in leaf_cells) if leaf_cells else 0.02
    dx = 0.08  # generous page-relative tolerance to catch "Temper" "ature in"
    for c in leaf_cells:
        stitched = stitch_header_fragments(
            c, lines, max_right_dx=dx, min_v_overlap=0.5)
        leaf_texts[c["col"]] = stitched

    # Parent from CELL spans (if any)
    top_headers = []
    for tier in tiers[:-1]:
        for cell in tier:
            if cell["start"] < cell["end"]:  # actual span
                top_headers.append(cell)

    # Compose from explicit spans first
    for c in leaf_cells:
        ancestors = []
        for parent in top_headers:
            if parent["start"] <= c["col"] <= parent["end"]:
                ancestors.append(parent["text"])
        parts = [to_snake_case(p) for p in ancestors if (p or "").strip()]
        parts.append(to_snake_case(leaf_texts.get(c["col"], c["text"])))
        name = "_".join([p for p in parts if p]) or f"col_{c['col']}"
        header_map[c["col"]] = name

    # ---- Floating parent via LINEs (e.g., "Canopy Openness") ----
    # Build column centers for the leaf row
    col_centers: Dict[int, float] = {
        c["col"]: bbox_center_x(c["bbox"]) for c in leaf_cells}
    # Leaf band vertical position
    leaf_top = min(c["bbox"]["y"] for c in leaf_cells) if leaf_cells else 0.0
    leaf_h = statistics.mean(c["bbox"]["h"]
                             for c in leaf_cells) if leaf_cells else 0.02

    # Candidate lines: close above the leaf band
    parent_candidates: List[Dict[str, Any]] = []
    for ln in lines:
        if ln["confidence"] < 90:
            continue
        # within ~2 row heights above the leaf row
        if (leaf_top - 2.0 * leaf_h) <= bbox_bottom(ln["bbox"]) <= (leaf_top + 0.5 * leaf_h):
            parent_candidates.append(ln)

    # For each candidate, see how many leaf columns it spans horizontally
    # Allow a small x padding around the line bbox
    if leaf_cells:
        avg_leaf_w = statistics.mean(c["bbox"]["w"] for c in leaf_cells)
    else:
        avg_leaf_w = 0.05
    x_pad = max(0.015, 0.6 * avg_leaf_w)

    for ln in parent_candidates:
        L = ln["bbox"]["x"] - x_pad
        R = bbox_right(ln["bbox"]) + x_pad
        covered_cols = [col for col, cx in col_centers.items() if L <= cx <= R]
        if len(covered_cols) >= 2:
            parent_key = to_snake_case(ln["text"])
            for col in covered_cols:
                leaf_key = header_map.get(col) or to_snake_case(
                    leaf_texts.get(col, ""))
                if not leaf_key:
                    leaf_key = f"col_{col}"
                if not leaf_key.startswith(parent_key + "_"):
                    header_map[col] = f"{parent_key}_{leaf_key}"

    # Fill missing columns + disambiguate duplicates
    for i in range(1, total_cols + 1):
        if i not in header_map:
            header_map[i] = f"col_{i}"
    seen = {}
    for k, v in list(header_map.items()):
        if v in seen:
            header_map[k] = f"{v}_{k}"
        else:
            seen[v] = True

    return header_map

# Row + overlay


def build_rows_and_boxes(
    cells: List[Dict[str, Any]],
    header_map: Dict[int, str],
    header_rows: List[int],
    confidence_threshold: float
) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    data_rows = defaultdict(list)
    for c in cells:
        if c["row"] not in header_rows:
            data_rows[c["row"]].append(c)

    structured_rows = []
    overlay_boxes = []

    for row_idx in sorted(data_rows.keys()):
        row_obj: Dict[str, str] = {}
        for cell in sorted(data_rows[row_idx], key=lambda z: z["col"]):
            key = header_map.get(cell["col"], f"col_{cell['col']}")
            value = cell["text"]
            row_obj[key] = value
            overlay_boxes.append({
                "group_id": f"row_{row_idx}_col_{cell['col']}",
                "key": key,
                "value": value,
                "bbox": cell["bbox"],
                "confidence": cell["confidence"],
                "doubt": cell["confidence"] < confidence_threshold
            })
        structured_rows.append(row_obj)
    return structured_rows, overlay_boxes

# CLI


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess Textract output into structured rows and overlay boxes."
    )
    parser.add_argument("--input", required=True,
                        help="Path to Textract JSON file.")
    parser.add_argument(
        "--output-rows", help="Output file for structured rows.")
    parser.add_argument(
        "--output-boxes", help="Output file for overlay boxes.")
    parser.add_argument("--header-row-density", type=float, default=0.6,
                        help="Header row density threshold (0–1). Default=0.6")
    parser.add_argument("--confidence-threshold", type=float, default=80.0,
                        help="Confidence threshold for doubtful fields. Default=80")

    args = parser.parse_args()
    input_path = Path(args.input)
    if not args.output_rows:
        args.output_rows = str(input_path.parent /
                               f"{input_path.stem}_rows.json")
    if not args.output_boxes:
        args.output_boxes = str(
            input_path.parent / f"{input_path.stem}_boxes.json")

    textract_data = load_json(args.input)
    cells = extract_cells(textract_data)
    lines = extract_lines(textract_data)

    header_rows = detect_header_rows(cells, args.header_row_density)
    header_map = build_header_map(cells, header_rows, lines)
    structured_rows, overlay_boxes = build_rows_and_boxes(
        cells, header_map, header_rows, args.confidence_threshold
    )
    save_json(structured_rows, args.output_rows)
    save_json(overlay_boxes, args.output_boxes)

    print("Preprocessing complete.")
    print(f"  Header rows detected: {header_rows}")
    print(f"  Rows written to:  {args.output_rows}")
    print(f"  Boxes written to: {args.output_boxes}")


if __name__ == "__main__":
    main()
