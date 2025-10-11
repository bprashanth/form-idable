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


def to_snake_case(text: str) -> str:
    """Convert text to snake_case format."""
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace("#", " number ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


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

        # Extract universal fields from UNIVERSAL rows and KEY_VALUE_SET blocks
        universal_fields = self.extract_universal_fields(rows)

        # Analyze KEY_VALUE_SET blocks for debugging
        if debug:
            self.analyze_key_value_sets(textract_json)

        # Only extract KEY_VALUE_SET blocks that are above the table (not in data/header rows)
        key_value_fields = self.extract_key_value_sets_above_table(
            textract_json, rows, debug)
        universal_fields.update(key_value_fields)

        # Build hierarchical header map using MERGED_CELL and ColumnSpan information
        header_map = self.build_header_map_from_cells(
            textract_json, rows, debug)

        print(f"✅ Classified {len(rows)} rows:\n")
        if universal_fields:
            print("📋 Universal Fields:")
            for key, value in universal_fields.items():
                print(f"   • {key}: {value}")
            print()

        if header_map:
            print("📊 Header Map:")
            for key, value in header_map.items():
                print(f"   • {key}: {value}")
            print()

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

                # Show which cells contain handwriting
                if hand > 0:
                    hand_cells = {}
                    for w in row["words"]:
                        if w["text_type"] == "HANDWRITING":
                            col = w.get("column_index", "?")
                            if col not in hand_cells:
                                hand_cells[col] = []
                            hand_cells[col].append(w["text"])

                    for col, texts in hand_cells.items():
                        print(
                            f"   • Column {col} handwriting: {' '.join(texts)}")

    # --------------------------
    # Helpers
    # --------------------------

    def extract_universal_fields(self, rows: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract universal fields from UNIVERSAL rows with key:value or key-value patterns."""
        universal_fields = {}

        for row in rows:
            if row.get("row_type") != "UNIVERSAL":
                continue

            # Get the full text of the row
            text = " ".join(w["text"] for w in row["words"])

            # Look for key:value or key-value patterns
            for separator in [":", "-"]:
                if separator in text:
                    parts = text.split(separator, 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()

                        # Convert key to snake_case
                        snake_key = to_snake_case(key)
                        if snake_key and value:
                            universal_fields[snake_key] = value
                            break  # Only use the first separator found

        return universal_fields

    def analyze_key_value_sets(self, textract_json: Dict[str, Any]) -> None:
        """Analyze all KEY_VALUE_SET blocks to understand their structure."""
        # Build a map of all WORD blocks by ID
        word_map = {}
        for block in textract_json.get("Blocks", []):
            if block["BlockType"] == "WORD":
                word_map[block["Id"]] = block

        print("🔍 KEY_VALUE_SET Analysis:")
        print("=" * 50)

        kv_count = 0
        for block in textract_json.get("Blocks", []):
            if block["BlockType"] != "KEY_VALUE_SET":
                continue

            kv_count += 1
            print(f"\nKEY_VALUE_SET #{kv_count}:")
            print(f"  ID: {block['Id']}")
            print(f"  Confidence: {block['Confidence']}")
            print(
                f"  Position: ({block['Geometry']['BoundingBox']['Left']:.3f}, {block['Geometry']['BoundingBox']['Top']:.3f})")

            # Analyze all relationships
            for rel_idx, relationship in enumerate(block.get("Relationships", [])):
                print(
                    f"  Relationship #{rel_idx + 1}: Type = '{relationship['Type']}'")

                words = []
                for word_id in relationship["Ids"]:
                    if word_id in word_map:
                        word_block = word_map[word_id]
                        words.append(
                            f"'{word_block['Text']}' (TextType: {word_block.get('TextType', 'UNKNOWN')})")
                    else:
                        words.append(f"'{word_id}' (WORD NOT FOUND)")

                print(f"    Words: {words}")

        print(f"\n📊 Total KEY_VALUE_SET blocks found: {kv_count}")
        print("=" * 50)

    def extract_key_value_sets(self, textract_json: Dict[str, Any], debug: bool = False) -> Dict[str, str]:
        """Extract universal fields from KEY_VALUE_SET blocks using explicit VALUE relationships."""
        key_value_fields = {}

        # Build maps of all blocks by ID
        word_map = {}
        kv_map = {}
        for block in textract_json.get("Blocks", []):
            if block["BlockType"] == "WORD":
                word_map[block["Id"]] = block
            elif block["BlockType"] == "KEY_VALUE_SET":
                kv_map[block["Id"]] = block

        # Process KEY_VALUE_SET blocks that have VALUE relationships
        for block in textract_json.get("Blocks", []):
            if block["BlockType"] != "KEY_VALUE_SET":
                continue

            # Extract key from CHILD relationships
            key_text = ""
            value_text = ""

            for relationship in block.get("Relationships", []):
                if relationship["Type"] == "CHILD":
                    # These are the KEY words
                    for word_id in relationship["Ids"]:
                        if word_id in word_map:
                            key_text += word_map[word_id]["Text"] + " "

                elif relationship["Type"] == "VALUE":
                    # Follow the VALUE relationship to get the value
                    for value_block_id in relationship["Ids"]:
                        if value_block_id in kv_map:
                            value_block = kv_map[value_block_id]
                            # Get value text from the value block's CHILD relationships
                            for value_rel in value_block.get("Relationships", []):
                                if value_rel["Type"] == "CHILD":
                                    for word_id in value_rel["Ids"]:
                                        if word_id in word_map:
                                            value_text += word_map[word_id]["Text"] + " "

            key_text = key_text.strip()
            value_text = value_text.strip()

            if debug and key_text and value_text:
                print(f"🔍 KEY_VALUE_SET: '{key_text}' -> '{value_text}'")

            if key_text and value_text:
                # Convert key to snake_case
                snake_key = to_snake_case(key_text)
                if snake_key:
                    key_value_fields[snake_key] = value_text

        return key_value_fields

    def extract_key_value_sets_above_table(self, textract_json: Dict[str, Any], rows: List[Dict[str, Any]], debug: bool = False) -> Dict[str, str]:
        """Extract universal fields from KEY_VALUE_SET blocks that are above the table structure."""
        key_value_fields = {}

        # Find the top boundary of the table (topmost row)
        if not rows:
            return key_value_fields

        table_top = min(row["y_mid"] for row in rows)

        # Build maps of all blocks by ID
        word_map = {}
        kv_map = {}
        for block in textract_json.get("Blocks", []):
            if block["BlockType"] == "WORD":
                word_map[block["Id"]] = block
            elif block["BlockType"] == "KEY_VALUE_SET":
                kv_map[block["Id"]] = block

        if debug:
            print(f"🔍 Table top boundary: {table_top:.3f}")

        # Process KEY_VALUE_SET blocks that are above the table
        kv_blocks_above_table = 0
        kv_blocks_in_table = 0

        for block in textract_json.get("Blocks", []):
            if block["BlockType"] != "KEY_VALUE_SET":
                continue

            # Check if this KEY_VALUE_SET block is above the table
            block_y = block["Geometry"]["BoundingBox"]["Top"]
            if block_y >= table_top:
                kv_blocks_in_table += 1
                if debug:
                    print(
                        f"🔍 Skipping KEY_VALUE_SET in table at Y={block_y:.3f}")
                continue

            kv_blocks_above_table += 1

            # Extract key from CHILD relationships
            key_text = ""
            value_text = ""

            for relationship in block.get("Relationships", []):
                if relationship["Type"] == "CHILD":
                    # These are the KEY words
                    for word_id in relationship["Ids"]:
                        if word_id in word_map:
                            key_text += word_map[word_id]["Text"] + " "

                elif relationship["Type"] == "VALUE":
                    # Follow the VALUE relationship to get the value
                    for value_block_id in relationship["Ids"]:
                        if value_block_id in kv_map:
                            value_block = kv_map[value_block_id]
                            # Get value text from the value block's CHILD relationships
                            for value_rel in value_block.get("Relationships", []):
                                if value_rel["Type"] == "CHILD":
                                    for word_id in value_rel["Ids"]:
                                        if word_id in word_map:
                                            value_text += word_map[word_id]["Text"] + " "

            key_text = key_text.strip()
            value_text = value_text.strip()

            if debug and key_text and value_text:
                print(
                    f"🔍 Universal KEY_VALUE_SET: '{key_text}' -> '{value_text}'")

            if key_text and value_text:
                # Convert key to snake_case
                snake_key = to_snake_case(key_text)
                if snake_key:
                    key_value_fields[snake_key] = value_text

        if debug:
            print(
                f"🔍 KEY_VALUE_SET summary: {kv_blocks_above_table} above table, {kv_blocks_in_table} in table")

        return key_value_fields

    def build_header_map_from_cells(self, textract_json: Dict[str, Any], rows: List[Dict[str, Any]], debug: bool = False) -> Dict[str, List[str]]:
        """Build hierarchical header map using MERGED_CELL and ColumnSpan information."""
        header_map = {}

        # Build maps of all blocks by ID
        word_map = {}
        cell_map = {}
        merged_cell_map = {}
        layout_text_map = {}

        for block in textract_json.get("Blocks", []):
            if block["BlockType"] == "WORD":
                word_map[block["Id"]] = block
            elif block["BlockType"] == "CELL":
                cell_map[block["Id"]] = block
            elif block["BlockType"] == "MERGED_CELL":
                merged_cell_map[block["Id"]] = block
            elif block["BlockType"] == "LAYOUT_TEXT":
                layout_text_map[block["Id"]] = block

        if debug:
            print(
                f"🔍 Found {len(cell_map)} CELL blocks, {len(merged_cell_map)} MERGED_CELL blocks, {len(layout_text_map)} LAYOUT_TEXT blocks")

        # Get header row indices from our classified rows
        header_row_indices = set()
        for row in rows:
            if row.get("row_type") == "HEADER":
                header_row_indices.add(row["row_index"])

        if debug:
            print(f"🔍 Header row indices: {sorted(header_row_indices)}")

        # Process MERGED_CELL blocks first (they take priority) - only in header rows
        merged_cell_info = {}  # Store info about merged cells for hierarchical mapping

        for merged_id, merged_cell in merged_cell_map.items():
            row_index = merged_cell.get("RowIndex", 0)

            # Only process MERGED_CELLs in header rows
            if row_index not in header_row_indices:
                continue

            if debug:
                print(
                    f"🔍 Processing MERGED_CELL {merged_id} in header row {row_index} (RowIndex: {merged_cell.get('RowIndex', 'N/A')})")

            # Extract text by following relationships
            merged_text = self._extract_text_from_relationships(
                merged_cell, word_map, cell_map, layout_text_map, debug)

            if merged_text:
                col_start = merged_cell.get("ColumnIndex", 0)
                col_span = merged_cell.get("ColumnSpan", 1)

                # Store merged cell info for hierarchical mapping
                merged_cell_info[merged_id] = {
                    "text": merged_text,
                    "col_start": col_start,
                    "col_span": col_span,
                    "row_index": row_index
                }

                if debug:
                    print(
                        f"   MERGED_CELL spans columns {col_start}-{col_start + col_span - 1}: {merged_text}")

        # Process regular CELL blocks that aren't covered by MERGED_CELLs - only in header rows
        covered_columns_by_row = {}  # Track covered columns per row
        for merged_cell in merged_cell_map.values():
            row_index = merged_cell.get("RowIndex", 0)
            if row_index in header_row_indices:
                col_start = merged_cell.get("ColumnIndex", 0)
                col_span = merged_cell.get("ColumnSpan", 1)
                if row_index not in covered_columns_by_row:
                    covered_columns_by_row[row_index] = set()
                for col in range(col_start, col_start + col_span):
                    covered_columns_by_row[row_index].add(col)

        if debug:
            for row_idx, cols in covered_columns_by_row.items():
                print(f"🔍 Row {row_idx} covered columns: {sorted(cols)}")

        for cell_id, cell in cell_map.items():
            row_index = cell.get("RowIndex", 0)
            col_index = cell.get("ColumnIndex", 0)

            # Only process CELLs in header rows
            if row_index not in header_row_indices:
                continue

            # Skip if this column is covered by a MERGED_CELL in the same row
            if (row_index in covered_columns_by_row and
                    col_index in covered_columns_by_row[row_index]):
                if debug:
                    print(
                        f"   Skipping CELL row {row_index} column {col_index} (covered by MERGED_CELL in same row)")
                continue

            # Extract text from this cell
            cell_text = self._extract_text_from_relationships(
                cell, word_map, cell_map, layout_text_map, debug)

            if cell_text:
                # Check if this cell is under a merged cell (hierarchical relationship)
                parent_merged_cell = None
                for merged_id, merged_info in merged_cell_info.items():
                    if (merged_info["row_index"] < row_index and  # Merged cell is in a higher row
                        col_index >= merged_info["col_start"] and
                            col_index < merged_info["col_start"] + merged_info["col_span"]):
                        parent_merged_cell = merged_info
                        break

                if parent_merged_cell:
                    # This cell is under a merged cell - create hierarchical key
                    parent_text = parent_merged_cell["text"]
                    combined_text = f"{parent_text} {cell_text}"
                    snake_key = to_snake_case(combined_text)

                    if debug:
                        print(
                            f"   HIERARCHICAL CELL row {row_index} column {col_index}: {snake_key} -> {combined_text} (under '{parent_text}')")
                else:
                    # Regular cell not under a merged cell
                    snake_key = to_snake_case(cell_text)

                    if debug:
                        print(
                            f"   REGULAR CELL row {row_index} column {col_index}: {snake_key} -> {cell_text}")

                if snake_key:
                    header_map[snake_key] = [
                        cell_text if not parent_merged_cell else combined_text]

        return header_map

    def _extract_text_from_relationships(self, block: Dict[str, Any], word_map: Dict[str, Any],
                                         cell_map: Dict[str, Any], layout_text_map: Dict[str, Any],
                                         debug: bool = False) -> str:
        """Extract text by following relationships from a block."""
        text_parts = []

        for relationship in block.get("Relationships", []):
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    # Check if it's a WORD
                    if child_id in word_map:
                        text_parts.append(word_map[child_id]["Text"])
                        if debug:
                            print(
                                f"     Found WORD: '{word_map[child_id]['Text']}'")

                    # Check if it's a CELL (follow its relationships)
                    elif child_id in cell_map:
                        cell_text = self._extract_text_from_relationships(
                            cell_map[child_id], word_map, cell_map, layout_text_map, debug)
                        if cell_text:
                            text_parts.append(cell_text)
                            if debug:
                                print(f"     Found CELL text: '{cell_text}'")

                    # Check if it's a LAYOUT_TEXT (follow its relationships)
                    elif child_id in layout_text_map:
                        layout_text = self._extract_text_from_relationships(
                            layout_text_map[child_id], word_map, cell_map, layout_text_map, debug)
                        if layout_text:
                            text_parts.append(layout_text)
                            if debug:
                                print(
                                    f"     Found LAYOUT_TEXT: '{layout_text}'")

        return " ".join(text_parts).strip()

    def _bboxes_overlap(self, bbox1: Dict[str, float], bbox2: Dict[str, float], threshold: float = 0.05) -> bool:
        """Check if two bounding boxes overlap significantly."""
        # Calculate overlap area
        left = max(bbox1["Left"], bbox2["Left"])
        right = min(bbox1["Left"] + bbox1["Width"],
                    bbox2["Left"] + bbox2["Width"])
        top = max(bbox1["Top"], bbox2["Top"])
        bottom = min(bbox1["Top"] + bbox1["Height"],
                     bbox2["Top"] + bbox2["Height"])

        if left < right and top < bottom:
            overlap_area = (right - left) * (bottom - top)
            area1 = bbox1["Width"] * bbox1["Height"]
            area2 = bbox2["Width"] * bbox2["Height"]

            # Check if overlap is significant relative to the smaller box
            min_area = min(area1, area2)
            overlap_ratio = overlap_area / min_area if min_area > 0 else 0

            return overlap_ratio > threshold

        return False

    def _bboxes_close(self, bbox1: Dict[str, float], bbox2: Dict[str, float], max_distance: float = 0.1) -> bool:
        """Check if two bounding boxes are close enough to be in the same logical cell."""
        # Calculate center points
        center1_x = bbox1["Left"] + bbox1["Width"] / 2
        center1_y = bbox1["Top"] + bbox1["Height"] / 2
        center2_x = bbox2["Left"] + bbox2["Width"] / 2
        center2_y = bbox2["Top"] + bbox2["Height"] / 2

        # Calculate distance between centers
        distance = ((center1_x - center2_x) ** 2 +
                    (center1_y - center2_y) ** 2) ** 0.5

        return distance < max_distance

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

            # Sort cells by ColumnIndex to maintain column order
            cells.sort(key=lambda c: c.get("ColumnIndex", 0))

            # Get words from each cell in this row, maintaining cell grouping
            for cell in cells:
                cell_words = []
                for relationship in cell.get("Relationships", []):
                    if relationship["Type"] == "CHILD":
                        for word_id in relationship["Ids"]:
                            if word_id in word_map:
                                word_block = word_map[word_id]
                                cell_words.append({
                                    "text": word_block.get("Text", "").strip(),
                                    "text_type": word_block.get("TextType", "PRINTED"),
                                    "x_mid": word_block["Geometry"]["BoundingBox"]["Left"] + word_block["Geometry"]["BoundingBox"]["Width"] / 2,
                                    "y_mid": word_block["Geometry"]["BoundingBox"]["Top"] + word_block["Geometry"]["BoundingBox"]["Height"] / 2,
                                    "column_index": cell.get("ColumnIndex", 0),
                                })

                # Sort words within this cell by y-coordinate first, then x-coordinate
                # This preserves multi-line sentences like "Soil Temperature in °C"
                cell_words.sort(key=lambda w: (w["y_mid"], w["x_mid"]))
                words.extend(cell_words)

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
        """Bottom-up classification: DATA -> HEADER -> UNIVERSAL -> TITLE_LEGEND."""
        # First, classify basic types
        for row in rows:
            types = [w["text_type"] for w in row["words"] if w["text"].strip()]
            if not types:
                row["basic_type"] = "EMPTY"
            elif all(t == "HANDWRITING" for t in types):
                row["basic_type"] = "HANDWRITING_ONLY"
            elif all(t == "PRINTED" for t in types):
                row["basic_type"] = "PRINTED_ONLY"
            else:
                row["basic_type"] = "MIXED"

        # Bottom-up state machine
        state = "DATA"  # Start from bottom looking for data rows
        for row in reversed(rows):  # Process from bottom to top
            # Count printed vs handwritten words for MIXED rows
            printed_count = sum(
                1 for w in row["words"] if w["text_type"] == "PRINTED" and w["text"].strip())
            hand_count = sum(
                1 for w in row["words"] if w["text_type"] == "HANDWRITING" and w["text"].strip())

            if state == "DATA":
                if row["basic_type"] == "HANDWRITING_ONLY":
                    row["row_type"] = "DATA"
                elif row["basic_type"] == "PRINTED_ONLY":
                    row["row_type"] = "HEADER"
                    state = "HEADER"
                elif row["basic_type"] == "MIXED":
                    # If mostly printed, treat as header; if mostly handwritten, treat as data
                    if printed_count > hand_count:
                        row["row_type"] = "HEADER"
                        state = "HEADER"
                    else:
                        row["row_type"] = "DATA"
                else:
                    row["row_type"] = "EMPTY"

            elif state == "HEADER":
                if row["basic_type"] == "PRINTED_ONLY":
                    row["row_type"] = "HEADER"
                elif row["basic_type"] == "MIXED":
                    # Check if this looks like universal fields (key: value pattern)
                    text = " ".join(w["text"] for w in row["words"])
                    if ":" in text or "-" in text:
                        row["row_type"] = "UNIVERSAL"
                        state = "UNIVERSAL"
                    else:
                        row["row_type"] = "HEADER"
                else:
                    row["row_type"] = "HEADER"

            elif state == "UNIVERSAL":
                if row["basic_type"] == "MIXED":
                    row["row_type"] = "UNIVERSAL"
                elif row["basic_type"] == "PRINTED_ONLY":
                    row["row_type"] = "TITLE_LEGEND"
                    state = "TITLE_LEGEND"
                else:
                    row["row_type"] = "UNIVERSAL"

            else:  # TITLE_LEGEND
                row["row_type"] = "TITLE_LEGEND"


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
