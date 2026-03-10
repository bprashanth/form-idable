# form-idable

A pipeline that converts handwritten field-survey forms into structured datasets using AWS Textract, with a human-in-the-loop review UI.

## The problem

Researchers collect ecological data on printed paper forms in the field. These forms have handwritten entries like species names, DBH measurements, GPS coordinates, and plot metadata. Digitizing hundreds of these forms manually is slow and error-prone.

## How it works

```
  Photo of a form (JPG/PNG)
         |
         v
  |---------------|
  | AWS Textract  |  Extracts tables, cells, key-value pairs
  | (TABLES+FORMS |  with bounding boxes and confidence scores
  |  +LAYOUT)     |
  |---------------|
         |  Raw Textract JSON (WORD, CELL, MERGED_CELL, KEY_VALUE_SET blocks)
         v
  |---------------|
  | preprocessor  |  Classifies rows (header vs data vs universal),
  | .py           |  builds header maps, extracts key-value fields,
  |---------------|  outputs structured intermediate format
         |
         v
  |---------------|
  | form-viewer   |  Vue 3 app: overlays bounding boxes on the
  | (UI)          |  original image, lets you review and correct
  |---------------|  extracted values, then export clean JSON
         |
         v
   Corrected structured JSON → ready for Excel/database
```

## Directory layout

```
cloud/                  AWS Textract pipeline (the main processing code)
  |--- preprocessor.py   Textract JSON → intermediate format (row classification,
  |                     universal fields, hierarchical headers, bounding boxes)
  |--- top_down_preprocess.py   Simpler alternative preprocessor
  |--- overlay.py        Debug tool: draws colored bboxes on the original image
  |--- forms/            Input images (original + segmented)
  |--- output/           Raw Textract JSON and processing artifacts
  |--- results/          Final classified JSON output
  |--- hack/             AWS management scripts

form-viewer/            Vue 3 review UI
  |--- src/
  |   |--- App.vue             Root layout + state management
  |   |--- components/
  |   |   |--- FormViewer.vue  Canvas: renders image + overlay boxes
  |   |   |--- BoxOverlay.vue  Single bounding box (color-coded by confidence)
  |   |   |--- ToolBar.vue     File upload, zoom, save
  |   |   |--- SidePanel.vue   Edit rows, headers, universal fields
  |   |   |--- VisualizationPanel.vue  AI-generated charts via Vega-Lite
  |   |--- assets/
  |--- package.json            Vue 3, Vite, Tailwind CSS

docs/                   Design docs
  |--- imf.md            Intermediate format spec (the JSON schema)
  |--- form_types.md     Supported form types
  |--- challenges.md     Known issues (sparse headers, merged cells, etc.)
  |--- ui.md             UI architecture and phasing

input_forms/            Sample form photos
llm/                    (Legacy) LLM-based extraction using OpenAI prompts
```

## Quick start

### 1. Extract text with Textract

From an S3 object:
```bash
aws textract analyze-document \
  --region ap-south-1 \
  --document '{"S3Object": {"Bucket":"your-bucket","Name":"form.png"}}' \
  --feature-types '["TABLES","FORMS","LAYOUT"]' \
  --output json > textract_output.json
```

Or from a local file:
```bash
aws textract analyze-document \
  --region ap-south-1 \
  --document '{"Bytes": "'$(base64 form.png | tr -d '\n')'"}' \
  --feature-types '["TABLES","FORMS","LAYOUT"]' \
  --output json > textract_output.json
```

### 2. Preprocess into intermediate format

```bash
cd cloud
python3 preprocessor.py \
  --input textract_output.json \
  --output classified.json \
  --debug
```

This produces a JSON with three sections:
- **`universal_fields`** -- metadata that applies to every row (date, plot number, researcher name, etc.)
- **`header_map`** -- column definitions with Textract column indices and merge info
- **`rows`** -- data rows, each with cell-level bounding boxes and confidence scores

See [docs/imf.md](docs/imf.md) for the full schema.

### 3. Review in the UI

```bash
cd form-viewer
npm install
npm run dev
```

Open the app, upload the classified JSON and the original form image. The UI overlays bounding boxes on the image color-coded by confidence:
- **Red glow**: confidence < 70% (needs review)
- **Orange glow**: 70-85%
- **No border**: 85%+ (likely correct)

Click any box to edit its value in the side panel. Universal fields and headers are also editable. When done, hit Save to export corrected JSON.

### 4. Debug with overlay

To visually inspect what Textract detected on the raw image:
```bash
cd cloud
python3 overlay.py --image forms/original/form.jpg --json output/form.json
```

Draws color-coded rectangles for tables (yellow), key-value pairs (green), header cells (red), and data cells (blue).

## Intermediate format (summary)

```json
{
  "universal_fields": {
    "date": { "value": "19/02/2025", "system": { "group_id": "universal_field_1", "valid": true } },
    "area_name": { "value": "BKM", "system": { "group_id": "universal_field_2", "valid": true } }
  },
  "header_map": {
    "s_no": { "field_name": "S.No", "system": { "column_index": 1, "merged": false } },
    "spp_name": { "field_name": "SPP Name", "system": { "column_index": 2, "merged": false } }
  },
  "rows": [
    {
      "s_no": "1",
      "spp_name": "cadelei",
      "system": {
        "row_index": 2,
        "bbox": { "Left": 0.065, "Top": 0.227, "Width": 0.748, "Height": 0.012 },
        "cells": {
          "row_2_col_1": { "text": "1", "confidence": 95.2, "bbox": { "..." : "..." } }
        }
      }
    }
  ]
}
```

## Requirements

- **Python 3.10+** with packages in `requirements.txt`
- **AWS CLI** configured with Textract access
- **Node.js 20+** for the form-viewer UI
