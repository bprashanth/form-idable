# PWA Design

Mobile PWA: photo -> crop -> Textract -> structured Excel (confidence-colored cells) -> Google Drive.

Review happens in the spreadsheet, not on the phone.

## Architecture

```
Phone (PWA)                    Server (FastAPI)                AWS
-------------                  ----------------                ---
Camera -> Crop -> Upload --POST /api/upload---> Textract ---> analyze_document
                                   |
                                   v
                              textractor library (parse response)
                              - Table.column_headers -> header row
                              - remaining cells -> data rows
                              - KEY_VALUE_SET -> universal fields
                              - cell.confidence -> per-cell scores
                                   |
                                   v
                              Excel generation (openpyxl)
                              - Red border: confidence < 70%
                              - Orange border: 70-85%
                              - No border: 85%+
                                   |
         <-- .xlsx file <----------|
         |
Save ----POST /api/drive/save---> Google Drive API
```

**Frontend: Vue 3 PWA.** FormViewer/BoxOverlay from form-viewer are reusable but not used here — review happens in Excel.

**Backend: FastAPI (Python).** Thin server: receive image, call Textract, parse with textractor, generate Excel.

## What Textract gives us for free

| Feature | How Textract provides it |
|---|---|
| Table structure | TABLE block -> CELL blocks with RowIndex, ColumnIndex, ColumnSpan |
| Column headers | `EntityTypes: ["COLUMN_HEADER"]` on CELL blocks |
| Universal fields (Date, Area Name, etc.) | KEY_VALUE_SET blocks with EntityTypes `["KEY"]` / `["VALUE"]` |
| Cell text + confidence | WORD blocks as children of CELL blocks |
| Table type | `STRUCTURED_TABLE` or `SEMI_STRUCTURED_TABLE` entity type |

The `amazon-textract-textractor` library (v1.9.2) wraps this:
- `Table.column_headers` -> `{header_text: [TableCell]}`
- `TableCell.is_column_header` -> boolean
- KEY_VALUE_SET parsing built in

For gaps beyond vanilla Textract+textractor, see [preprocessing.md](preprocessing.md).

## UX flow (4 screens)

1. **Capture** - camera button + gallery picker (`<input type="file" accept="image/*" capture="environment">`)
2. **Crop** - cropperjs overlay to trim margins. "Crop & Send" button.
3. **Processing** - spinner (~10-15 sec for Textract).
4. **Done** - "Download Excel" / "Save to Drive" buttons. Summary: row count, flagged cell count.

## Excel confidence formatting

- `confidence < 70`: **red** border + light red fill (`#FFF0F0`)
- `70 ≤ confidence < 85`: **orange** border + light orange fill (`#FFF8F0`)
- `confidence ≥ 85`: default border (no highlight)
- Header row: bold + gray background
- Universal fields: rows above the table
- Legend row explaining colors

## Project structure

```
pwa/                              Minimal Vue 3 PWA
  src/
    App.vue                       Router shell
    views/
      CaptureView.vue             Camera + gallery
      CropView.vue                cropperjs
      ProcessingView.vue          Spinner
      ResultView.vue              Download / Save to Drive
    components/
      ImageCropper.vue            cropperjs wrapper
    stores/
      formStore.js                Pinia
    composables/
      useApi.js                   Fetch wrapper
  public/manifest.json
  vite.config.js
```
The server that this pwa uses is deployed via `good-shepherd/server`. 

## Header detection

Implemented in `server/services/table_extractor.py`:
1. **Primary**: textractor `Table.column_headers` (uses `COLUMN_HEADER` entity type)
2. **Fallback**: First row of table = headers (when no `COLUMN_HEADER` entity type present)

## API endpoints

These are the API endpoints in the `good-shepherd/server` that are useful for form extraction. 
### POST /api/analyze (diagnostic)

Accepts image (multipart) OR raw Textract JSON. Returns:
```json
{
  "block_types_found": ["TABLE", "CELL", "WORD", "LINE", "KEY_VALUE_SET"],
  "entity_types_found": ["COLUMN_HEADER", "KEY", "VALUE", "STRUCTURED_TABLE"],
  "table_count": 1,
  "tables": [{
    "table_type": "STRUCTURED_TABLE",
    "row_count": 15,
    "column_count": 5,
    "column_headers": [
      {"text": "S.No", "column_index": 1, "confidence": 65.7}
    ],
    "text_types": {"HANDWRITING": 42, "PRINTED": 8}
  }],
  "key_value_pairs": [
    {"key": "Date", "value": "19/02/2025", "confidence": 92.1}
  ]
}
```

