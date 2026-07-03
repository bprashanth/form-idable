# Golden reference — TreePhenologyTwoTrails.pdf, page 1

Built by: rendering `v1_overview.png` (zoom 2), `crop_header.png`,
`crop_colheader.png`, `crop_deadrow.png` (zoom 4), cross-checked against
`v1.json`'s table (39x15, header spans rows 1-2) and key_values (6).

## Structure (2 sections)

1. Header metadata (from `v1.json` key_values, all clean, conf ~95):
   - Trail: Andiparai Left Side
   - Date: 01-01-2019
   - Observers: Vanidas & Moorthi (Textract raw: "Vanidas S Moorths" —
     light correction, "S"→"&", "Moorths"→"Moorthi")
   - Weather: Cloudy
   - Start time: 9:12 am
   - Notes: *(blank — not filled in)*

2. Main data table (Textract table[0], 39 rows incl. 2-row header x 15
   cols → 37 data rows). The 2-row header was merged into one row:
   `Tree No, Species, H (m), GBH (cm), Multistem, Leaves Flush, Leaves
   Mature, Leaves Fallen, Flowers Buds, Flowers Open, Flowers Fallen,
   Fruits Unripe, Fruits Ripe, Fruits Fallen, Notes`. 37 data rows
   (tree numbers 1-48, not contiguous — several tree numbers are
   skipped, e.g. 6, 10, 17, 21, 26, 32, 35, 38, 40, 43, 45 don't appear;
   this is normal for a survey transect, not a transcription error).

## Approach taken: minimal cell-level correction (deliberate)

This page is **dense**: 37 rows x 15 cols, and ~9 of those columns
(Leaves/Flowers/Fruits x 3 sub-columns each) are single-character cells
(`0`-`4`, `Y`/`N`/`y`, `X`, and several harder-to-read symbols like `Z`,
`7`, `"`, `8N`, `XX`, `D`). Per `system_prompt.md`'s quality bar
("individual cell values do not need to be perfect... don't zoom in to
verify individual cell values"), **the golden transcribes these columns
essentially as Textract read them**, with only one structural fix (the
DEAD/DRY row, below) — this matches the bar the production agent itself
is held to, rather than hand-correcting ~100 ambiguous single-char
cells.

## Structural fix: row for Tree 30 ("DEAD/DRY tree (May 2017)")

Raw Textract table row 27 (tree 30, Glochidion malabaricum, H=16,
GBH=126) has the handwritten annotation **"DEAD/DRY tree (May 2017)"**
smeared across the Leaves-Mature/Leaves-Fallen/Flowers-Buds cells
(`'DEAD/DRY tree'`, `'(May'`, `'2017)'`) instead of in the Notes column,
with the rest of the Leaves/Flowers/Fruits cells empty (`crop_deadrow.png`
confirms: the handwriting visually starts mid-row, overlapping several
column boundaries). Golden moves this text to the **Notes** column as a
single string `"DEAD/DRY tree (May 2017)"` and leaves all
Leaves/Flowers/Fruits cells for this row blank+flagged — this is the one
row where "transcribe as Textract gave it" would produce a clearly wrong
column alignment (data-looking text in numeric columns).

## A hypothesis worth testing against codex's output (not corrected here)

Looking at the **"Fallen" sub-column of each of Leaves/Flowers/Fruits**
(cols 8, 11, 14): unlike the other numeric sub-columns (Flush/Mature,
Buds/Open, Unripe/Ripe — which are clean `0`-`4` digits), the "Fallen"
columns are dominated by `Y`/`N`/`y` with scattered look-alikes (`Z`,
`X`, `7`, `2`, `"`, `8N`, `XX`, `D`). This strongly suggests **"Fallen" is
a binary Yes/No field** ("was any fallen [leaf/flower/fruit] litter
observed under this tree?"), not a 0-4 count like its neighbors — and
most of the odd single-char reads (`Z`, `2`, `7`, `"`) are OCR
mis-reads of handwritten `Y`/`N`. **This is left as Textract read it in
the golden** (per the "don't hand-correct ~100 cells" decision above),
but is a good test: does codex, looking at crops of this column, notice
the Y/N pattern and normalize the outliers — or does it (like the
golden) leave them as Textract's raw single chars?

## Notes / what this PDF stress-tests

- **Sheer column/row density** (37x15 = 555 data cells) — does codex's
  crop strategy scale, or does it spend most of its turn budget on a
  handful of crops and call it done (as the quality bar permits)?
- **The DEAD/DRY row** — a real "row doesn't fit the column grid"
  case, structurally similar to PDF1's "section label with no data"
  but inverted (here there IS a row, but its content doesn't belong in
  the columns it landed in).
- **The Fallen-column Y/N-vs-OCR-garble pattern** — if codex normalizes
  this column toward Y/N, that's a signal the production prompt could
  call out "a column of repeated similar single characters with a few
  outliers is probably one categorical field — normalize outliers to
  the dominant value(s), don't transcribe OCR noise literally", which
  would generalize beyond just this PDF.
