import json
import cv2
import numpy as np

# === paths ===
IMG_PATH = "./forms/original/IMG-20250924-WA0000.jpg"                  # original form image
TEXTRACT_JSON = "./output/cloud_IMG-20250924-WA0000.json"
OUT_PATH = "./output/overlays/IMG-20250924-WA0000_overlay.jpg"

# === load data ===
image = cv2.imread(IMG_PATH)
h, w = image.shape[:2]

data = json.load(open(TEXTRACT_JSON))
blocks = data["Blocks"]

# === helper functions ===


def get_text_from_block(block, blocks):
    """Extract text from a block, handling relationships to child blocks"""
    text = block.get("Text", "")
    if not text and "Relationships" in block:
        for rel in block["Relationships"]:
            if rel["Type"] == "CHILD":
                words = []
                for wid in rel["Ids"]:
                    wblk = next(
                        (x for x in blocks if x["Id"] ==
                         wid and x["BlockType"] == "WORD"), None
                    )
                    if wblk:
                        words.append(wblk["Text"])
                text = " ".join(words)
                break
    return text.strip()


def draw_rectangle_with_text(image, box, text, color, thickness=2, font_scale=0.4):
    """Draw rectangle and text with given styling"""
    top = int(box["Top"] * h)
    left = int(box["Left"] * w)
    width = int(box["Width"] * w)
    height = int(box["Height"] * h)

    p1 = (left, top)
    p2 = (left + width, top + height)

    cv2.rectangle(image, p1, p2, color, thickness)

    if text:
        cv2.putText(
            image,
            text[:30],  # truncate long text
            (left + 2, top + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )


# === draw overlays ===
# First pass: Draw layout elements (background)
for b in blocks:
    if b["BlockType"] == "LAYOUT_TABLE":
        text = get_text_from_block(b, blocks)
        draw_rectangle_with_text(
            image, b["Geometry"]["BoundingBox"], f"TABLE: {text}", (0, 255, 255), 3, 0.6)

    elif b["BlockType"] == "LAYOUT_TEXT":
        text = get_text_from_block(b, blocks)
        draw_rectangle_with_text(
            image, b["Geometry"]["BoundingBox"], f"TEXT: {text}", (255, 255, 0), 2, 0.5)

# Second pass: Draw form elements
for b in blocks:
    if b["BlockType"] == "KEY_VALUE_SET":
        text = get_text_from_block(b, blocks)
        # Check if it's a key or value
        entity_types = b.get("EntityTypes", [])
        if "KEY" in entity_types:
            draw_rectangle_with_text(
                image, b["Geometry"]["BoundingBox"], f"KEY: {text}", (0, 255, 0), 2, 0.4)
        elif "VALUE" in entity_types:
            draw_rectangle_with_text(
                image, b["Geometry"]["BoundingBox"], f"VALUE: {text}", (0, 200, 0), 2, 0.4)
        else:
            draw_rectangle_with_text(
                image, b["Geometry"]["BoundingBox"], f"FORM: {text}", (0, 150, 0), 2, 0.4)

# Third pass: Draw table cells with enhanced header detection
for b in blocks:
    if b["BlockType"] == "CELL":
        box = b["Geometry"]["BoundingBox"]
        text = get_text_from_block(b, blocks)

        # Determine if this is likely a header cell
        row_index = b.get("RowIndex", 0)
        is_header = row_index == 1  # First row is typically header

        if is_header:
            # Header cells - bright red
            draw_rectangle_with_text(
                image, box, f"H: {text}", (0, 0, 255), 2, 0.5)
        else:
            # Regular cells - light blue
            label = text if text else f"R{b.get('RowIndex')}-C{b.get('ColumnIndex')}"
            draw_rectangle_with_text(
                image, box, label, (255, 200, 100), 1, 0.3)

# === save & display ===
cv2.imwrite(OUT_PATH, image)
print(f"Overlay saved to {OUT_PATH}")
