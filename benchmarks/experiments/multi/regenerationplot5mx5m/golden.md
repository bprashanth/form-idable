# Golden reference — RegenerationPlot5mx5m.pdf, page 1

Built by: rendering `v1_overview.png` (zoom 2) and several targeted crops
(`crop_rows.png`, `crop_rows2.png`, `crop_r1r2_seedlings.png`,
`crop_r2_seedling.png`, `crop_species.png`, `crop_bottom_left.png`,
`crop_bottom_right.png`, `crop_topleft.png`) at zoom 5-14, cross-checked
against `v1.json`'s table (23x5), key_values (14), other_text (6).

## Structure (4 sections)

1. Title: "Regeneration plot data sheet" (other_text, conf 100).

2. Header metadata (from `v1.json` key_values, mostly clean):
   - Date: 15/10/18
   - Site: Condure Aol (handwritten plot code — **uncertain**, conf 94.9
     but the handwriting itself is ambiguous, e.g. could be "Condorea"
     vs "Condure")
   - GPS point: 10.30217', 76.84301 — **uncertain**, both Textract's raw
     read (`"10.30217', 76,84301"`, conf 95.6) and a crop disagreed
     slightly on the leading digit (`10.2...` vs `10.3...`)
   - Data collectors: SR, SK, RS
   - Type (R/U/B/E): *(blank — not filled in)*
   - Year restored: *(blank — not filled in)*
   - Canopy densitometer: 0, 0, 0, 0 (closed/open: closed — checkmark
     next to "closed/open") — **uncertain**, raw Textract conf only 60,
     one of the four "0"s is drawn as "∂"

3. Main data table (Textract table[0], 23 rows incl. header x 5 cols:
   `S No, Species, Seedlings, Saplings, Remarks`). Only **4 of 22** data
   rows are filled; rows 5-22 are empty.

   | S No | Species | Seedlings | Saplings | Remarks |
   |---|---|---|---|---|
   | 1 | Vdct Mdl *(uncertain abbreviation)* | 1 | 4 | |
   | 2 | Ficus exas *(likely "Ficus exasperata")* | 5 *(uncertain — see below)* | 1 | |
   | 3 | Lantana *(likely "Lantana camara")* | — | 1 | |
   | 4 | Xanthus flav *(uncertain)* | — | 1 | |

   **Tally-mark reading (this is the focus PDF for tally counts):**
   - Row 1 Saplings: Textract read `"1114"` — visually this is 4 vertical
     tally strokes with a closing diagonal (`llll` + `/`), i.e. **4**.
     Confident, not flagged.
   - Row 1 Seedlings: Textract read `")"` — a single curved tally stroke
     = **1**. Confident, not flagged.
   - Row 2 Seedlings: Textract read `"$"` — a dollar-sign-like symbol
     (vertical stroke + horizontal bar through it), most consistent with
     a **bundled tally of 5** (4 strokes + 1 diagonal/crossbar grouping
     them). Took as **5**, but this is the single most ambiguous mark on
     the page — **yellow-flagged**.
   - Row 2/3/4 Saplings: each a single `")"`-like stroke = **1**.
     Confident.
   - Rows 3-4 Seedlings: no mark — left empty (not `0`; per
     `system_prompt.md`'s dot/line convention, "no mark" ≠ "recorded
     zero" here, since there's no dot or strike-through, just nothing).

4. Two species-list sections that exist **only as fragmented
   `key_values`/`other_text`** — Textract's table[0] doesn't cover them
   at all, and its key/value pairing badly mis-keyed both lists:
   - "Canopy above 5x5" (left list): `1) Spathodea`, `2) [a genus name,
     crossed out] Tetramilis` — Textract's key_values for this list are
     `'11'=''` and `'21'='Mawangh Tetramilis.'` (numbers `1)`/`2)`
     misread as `11`/`21`).
   - "Other Species" (right list): `1) Polygonum(?)`, `2) ?(illegible)`,
     `3) Chrisholum(?)`, `4) Brackens(?)` — Textract's key_values are
     `'1)'='Doly gomes'`, `'2)'='grany'`, `'3)'=''`, `'4)'='Brackers'`.
   Both lists added as new sections, **whole-section yellow-flagged**
   per `system_prompt.md` step 2/4 (recovering shape, not confident on
   values). `v2_meta.json`-style entries would point at these two
   regions.

## Ignored as noise

- Top-left corner: a black binder-clip (artifact of scanning a paper
  stack) plus a short handwritten initial/signature below it, OCR'd by
  Textract as `'Done'` (other_text, conf 87.9, x≈0.108 y≈0.074). This is
  **not part of the form** — correctly ignorable per the "ignore stray
  entries" rule.
- A low-confidence `'1'` (conf 59.5) near the title — likely a page
  number, not transcribed.

## Notes / what this PDF stress-tests

- This PDF is the designated **tally-mark test**: per the earlier scope
  decision, actual tally counts (the Seedlings/Saplings columns) must
  **not** be descoped/ignored — they're the core data of this form. The
  one genuinely hard mark (row 2 Seedlings, the "$"-like bundled-5 tally)
  is the kind of cell where codex's crop access should make a real
  difference vs. a no-crop pass.
- Both species-list sections at the bottom are a **third variant** of
  "structure missing from v1.tables": unlike PDF2's "Dry weight" section
  (clean two-column grid of numbers), here Textract's key/value pairing
  actively *mis-grouped* the list items (numbers `1)`-`4)` became
  spurious keys `'11'`, `'21'`, `'1)'`...`'4)'` paired with the wrong
  values) — testing whether the agent can recognize "these key_values
  are garbage groupings, the real structure is two numbered species
  lists" rather than transcribing the bogus key/value pairs as-is.
