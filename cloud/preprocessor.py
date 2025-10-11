#!/usr/bin/env python3
"""
preprocessor.py

Implements a modular Textract preprocessing pipeline. This implements the "bottom up" algorithm. See ../docs/ppalgorithms.md for details.

Each form type is represented by a class with a .preprocess() method.
The first class that successfully processes the input claims the form.

This file contains:
 - BaseFormProcessor (abstract)
 - HandwrittenTableForm (handwriting/printed detector)
 - CLI entrypoint

Usage:
$ aws textract analyze-document   --region ap-south-1   --document '{"S3Object": {"Bucket":"<bucketname>","Name":"<dirname>/<filename>.jpg"}}'   --feature-types '["TABLES", "FORMS", "LAYOUT"]'   --output json > 001_layout.json

$ python3 ./preprocessor.py --input 001_layout.json
"""

import json
import argparse
import statistics
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict


# ======================================================
# Utility functions
# ======================================================

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def to_snake_case(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace("#", " number ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


# ======================================================
# Base class for all form processors
# ======================================================

class UnknownFormError(Exception):
    pass


class BaseFormProcessor:
    """Abstract base for all form recognizers."""

    name: str = "BaseFormProcessor"

    def preprocess(self, textract_json: Dict[str, Any]) -> Dict[str, Any]:
        """Return structured dict with keys: title_legend, universal_fields, headers, rows."""
        raise NotImplementedError("Subclasses must implement preprocess()")


# ======================================================
# Handwritten table form processor
# ======================================================

class HandwrittenTableForm(BaseFormProcessor):
    """Form type: printed headers + handwritten data rows."""

    name = "HandwrittenTableForm"

    # --------------------------
    # Core API
    # --------------------------
    def preprocess(self, textract_json: Dict[str, Any]) -> Dict[str, Any]:
        words = self.extract_words(textract_json)
        if not words:
            raise UnknownFormError("No WORD blocks found.")

        rows = self.cluster_rows(words)
        self.classify_rows(rows)

        title_rows, universal_rows, header_rows, data_rows = self.segment_rows(
            rows)

        if not header_rows or not data_rows:
            raise UnknownFormError("No header+data block detected.")

        result = {
            "title_legend": self.build_title_legend(title_rows),
            "universal_fields": self.build_universal_fields(universal_rows),
            "headers": self.build_headers(header_rows),
            "rows": self.build_data_objects(data_rows),
        }

        return result

    # --------------------------
    # Extraction helpers
    # --------------------------
    def extract_words(self, textract_json) -> List[Dict[str, Any]]:
        words = []
        for block in textract_json["Blocks"]:
            if block["BlockType"] == "WORD":
                bb = block["Geometry"]["BoundingBox"]
                words.append({
                    "text": block["Text"].strip(),
                    "text_type": block.get("TextType", "PRINTED"),
                    "y_mid": bb["Top"] + bb["Height"] / 2,
                    "x_mid": bb["Left"] + bb["Width"] / 2,
                    "bbox": {
                        "x": bb["Left"],
                        "y": bb["Top"],
                        "w": bb["Width"],
                        "h": bb["Height"],
                    },
                    "conf": block.get("Confidence", 100),
                })
        words.sort(key=lambda w: w["y_mid"])
        return words

    def cluster_rows(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group words into horizontal rows."""
        rows = []
        row_gap_threshold = 0.015
        current_y = None
        current_row = []

        for w in words:
            if current_y is None:
                current_y = w["y_mid"]
                current_row = [w]
                continue
            if abs(w["y_mid"] - current_y) < row_gap_threshold:
                current_row.append(w)
                current_y = (current_y + w["y_mid"]) / 2
            else:
                rows.append({"y_mid": current_y, "words": current_row})
                current_row = [w]
                current_y = w["y_mid"]

        if current_row:
            rows.append({"y_mid": current_y, "words": current_row})
        return rows

    def classify_rows(self, rows: List[Dict[str, Any]]) -> None:
        """Assign a row_type to each row."""
        for row in rows:
            types = [w["text_type"] for w in row["words"] if w["text"].strip()]
            if not types:
                row["row_type"] = "EMPTY"
            elif all(t == "HANDWRITING" for t in types):
                row["row_type"] = "HANDWRITING_ONLY"
            elif all(t == "PRINTED" for t in types):
                row["row_type"] = "PRINTED_ONLY"
            else:
                row["row_type"] = "MIXED"

    # --------------------------
    # Row segmentation
    # --------------------------
    def segment_rows(self, rows: List[Dict[str, Any]]) -> Tuple[list, list, list, list]:
        """Return (title_rows, universal_rows, header_rows, data_rows)."""
        data_rows, header_rows, universal_rows, title_rows = [], [], [], []
        state = "SEARCH_DATA"

        for row in reversed(rows):  # bottom-up
            rtype = row["row_type"]

            if state == "SEARCH_DATA":
                if rtype == "HANDWRITING_ONLY":
                    data_rows.append(row)
                    continue
                elif rtype == "PRINTED_ONLY":
                    state = "SEARCH_HEADER"
                    header_rows.append(row)
                    continue

            elif state == "SEARCH_HEADER":
                if rtype == "PRINTED_ONLY":
                    header_rows.append(row)
                elif rtype == "MIXED":
                    state = "SEARCH_UNIVERSAL"
                    universal_rows.append(row)
                else:
                    state = "SEARCH_TITLE"
                    title_rows.append(row)

            elif state == "SEARCH_UNIVERSAL":
                if rtype == "MIXED":
                    universal_rows.append(row)
                elif rtype == "PRINTED_ONLY":
                    state = "SEARCH_TITLE"
                    title_rows.append(row)

            elif state == "SEARCH_TITLE":
                if rtype == "PRINTED_ONLY":
                    title_rows.append(row)
                else:
                    break

        # restore top-down order
        return (
            list(reversed(title_rows)),
            list(reversed(universal_rows)),
            list(reversed(header_rows)),
            list(reversed(data_rows)),
        )

    # --------------------------
    # Builders
    # --------------------------
    def build_title_legend(self, title_rows):
        return [" ".join(w["text"] for w in row["words"]) for row in title_rows]

    def build_universal_fields(self, universal_rows):
        fields = {}
        for row in universal_rows:
            text_line = " ".join(w["text"] for w in row["words"])
            if ":" in text_line:
                key, val = text_line.split(":", 1)
                fields[to_snake_case(key)] = val.strip()
        return fields

    def build_headers(self, header_rows):
        """Simplest: combine last 1–2 printed rows as headers."""
        header_texts = [
            [w["text"] for w in row["words"] if w["text"].strip()]
            for row in header_rows
        ]
        return self._build_hierarchical_header_map(header_texts)

    def _build_hierarchical_header_map(self, header_texts):
        if not header_texts:
            return {}
        if len(header_texts) == 1:
            return {to_snake_case(t): t for t in header_texts[0]}

        top, bottom = header_texts[0], header_texts[1]
        header_map = {}
        for t in top:
            for b in bottom:
                if b.lower() in ["north", "east", "west", "south"]:
                    key = f"{to_snake_case(t)}_{to_snake_case(b)}"
                    header_map[key] = f"{t} / {b}"
        for b in bottom:
            k = to_snake_case(b)
            if k not in header_map:
                header_map[k] = b
        return header_map

    def build_data_objects(self, data_rows):
        """Create data objects from handwriting rows."""
        data_objects = []
        for row in data_rows:
            text_line = [w["text"] for w in row["words"] if w["text"].strip()]
            data_objects.append(text_line)
        return data_objects

    # --------------------------
    # Overlay boxes (for UI)
    # --------------------------
    def build_overlay_boxes(
        self,
        textract_json: Dict[str, Any],
        header_map: Dict[int, str],
        confidence_threshold: float = 80.0,
    ) -> List[Dict[str, Any]]:
        """Create overlay boxes using CELL blocks if available."""
        boxes = []
        for b in textract_json["Blocks"]:
            if b["BlockType"] != "CELL":
                continue
            row, col = b.get("RowIndex", -1), b.get("ColumnIndex", -1)
            bb = b["Geometry"]["BoundingBox"]
            key = header_map.get(col, f"col_{col}")
            boxes.append({
                "group_id": f"row_{row}_col_{col}",
                "key": key,
                "value": "",
                "bbox": {
                    "x": bb["Left"],
                    "y": bb["Top"],
                    "w": bb["Width"],
                    "h": bb["Height"],
                },
                "confidence": b.get("Confidence", 100.0),
                "doubt": b.get("Confidence", 100.0) < confidence_threshold,
            })
        return boxes


# ======================================================
# CLI entrypoint
# ======================================================

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
    args = parser.parse_args()

    input_path = Path(args.input)
    if not args.output_rows:
        args.output_rows = str(input_path.parent /
                               f"{input_path.stem}_rows.json")
    if not args.output_boxes:
        args.output_boxes = str(
            input_path.parent / f"{input_path.stem}_boxes.json")

    textract_data = load_json(args.input)

    # Attempt processors sequentially
    processors = [HandwrittenTableForm()]

    processed = None
    for processor in processors:
        try:
            result = processor.preprocess(textract_data)
            print(f"INFO: {processor.name} claimed the form.")
            processed = result
            break
        except UnknownFormError as e:
            print(f"ERROR: {processor.name} skipped: {e}")

    if not processed:
        print("ERROR: No known form structure could process this input.")
        return

    # Save structured rows and overlay boxes
    save_json(processed, args.output_rows)

    header_map = processed.get("headers", {})
    boxes = processors[0].build_overlay_boxes(textract_data, header_map)
    save_json(boxes, args.output_boxes)

    print(f"Rows written to: {args.output_rows}")
    print(f"Boxes written to: {args.output_boxes}")


if __name__ == "__main__":
    main()
