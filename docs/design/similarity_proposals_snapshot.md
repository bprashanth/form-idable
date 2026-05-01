# Snapshot: Similarity Proposals — State as of 2026-04-28

## Status of `similarity_proposals.md`

`docs/design/similarity_proposals.md` is a **pure design document** — it was written
at the end of the previous session as a spec. **None of the features it describes have
been implemented yet.** The implementation phase had not started when context was lost.

---

## What IS already implemented (pre-dates the design doc)

These features are in the codebase and working:

### Agent server (`agent/server/`)

| File | What's there |
|------|-------------|
| `config.py` | `SYSTEM_SERIAL_HEADER = "(Good Shepherd) Row ID"` |
| `services/excel.py` | `extract_species_with_system_serials` — collects unique species values with all their system_serials; raises ValueError if reserved column absent |
| `services/excel.py` | `apply_species_corrections` — applies corrections filtered strictly by system_serial (exact string match on `original`) |
| `routers/checks.py` | `POST /check-species` — returns `{proposals: [{original, corrected, matched_display, match_field, score, system_serials}]}` |
| `routers/checks.py` | `POST /apply-species` — accepts `{original, corrected, system_serials}` corrections |
| `routers/checks.py` | `POST /lookup-species` — single-value re-lookup for edit flow |

### PWA (`pwa/src/`)

| File | What's there |
|------|-------------|
| `composables/useFormStore.js` | `rowBboxes: ref(null)` — Map<system_serial, bbox> populated from upload response |
| `views/ProcessingView.vue` | Decodes JSON upload response; populates `xlsxBytes`, `summary`, `rowBboxes` |
| `components/FormImageOverlay.vue` | Two-color overlay: red (`primaryEntries`) = first system_serial, amber (`secondaryEntries`) = remaining system_serials; consecutive-serial merge; BUFFER=0.008 |
| `views/ResultView.vue` | Species review split view; proposal cards with edit/lookupSpecies/pending_confirm/reviewed states; "Update all / Just this row" confirmation; green border for reviewed; "Save changes" blocked while any pending_confirm |

---

## What is NOT yet implemented (from `similarity_proposals.md`)

### 1. Case-insensitive siblings (Section 1 of design doc)

**File: `agent/server/services/excel.py`**

`extract_species_with_system_serials` currently uses raw `str(cell.value).strip()` as
the dedup key, so "Kage" and "kage" produce two separate proposals.

**Fix needed:**
```python
# in extract_species_with_system_serials:
v = str(cell.value).strip()
key = v.lower()          # normalize for dedup
seen.setdefault(key, {"value": v, "serials": []})
seen[key]["serials"].append(system_serial)
# return [{"value": entry["value"], "system_serials": entry["serials"]} ...]
```

`apply_species_corrections` currently does exact string match (`v in correction_map`).

**Fix needed:**
```python
# build map keyed by lowercase original
correction_map = {c["original"].lower(): ...}
# match: v.lower() in correction_map
```

### 2. `SIMILAR_SPECIES_THRESHOLD` config

**File: `agent/server/config.py`**

Missing:
```python
import os
SIMILAR_SPECIES_THRESHOLD = int(os.environ.get("SIMILAR_SPECIES_THRESHOLD", 70))
```

### 3. Similar proposals grouping in `check-species`

**File: `agent/server/routers/checks.py`**

`check-species` currently returns proposals with no `similar_proposals` field.

**Fix needed:** After generating proposals, group by `corrected` value. For each
proposal, list other proposals with the same `corrected` AND `score >=
SIMILAR_SPECIES_THRESHOLD` as `similar_proposals`:
```python
# Group by corrected value
from collections import defaultdict
corrected_groups = defaultdict(list)
for p in proposals:
    if p["corrected"] and p["score"] >= SIMILAR_SPECIES_THRESHOLD:
        corrected_groups[p["corrected"]].append(p)

# Attach similar_proposals to each proposal
for p in proposals:
    p["similar_proposals"] = [
        {"original": s["original"], "system_serials": s["system_serials"], "score": s["score"]}
        for s in corrected_groups.get(p.get("corrected"), [])
        if s is not p
    ]
```

