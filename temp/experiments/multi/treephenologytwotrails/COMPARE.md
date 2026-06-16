# Compare — codex output.xlsx vs golden.xlsx (TreePhenologyTwoTrails.pdf, page 1)

**Result: essentially identical** — 37x15 data table matches golden
cell-for-cell, including all the "Fallen"-column OCR artifacts
(`Z`, `X`, `2`, `7`, `"`, `8N`, `XX`, `D`, etc.) that the golden
deliberately left as Textract read them. 57,166 tokens (highest of the
4 PDFs done so far — likely just from writing out 555 data cells, not
from extra cropping).

## Header metadata — identical, including the same corrections

- All 6 fields match exactly, **including the same two light
  corrections** the golden made independently: `Observers: Vanidas &
  Moorthi` (raw Textract: "Vanidas S Moorths") and `Start time: 9:12 am`
  (normalized from raw "9:12 aM"). Codex made the same calls without
  being told what the "right" correction was.

## DEAD/DRY row (tree 30) — same structural fix, independently made

Both golden and codex: moved `"DEAD/DRY tree (May 2017)"` into the Notes
column, left all 9 Leaves/Flowers/Fruits cells for that row blank, and
**flagged the whole row** (golden flagged cols 6-15; codex flagged
F33:O33, i.e. cols 6-15 — the same range). This was the one row where
"transcribe Textract's table as-is" would clearly misalign data into
numeric columns, and both builders caught it the same way.

## The "Fallen column is really Y/N" hypothesis — left untested by both

The golden's `golden.md` flagged a hypothesis: the "Fallen" sub-columns
under Leaves/Flowers/Fruits look like they should be a binary Y/N field
(dominated by `Y`/`N`/`y` with scattered OCR-garbled look-alikes `Z`,
`2`, `7`, `X`, `"`), unlike their numeric `0`-`4` neighbors
(Flush/Mature, Buds/Open, Unripe/Ripe). **Codex's output passes these
columns through exactly as Textract read them**, same as golden — it
did not crop into the Fallen columns to verify/normalize them. This is
consistent with the "individual cell values do not need to be perfect...
don't crop to verify" instruction in `system_prompt.md`, which both the
golden-builder and codex followed literally for this dense table.

## One cosmetic difference: codex flagged the entire header row

Codex applied a yellow fill to all 15 header cells (row 8) — golden did
not. Minor, doesn't affect data, possibly codex flagging "I merged a
2-row Textract header into 1 row, here's where that happened."

## Takeaway for scope/descope

- On a **dense, mostly-numeric grid** (37x15, single-char cells), codex
  converges to essentially a pass-through of Textract's raw values plus
  one well-chosen structural fix (the DEAD/DRY row) — it does **not**
  spend its turn budget trying to disambiguate ~100 single-character
  cells, which matches the prompt's explicit guidance.
- **This raises a real scope question for the production pipeline**:
  if the "Fallen" columns are genuinely a Y/N field (very plausible —
  numeric columns are clean 0-4, "Fallen" columns are ~90% Y/N with a
  handful of OCR artifacts), then leaving Textract's raw garbled chars
  (`Z`, `2`, `7`, `"`, `8N`) in those cells could propagate OCR noise
  into a field that's supposed to be categorical. **A targeted
  preprocessing step in `textract_minimize.py`** — e.g., for a column
  where >80% of values are in a small set (`{Y,N,y}`), normalize
  near-miss single-char outliers to the nearest of that set and flag
  the rest — would fix this *without* requiring the agent to spend
  crop budget on it. This is a concrete "improve the input to the
  agent" finding, distinct from PDF1-3's "the agent+crops already
  handles this" findings.
- No new off-table sections on this page (unlike PDF2/PDF3) — `Notes`
  column is part of the existing table, and `key_values` covered all
  header fields cleanly. `v2_meta.json` correctly omitted by both.