### POST /api/upload

Accepts image (multipart) OR raw Textract JSON. Returns `.xlsx` file.

### POST /api/drive/save (Phase 4)

Accepts `.xlsx` file + OAuth token. Uploads to Google Drive.

## Testing

Start the server:
```bash
cd good-shepherd/server && uvicorn main:app --port 8070 --host 0.0.0.0
```
Check the transformation of textract json -> 
1. Column headers
2. Univseral fields 

**Check 1 - column headers detected for form 000:**
```bash
curl -s -X POST http://localhost:8070/api/analyze/json \
  -H "Content-Type: application/json" \
  -d @../cloud/output/000_layout.json \
  | jq '.tables[0].column_headers | map(.text)'
```
Expected: `["S.No", "SPP Name/Local Name", "Habit", "DBH in cms", "Phenological condition"]`

**Check 2 - universal fields (KEY_VALUE_SET) present:**
```bash
curl -s -X POST http://localhost:8070/api/analyze/json \
  -H "Content-Type: application/json" \
  -d @../cloud/output/000_layout.json \
  | jq '[.key_value_pairs[] | {key, value, key_confidence}]'
```
Expected:
```json
[
  {"key": "1210",                    "value": "10.12.30",          "key_confidence": 67.0},
  {"key": "Area Name",              "value": "BKM",               "key_confidence": 99.3},
  {"key": "Date",                   "value": "19/02/2025",        "key_confidence": 91.8},
  {"key": "Plot #",                 "value": "2",                 "key_confidence": 94.4},
  {"key": "Names of research team", "value": "AK,HA kk, MK, PK", "key_confidence": 97.9},
  {"key": "Transect #",             "value": "1",                 "key_confidence": 95.3},
  {"key": "Block Code: ,",          "value": "",                  "key_confidence": 34.8}
]
```

**Note:** No confidence filtering happens at extraction time. All fields - including low-confidence ones - are preserved. In Excel, these will appear with red borders/fill so the reviewer can see they need attention. The confidence score determines cell coloring, never whether to include the field.

**Check 3 - json to excel transformation:**

```bash
# Generate Excel from existing Textract JSON (no AWS call)
curl -s -X POST http://localhost:8070/api/upload/json \
  -H "Content-Type: application/json" \
  -d @../cloud/output/000_layout.json \
  -o output.xlsx
```

Open `output.xlsx` and verify:
- Row 1: color legend (red sample, orange sample, plain label)
- Rows 3-9: 7 universal fields as key-value pairs
  - "1210" and "Block Code: ," should have **red** key+value cells (low confidence)
  - "Names of research team" value should be **red** (48.2% confidence)
  - "Area Name", "Date", "Plot #", "Transect #" should be **plain** (85%+)
- Row 11: 5 column headers (bold, gray): S.No, SPP Name/Local Name, Habit, DBH in cms, Phenological condition
- Rows 12-55: 44 data rows
  - S.No column should be mostly **red** (confidence 42-65%)
  - SPP Name, DBH columns should be mostly **plain** (85%+)
- Distribution: ~43 red cells, ~33 orange, ~90 plain

**Check 4 - json to excel transformation:**

```console 
$ cd pwa/
$ npm run dev
# navigate to localhost:5174
```
Login with test user credentials. You should be able to take photographs and convert to excel. 

## POC server APIs

The agent server (`agent/server/`) provides post-processing checks (serial
renumbering, species fuzzy-matching) that run after the main upload pipeline.

See [agent/server/README.md](../agent/server/README.md) for all endpoints.

## Remaining work

~~### Phase 4 - Google Drive + preprocessor fallbacks~~
~~10. OAuth 2.0 + Drive API~~

### Polish

5. Client-side image contrast/brightness enhancement before upload. Textract misses
    handwriting in low-contrast regions (e.g. last rows near page edges where lighting
    fades). Adjusting contrast before sending to Textract should improve OCR accuracy
    for these edge cases.
...