**New response shape:**
```json
{
  "original": "Bootheham",
  "corrected": "Symplocos cochinchinensis",
  "score": 73.0,
  "system_serials": [3],
  "similar_proposals": [
    {"original": "Boothakani", "system_serials": [1, 5], "score": 100.0},
    {"original": "Boothern",   "system_serials": [7],    "score": 85.0}
  ]
}
```

### 4. Purple highlight layer in `FormImageOverlay.vue`

**File: `pwa/src/components/FormImageOverlay.vue`**

Missing: third prop `similarEntries: [{serial, bbox}]` and corresponding purple overlay divs.

### 5. Two-step confirmation + "Related" line in `ResultView.vue`

**File: `pwa/src/views/ResultView.vue`**

Missing:
- `similarEntries` computed prop (all system_serials across `similar_proposals` of active proposal)
- "Related" line in proposal card (shows sibling originals + their row numbers)
- `pending_similar` state after `pending_exact` resolves
- "Apply to similar / Skip" buttons
- `resolved_via` label on folded proposal cards (green border, "Resolved via X", not editable)
- State machine: `pending_exact → pending_similar → reviewed`

**State machine per design doc:**
```
initial → (user edits, clicks done) → looking_up
  looking_up → (RPC returns, system_serials.length == 1, no similar) → reviewed
  looking_up → (RPC returns, system_serials.length > 1 OR has similar) → pending_exact
    pending_exact → (Update all / Just this row) → pending_similar (if has similar)
    pending_exact → (Update all / Just this row) → reviewed (if no similar)
      pending_similar → (Apply to similar) → reviewed  [siblings → resolved_via]
      pending_similar → (Skip) → reviewed  [siblings stay independent]
```

---

## Open design question (unanswered)

When "Apply to similar" is chosen, should folded proposal cards:
- **Stay visible** — green border, "Resolved via X" label, not editable (design doc says this; prior session leaned toward it)
- **Disappear** — removed from the proposals list

The design doc says keep them visible. Confirm before implementing `pending_similar`.

---

## How to test the current state (what's already working)

### Prerequisites
```bash
# Terminal 1: agent server
cd /home/desinotorious/src/github.com/bprashanth/form-idable/agent/server
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8071 --reload

# Terminal 2: PWA
cd /home/desinotorious/src/github.com/bprashanth/form-idable/pwa
npm run dev
```

The PWA proxies `/agent/*` → `http://localhost:8071` by default.
You need the good-shepherd server running for `/api/upload` (or use a pre-existing
`output.xlsx` file in `pwa/` as a stand-in for the XLSX).

### Test flow
1. Open PWA → capture/crop a form image → ProcessingView auto-uploads
2. ResultView appears with Download button and "Data Checks" section
3. Click "Infer Column Types" → confirm the type map
4. Click "Check Serial Numbers" (if serial column detected)
5. Click "Check Species Names" → proposal cards appear; split view shows form image
6. Click a proposal card → red box on primary row, amber boxes on secondary rows
7. Click "edit" on a proposal → type a different abbr → "done" → spinner → "Update all / Just this row"
8. "Update all" → green border on card
9. "Save changes" → corrected XLSX replaces in-memory bytes; download to verify

### Known gap during testing
"Kage" and "kage" in the same sheet will show as two separate proposals (case-insensitive
dedup is the first thing to implement). No `similar_proposals` grouping yet.

---

## Implementation order (when ready to build)

1. `agent/server/config.py` — add `SIMILAR_SPECIES_THRESHOLD`
2. `agent/server/services/excel.py` — case-insensitive dedup + case-insensitive apply
3. `agent/server/routers/checks.py` — attach `similar_proposals` to each proposal
4. `pwa/src/components/FormImageOverlay.vue` — add `similarEntries` prop + purple layer
5. `pwa/src/views/ResultView.vue` — `similarEntries` computed, "Related" line, `pending_similar` state, folded card display

Steps 1–3 are server-only and can be tested with `curl` before touching the PWA.
