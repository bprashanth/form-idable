# End-to-end pipeline test

Manual curl walkthrough of the full form → Excel flow, mirroring what the PWA does when a user uploads a form, runs the agent pipeline, and downloads the corrected file.

## Prerequisites

Both servers must be running locally. Each has its own venv.

### good-shepherd (Textract + xlsx generation) — port 8070

```bash
cd ~/src/github.com/bprashanth/good-shepherd/server
source ../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8070 --reload
```

### agent server (column type checks) — port 8071

```bash
cd ~/src/github.com/bprashanth/form-idable/agent/server
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8071
```

### Health checks

```bash
curl -s http://localhost:8070/api/health   # → {"status":"ok"}
curl -s http://localhost:8071/agent/health # → {"status":"ok"}
```

---

## Step 0 — source config and get a Cognito token

The good-shepherd `/api/upload` endpoint requires a Cognito JWT. The config and test credentials live in the good-shepherd repo.

```bash
source ~/src/github.com/bprashanth/good-shepherd/server/deploy/config.sh
source ~/src/github.com/bprashanth/good-shepherd/server/deploy/test-credentials.env
# ^ sets TEST_USERNAME and TEST_PASSWORD

TOKEN=$(aws cognito-idp initiate-auth \
  --region ap-south-1 \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "$COGNITO_CLIENT_ID" \
  --auth-parameters USERNAME="$TEST_USERNAME",PASSWORD="$TEST_PASSWORD" \
  --query 'AuthenticationResult.IdToken' \
  --output text)
```

---

## Step 1 — upload the form image → good-shepherd → xlsx

The PWA POSTs the cropped image. The crop is important: it should contain only the data grid, not the top metadata block (date, area name, block code). Without the crop the xlsx will contain multiple small tables from the metadata before the main table, which confuses the agent's header detection.

```bash
curl -s -X POST http://localhost:8070/api/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@path/to/form.jpg" \
  | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
print('summary:', d['summary'])
print('rows (first 3):', d['rows'][:3])
with open('/tmp/output.xlsx', 'wb') as f:
    f.write(base64.b64decode(d['xlsx']))
print('saved /tmp/output.xlsx')
"
```

**Response shape:**
```json
{
  "xlsx": "<base64>",
  "summary": {"rowCount": 43, "flaggedCount": 43},
  "rows": [
    {"system_serial": 1, "bbox": {"left": 0.34, "top": 0.05, "width": 0.61, "height": 0.015}},
    ...
  ]
}
```

`rows` is the per-row bounding box list used by the PWA to highlight rows in the image when reviewing species proposals. The `system_serial` maps to the `(Good Shepherd) Row ID` column written into the xlsx.

---

## Step 2 — infer column types

```bash
curl -s -X POST http://localhost:8071/agent/infer-types \
  -F "file=@/tmp/output.xlsx" | jq .
```

**Response shape:**
```json
{
  "type_map": {
    "S.No": {"type": "serial", "confidence": "high", "matched_keyword": "s.no"},
    "SPP Name/Local Name": {"type": "species", "confidence": "medium", "matched_keyword": "spp"}
  },
  "all_headers": ["S.No", "SPP Name/Local Name", "Habit", "DBH in cms", "Phenological condition"]
}
```

The PWA shows this to the user for confirmation. `type_map` contains only matched columns; `all_headers` is every column (used to show unmatched columns to the user so they can edit the cheatsheet if needed).

In the PWA the user clicks **Confirm** to proceed, or **Edit Cheatsheet** to add keywords for missed columns.

---

## Step 3 — fix serial numbers (if a serial column was detected)

```bash
TYPE_MAP='{"S.No":{"type":"serial","confidence":"high","matched_keyword":"s.no"},"SPP Name/Local Name":{"type":"species","confidence":"medium","matched_keyword":"spp"}}'

curl -s -X POST http://localhost:8071/agent/check-serial \
  -F "file=@/tmp/output.xlsx" \
  -F "type_map=$TYPE_MAP" \
  -D /tmp/serial_headers.txt \
  -o /tmp/output_serial.xlsx

grep -i x-row-count /tmp/serial_headers.txt
# X-Row-Count: 43
```

Returns a corrected `.xlsx` (binary) with serial values rewritten 1, 2, 3 … N. The row count comes back in the `X-Row-Count` response header. The PWA replaces its in-memory xlsx bytes with this response.

---

## Step 4 — get species correction proposals

```bash
curl -s -X POST http://localhost:8071/agent/check-species \
  -F "file=@/tmp/output_serial.xlsx" \
  -F "type_map=$TYPE_MAP" | jq '.proposals[:5]'
```

**Response shape:**
```json
{
  "proposals": [
    {
      "original": "kage",
      "corrected": "Litsea wightiana",
      "matched_display": "Kage",
      "match_field": "toda_name",
      "score": 100.0,
      "system_serials": [3, 8, 12, 19]
    }
  ]
}
```

Each proposal represents a unique raw value from the species column.  `system_serials` is the list of `(Good Shepherd) Row ID` values where this raw value appears — used to target corrections and to drive bbox highlighting in the PWA (click a proposal, the corresponding form rows light up in the image).

The PWA enters a split-view: proposals on the left, the form image with highlighted bboxes on the right. The user can accept, edit, or skip each proposal. The **Save changes** button calls Step 5.

---

## Step 5 — apply accepted corrections

Build the corrections array from the proposals you want to apply. `system_serials` scopes each correction to specific rows (pass all serials from the proposal to correct every occurrence; pass a subset for partial correction).

```bash
CORRECTIONS='[
  {"original": "kage",  "corrected": "Litsea wightiana",    "system_serials": [3, 8, 12, 19]},
  {"original": "nelli", "corrected": "Phyllanthus emblica",  "system_serials": [5]}
]'

curl -s -X POST http://localhost:8071/agent/apply-species \
  -F "file=@/tmp/output_serial.xlsx" \
  -F "type_map=$TYPE_MAP" \
  -F "corrections=$CORRECTIONS" \
  -o /tmp/form_output_final.xlsx
```

Returns the corrected `.xlsx`. This is what the user downloads in the PWA.

---

## Step 6 — inspect the final file

```bash
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('/tmp/form_output_final.xlsx')
ws = wb.active
for row in ws.iter_rows(values_only=True):
    if any(v is not None for v in row):
        print(row)
"
```

---

## Notes

**Crop matters.** If the uploaded image includes the handwritten metadata block above the data grid (date, area name, block code, team names), Textract renders those as small tables in the xlsx before the main table. The agent's `_find_header_row` looks for the first row with 2+ bold cells, which is then the first mini-table rather than the real data grid header. Always crop to the grid only before uploading.

**Auth is only on good-shepherd.** The agent server (`/agent/*`) has no auth — in production it is a public Lambda Function URL. Only `/api/upload` (and other good-shepherd endpoints) require the Cognito JWT.

**Cheatsheet is live-editable.** The agent server reads `cheatsheet.json` on every request. You can update it via `PUT /agent/cheatsheet` (or through the PWA sidebar) without restarting the server.
