import json
import cv2
import numpy as np

# === paths ===
IMG_PATH = "../input_forms/IMG-20250924-WA0002.jpg"                  # original form image
TEXTRACT_JSON = "output/textract_output.json"
OUT_PATH = "textract_overlay.jpg"

# === load data ===
image = cv2.imread(IMG_PATH)
h, w = image.shape[:2]

data = json.load(open(TEXTRACT_JSON))
blocks = data["Blocks"]

# === draw overlays ===
for b in blocks:
    if b["BlockType"] == "CELL":
        box = b["Geometry"]["BoundingBox"]
        top = int(box["Top"] * h)
        left = int(box["Left"] * w)
        width = int(box["Width"] * w)
        height = int(box["Height"] * h)

        # coordinates
        p1 = (left, top)
        p2 = (left + width, top + height)

        # draw faint rectangle (light blue)
        cv2.rectangle(image, p1, p2, (255, 200, 100), 1)

        # get cell text (if any)
        text = b.get("Text", "")
        if not text and "Relationships" in b:
            # reconstruct from child WORD blocks
            for rel in b["Relationships"]:
                if rel["Type"] == "CHILD":
                    words = []
                    for wid in rel["Ids"]:
                        wblk = next(
                            (x for x in blocks if x["Id"] == wid and x["BlockType"] == "WORD"), None
                        )
                        if wblk:
                            words.append(wblk["Text"])
                    text = " ".join(words)
                    break

        label = text.strip() if text.strip() else f"R{b.get('RowIndex')}-C{b.get('ColumnIndex')}"

        # put small text label (avoid overflowing box)
        font_scale = 0.3
        thickness = 1
        cv2.putText(
            image,
            label[:25],  # truncate long text
            (left + 2, top + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (0, 100, 255),
            thickness,
            cv2.LINE_AA,
        )

# === save & display ===
cv2.imwrite(OUT_PATH, image)
print(f"Overlay saved to {OUT_PATH}")

