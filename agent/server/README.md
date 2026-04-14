# Agent Server APIs

POC FastAPI server (`agent/server/`) that provides post-processing checks on the
Excel output from the main upload pipeline. All endpoints are prefixed `/agent/`.

Deployed as an AWS Lambda Function URL (no API Gateway). No auth — public API.

## Architecture

```
PWA (ResultView)               Agent Server (FastAPI)
----------------               ---------------------
.xlsx from upload --POST /agent/infer-types--> column type inference
                  --POST /agent/check-serial--> serial renumbering  -> corrected .xlsx
                  --POST /agent/check-species-> fuzzy species match -> proposals
                  --POST /agent/apply-species-> apply corrections   -> corrected .xlsx
```

## Running locally

```bash
cd agent/server
uvicorn main:app --host 0.0.0.0 --port 8071 --reload
```

The PWA dev server proxies `/agent/*` to `http://localhost:8071` by default
(`vite.config.js`). To proxy to the deployed Lambda instead, set in `pwa/.env.local`:

```
AGENT_TARGET=https://<your-function-url>.lambda-url.ap-south-1.on.aws
```

## Deploy

```bash
cd agent/server
./deploy/deploy.sh
```

See `deploy/README.md` for first-time setup. The Lambda Function URL is printed at
the end and must be pasted into `netlify.toml`.

---

## API Endpoints

### GET /agent/health

Health check. Returns HTTP 200.

```json
{"status": "ok"}
```

---

### POST /agent/infer-types

Infers the semantic type of each column in the uploaded Excel file by fuzzy-matching
column headers against a cheatsheet of known column names.

**Request:** multipart, field `file` — `.xlsx` file.

**Response:**
```json
{
  "type_map": {
    "S.No": {"type": "serial"},
    "SPP Name/Local Name": {"type": "species"}
  },
  "all_headers": ["S.No", "SPP Name/Local Name", "Habit", "DBH in cms"]
}
```

`type_map` contains only the headers that matched a known type. Unrecognised headers
are absent from `type_map` but present in `all_headers`.

**Check:**
```bash
curl -s -X POST http://localhost:8071/agent/infer-types \
  -F "file=@output.xlsx" | jq .
```

---

### POST /agent/check-serial

Renumbers the serial column(s) sequentially (1, 2, 3, …) overwriting whatever
values Textract extracted. Returns the corrected `.xlsx` and the row count in a
response header.

**Request:** multipart fields:
- `file` — `.xlsx` file
- `type_map` — JSON string (output of `/agent/infer-types`)

**Response:** `.xlsx` file (binary).

**Response headers:**
- `X-Row-Count: <n>` — number of data rows renumbered.

**Error:** HTTP 400 if `type_map` contains no `serial`-typed column.

**Check:**
```bash
curl -s -X POST http://localhost:8071/agent/check-serial \
  -F "file=@output.xlsx" \
  -F 'type_map={"S.No":{"type":"serial"}}' \
  -D - -o corrected.xlsx | grep X-Row-Count
```
Expected: `X-Row-Count: 44` (or however many data rows are in the file).

---

### POST /agent/check-species

Fuzzy-matches each unique species value in the Excel file against the species
database (`data/species_name.csv`). Returns proposed corrections with match
provenance, sorted by first serial number so proposals appear in document order.

**Request:** multipart fields:
- `file` — `.xlsx` file
- `type_map` — JSON string (output of `/agent/infer-types`)

**Response:**
```json
{
  "proposals": [
    {
      "original": "kage",
      "corrected": "Litsea wightiana",
      "matched_display": "Kage",
      "match_field": "abbr",
      "score": 100.0,
      "first_serial": 1
    }
  ]
}
```

`match_field` is one of `abbr`, `expanded`, or `toda_name` — which column of the
species DB produced the match. `first_serial` is the serial number of the first row
where this species value appears (from the post-serial-correction Excel).

**Error:** HTTP 400 if `type_map` contains no `species`-typed column.

**Check:**
```bash
curl -s -X POST http://localhost:8071/agent/check-species \
  -F "file=@corrected.xlsx" \
  -F 'type_map={"S.No":{"type":"serial"},"SPP Name/Local Name":{"type":"species"}}' \
  | jq '.proposals[] | {original, corrected, match_field, score}'
```

---

### POST /agent/apply-species

Applies species corrections to the Excel file, replacing original values with the
corrected (expanded) species names.

**Request:** multipart fields:
- `file` — `.xlsx` file
- `type_map` — JSON string (output of `/agent/infer-types`)
- `corrections` — JSON object mapping original value → corrected value:
  `{"kage": "Litsea wightiana", "nelli": "Phyllanthus emblica"}`

**Response:** `.xlsx` file (binary).

**Check:**
```bash
curl -s -X POST http://localhost:8071/agent/apply-species \
  -F "file=@corrected.xlsx" \
  -F 'type_map={"SPP Name/Local Name":{"type":"species"}}' \
  -F 'corrections={"kage":"Litsea wightiana"}' \
  -o final.xlsx
# Open final.xlsx and verify the species column values are updated.
```

---

### GET /agent/cheatsheet

Returns the current column-type cheatsheet used by `/agent/infer-types`.

**Response:** JSON object mapping canonical column names to type metadata.

---

### PUT /agent/cheatsheet

Replaces the cheatsheet. Accepts the full cheatsheet JSON as the request body.

**Response:** `{"ok": true}`

---

### GET /agent/species-db

Returns all entries in the species database as a JSON array.

**Response:**
```json
[
  {"abbr": "Kage", "expanded": "Litsea wightiana", "toda_name": "NA"},
  ...
]
```

---

### POST /agent/species-db/entry

Appends a new entry to the species database CSV.

**Request body (JSON):**
```json
{"abbr": "Nelli", "expanded": "Phyllanthus emblica", "toda_name": "NA"}
```

**Response:** `{"ok": true}`
