# Adding a new ecological context handler

This manual walks through adding support for a new column type — meaning a column whose contents Textract extracts poorly and where domain knowledge can be applied to produce better values.

The example used throughout is a hypothetical `tally` type: columns that contain hand-drawn tally marks (`IIII`, `llll`, `1111`). Textract turns these into a mix of `I`, `l`, `1`, and `|`; the correct value is just the count of those marks.

---

## 1. Decide what the handler needs

Before writing any code, answer these questions:

1. **What does a cell in this column look like after Textract?** (e.g. garbled tally marks, a phonetic mis-transcription of a name, a fractional number where a whole number was expected)
2. **What should the corrected value be?** (e.g. count of marks, a canonical name from a reference list, a rounded integer)
3. **Does correction require a reference dataset?** Species names do; serial numbers don't; tally marks don't.
4. **Does the user need to review corrections, or can they be applied automatically?** Serial numbers are always 1…N so no review is needed. Species names are ambiguous so the user reviews proposals. Tally counts are deterministic so no review is needed.

---

## 2. Add the type to the cheatsheet

Open `agent/server/cheatsheet.json` and add an entry under `"types"`:

```json
{
  "types": {
    "species": { ... },
    "serial":  { ... },
    "tally": {
      "keywords": ["tally", "count", "no. of", "number of"],
      "units": null,
      "ignore_headers": []
    }
  }
}
```

`keywords` is a list of lowercase substrings. A column header matches if any keyword is a substring of the lowercased header, or vice versa. Add `ignore_headers` entries for exact header strings that should never be matched (e.g. a column called "Tally" that is actually free text).

> The cheatsheet is read from disk on every request, so the change takes effect immediately on a running server without a restart.

---

## 3. Add the service logic

Create `agent/server/services/tally.py` (or add a function to an existing service if it is small):

```python
import re

def count_tally_marks(value: str) -> int:
    """Return the number of tally-mark characters (I, l, 1, |) in a cell."""
    return len(re.findall(r"[Il1|]", str(value)))


def apply_tally_counts(xlsx_bytes: bytes, tally_cols: list[str]) -> bytes:
    """
    Replace every cell in each tally column with the count of tally-mark
    characters found in that cell. Returns the modified workbook bytes.
    """
    import openpyxl, io
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
    ws = wb.active

    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    tally_col_indices = [i + 1 for i, h in enumerate(headers) if h in tally_cols]

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            if cell.column in tally_col_indices:
                cell.value = count_tally_marks(cell.value or "")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

Keep the service pure Python — no FastAPI imports. The router imports the service; the service knows nothing about HTTP.

---

## 4. Add the router endpoint(s)

For a type that requires no user review, a single `POST /agent/check-tally` endpoint that returns the corrected `.xlsx` is sufficient (same pattern as `check-serial`).

Add to `agent/server/routers/checks.py`:

```python
from services import tally as tally_svc   # add this import at the top

@router.post("/check-tally")
async def check_tally(
    file: UploadFile = File(...),
    type_map: str = Form(...),
):
    xlsx_bytes = await file.read()
    tm = json.loads(type_map)
    tally_cols = [col for col, info in tm.items() if info["type"] == "tally"]
    if not tally_cols:
        raise HTTPException(400, "No tally columns in type_map")
    corrected = tally_svc.apply_tally_counts(xlsx_bytes, tally_cols)
    return Response(
        content=corrected,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=corrected.xlsx"},
    )
```

If your handler produces proposals for the user to review (like species), you will need two endpoints: one to generate proposals and one to apply accepted corrections. Follow the `check-species` / `apply-species` pair in `checks.py` as a template.

If your handler needs its own reference data or configuration endpoints (like `species-db`), create a new router file `agent/server/routers/tally.py` and register it in `agent/server/main.py`:

```python
from routers import checks, cheatsheet, species_db, tally   # add tally

app.include_router(tally.router, prefix="/agent")
```

---

## 5. Wire up the UI

Open `pwa/src/views/ResultView.vue`. The agent pipeline is implemented in the `<script setup>` section as a series of async functions (`inferTypes`, `checkSerial`, `checkSpecies`, …). Add a parallel function for your new type:

```js
// Stage 1c — tally
async function checkTally() {
  checkingTally.value = true
  agentError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    fd.append('type_map', JSON.stringify(typeMap.value))
    const res = await agentPost('/agent/check-tally', fd)
    xlsxBytes.value = await res.arrayBuffer()
  } catch (e) {
    agentError.value = `Tally check failed: ${e.message}`
  } finally {
    checkingTally.value = false
  }
}
```

Add `const checkingTally = ref(false)` with the other state refs, and a `hasTally` computed:

```js
const hasTally = computed(() =>
  typeMap.value && Object.values(typeMap.value).some(v => v.type === 'tally')
)
```

Add the button in the template, after the serial button and before the species button:

```html
<button
  v-if="typeMapConfirmed && hasTally"
  class="w-full h-12 rounded-lg border border-yellow-700 text-yellow-300 font-medium active:bg-gray-800 transition-colors disabled:opacity-40"
  :disabled="checkingTally"
  @click="checkTally"
>{{ checkingTally ? 'Counting tallies…' : 'Fix Tally Columns' }}</button>
```

If your handler returns proposals for user review, model the UI after the species review split-view (left panel with proposals, right panel showing the form image with bbox highlighting for the active row).

---

## 6. Test locally

```bash
# Terminal 1 — agent server
cd agent/server
uvicorn main:app --host 0.0.0.0 --port 8071 --reload

# Terminal 2 — smoke test without UI
curl -s -X POST http://localhost:8071/agent/check-tally \
  -F "file=@pwa/output.xlsx" \
  -F 'type_map={"Tally":{"type":"tally","confidence":"high","matched_keyword":"tally"}}' \
  -o corrected.xlsx
# open corrected.xlsx and check the tally column values are now integers
```

See `agent/test/TESTING.md` for how to run the full test suite against a local or deployed server.

---

## 7. Deploy

No infrastructure changes are needed — the agent server is a single Lambda. Rebuild and push:

```bash
cd agent/server
./deploy/deploy.sh
```

The Lambda Function URL does not change on redeploy. If it does (e.g. after a teardown/recreate), update `netlify.toml` and push to Netlify.
