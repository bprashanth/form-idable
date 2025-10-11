#!/usr/bin/env python3
"""
row_classifier.py

Given a Textract JSON file, classify each detected row as:
  - PRINTED_ONLY
  - HANDWRITING_ONLY
  - MIXED
  - EMPTY

Usage:
  python row_classifier.py --input 002_layout.json
  python row_classifier.py --input 002_layout.json --debug
"""

import json
import argparse
import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any


# ======================================================
# Utilities
# ======================================================

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ======================================================
# Base class
# ======================================================

class BaseFormProcessor:
    name: str = "BaseFormProcessor"

    def classify_rows(self, textract_json: Dict[str, Any], debug: bool = False):
        raise NotImplementedError


# ======================================================
# Handwritten Table Form — only classification step
# ======================================================

class HandwrittenTableForm(BaseFormProcessor):
    name = "HandwrittenTableForm"

    def classify_rows(self, textract_json: Dict[str, Any], debug: bool = False):
        # Use CELL blocks for reliable row detection
        rows = self.extract_rows_from_cells(textract_json)
        if not rows:
            print("❌ No CELL blocks found.")
            return

        self.assign_row_types(rows)

        print(f"✅ Classified {len(rows)} rows:\n")
        for idx, row in enumerate(rows, start=1):
            text_preview = " ".join(w["text"] for w in row["words"])[:120]
            print(f"Row {idx:02d} → {row['row_type']}: {text_preview}")
            if debug:
                printed = sum(1 for w in row["words"]
                              if w["text_type"] == "PRINTED")
                hand = sum(1 for w in row["words"]
                           if w["text_type"] == "HANDWRITING")
                print(
                    f"   • total_words={len(row['words'])}, printed={printed}, handwriting={hand}")

    # --------------------------
    # Helpers
    # --------------------------

    def extract_rows_from_cells(self, textract_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract rows using CELL blocks with RowIndex, then get words from each cell."""
        # First, build a map of all WORD blocks by ID
        word_map = {}
        for block in textract_json.get("Blocks", []):
            if block["BlockType"] == "WORD":
                word_map[block["Id"]] = block

        # Group CELL blocks by RowIndex
        rows_by_index = {}
        for block in textract_json.get("Blocks", []):
            if block["BlockType"] != "CELL":
                continue

            row_index = block.get("RowIndex", 0)
            if row_index not in rows_by_index:
                rows_by_index[row_index] = []
            rows_by_index[row_index].append(block)

        # Convert to rows with words
        rows = []
        for row_index in sorted(rows_by_index.keys()):
            cells = rows_by_index[row_index]
            words = []

            # Get words from each cell in this row
            for cell in cells:
                for relationship in cell.get("Relationships", []):
                    if relationship["Type"] == "CHILD":
                        for word_id in relationship["Ids"]:
                            if word_id in word_map:
                                word_block = word_map[word_id]
                                words.append({
                                    "text": word_block.get("Text", "").strip(),
                                    "text_type": word_block.get("TextType", "PRINTED"),
                                    "x_mid": word_block["Geometry"]["BoundingBox"]["Left"] + word_block["Geometry"]["BoundingBox"]["Width"] / 2,
                                    "y_mid": word_block["Geometry"]["BoundingBox"]["Top"] + word_block["Geometry"]["BoundingBox"]["Height"] / 2,
                                })

            # Sort words by x-coordinate within the row
            words.sort(key=lambda w: w["x_mid"])

            if words:  # Only add rows that have words
                rows.append({
                    "row_index": row_index,
                    # Average Y position
                    "y_mid": sum(w["y_mid"] for w in words) / len(words),
                    "words": words
                })

        return rows

    def extract_words(self, textract_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        words = []
        for b in textract_json.get("Blocks", []):
            if b["BlockType"] != "WORD":
                continue
            bb = b["Geometry"]["BoundingBox"]
            words.append({
                "text": b.get("Text", "").strip(),
                "text_type": b.get("TextType", "PRINTED"),
                "y_mid": bb["Top"] + bb["Height"] / 2,
                "x_mid": bb["Left"] + bb["Width"] / 2,
            })
        words.sort(key=lambda w: w["y_mid"])
        return words

    def cluster_rows(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group words by proximity of their vertical centers."""
        rows = []
        row_gap_threshold = 0.015
        current_y, current_row = None, []

        for w in words:
            if current_y is None:
                current_y, current_row = w["y_mid"], [w]
                continue

            if abs(w["y_mid"] - current_y) < row_gap_threshold:
                current_row.append(w)
                current_y = (current_y + w["y_mid"]) / 2
            else:
                rows.append({"y_mid": current_y, "words": current_row})
                current_y, current_row = w["y_mid"], [w]

        if current_row:
            rows.append({"y_mid": current_y, "words": current_row})

        # Sort words within each row by x-coordinate (left to right)
        for row in rows:
            row["words"].sort(key=lambda w: w["x_mid"])

        return rows

    def assign_row_types(self, rows: List[Dict[str, Any]]):
        """Label each row as HANDWRITING_ONLY / PRINTED_ONLY / MIXED / EMPTY."""
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


# ======================================================
# CLI Entrypoint
# ======================================================

def main():
    parser = argparse.ArgumentParser(
        description="Classify Textract rows by PRINTED/HANDWRITING composition."
    )
    parser.add_argument("--input", required=True,
                        help="Path to Textract JSON file.")
    parser.add_argument("--debug", action="store_true",
                        help="Enable verbose debug output.")
    args = parser.parse_args()

    textract_data = load_json(args.input)
    processor = HandwrittenTableForm()
    processor.classify_rows(textract_data, debug=args.debug)


if __name__ == "__main__":
    main()
