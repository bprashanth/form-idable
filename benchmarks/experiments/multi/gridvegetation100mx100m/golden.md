# Golden reference — GridVegetation100mx100m.pdf, page 1

Built by: rendering `v1_overview.png` (zoom 2), `crop_topleft.png`,
`crop_cancomp.png`, `crop_bottom_candensity.png`, `crop_bottom_cancomp.png`
(zoom 8), cross-checked against `v1.json`'s 4 tables (2x[6x7 "Alien trees"],
2x[~11x7 "Alien plant prevalence"]), 45 key_values, 40 other_text entries.

## Structure: TWO complete, near-identical form-sheets stacked on one page

This page is the designed stress test for "repeated form-blocks": the
top form is for **Grid M13**, the bottom form is for **Grid L13**, and
each repeats the same sub-structure:

1. Header metadata block (Grid no / Date / Observer / GPS Centroid /
   Altitude / Slope (clinometer) / Canopy density / Canopy composition /
   Disturbance)
2. Two **marginal 2x2 quadrant grids** ("CAN DENSITY" and "CAN. COMP"),
   drawn by hand in the left margin next to the metadata block, with
   N(orth)/S(outh) compass labels — **not present in any `v1.tables`
   entry at all**, only as scattered single-char `other_text`.
3. "6) Alien trees (Presence/Absence)" table (6x7, Textract table0/table2)
4. "* Other species:" free-text entry (key_value, right after table 6)
5. "7) Alien plant prevalence" table (11x7/12x7, Textract table1/table3),
   preceded by a printed "Cover: 0=Absent,1=Low<33%,2=Med33-67%;3=High>67%;
   Quarters: note P/A" legend line
6. "* Other species:" free-text entry (key_value, right after table 7)

## Header metadata — both forms

| Field | Form 1 (M13) | Form 2 (L13) |
|---|---|---|
| Grid no | M13 | L13 |
| Date | "29thpn!" -> guessed **29th Apr (?)**, flagged | "29tapnl" -> same guess, flagged |
| Observer | "8K,S,PS." -> **SK, S, PS (?)**, flagged (8->S OCR) | "SK.S,PS" -> clean enough, not flagged |
| Grid Centroid GPS | "1.31305 76.83210" -> **10.31305 76.83210 (?)**, flagged (leading "10" likely dropped, by analogy with Form 2's "10.31309 76.83302") | 10.31309 76.83302 (clean, conf 89.8) |
| Altitude | (blank, both forms — "1) Altitude:" key_value empty) | (blank) |
| Slope (clinometer) | 15 (clean, conf 94.1) | "RO" -> **20 (?)**, flagged (R~2, O~0 OCR garble) |
| Canopy density | printed legend "Open(<5%)/Sparse/Moderate/High"; quadrant grid all S (Sparse) | same legend; quadrant grid ~S (Sparse?), flagged — cursive handwriting reads more like "5" |
| Canopy composition | printed legend "Mostly Exotic/Mixed/Mostly Native"; quadrant grid NW=2(?)/N/N/N | same legend; quadrant grid all ~M (Mixed?), flagged — cursive |
| Disturbance | "Grazing/Firewood/Lopping/Girdling/Tree Cutting/" + handwritten "metal wiresd, lines." -> guessed **"metal wires(?), snares(?)"**, flagged | **not captured by Textract at all** — flagged as a possible gap (see "Open question" below) |

## The two marginal quadrant grids — the core new-structure test

Both "CAN DENSITY" and "4) CAN. COMP" are drawn as a 2x2 grid in the
left margin, with "N" written above and "S" below (compass
orientation), i.e. the grid represents the 4 quadrants of the 100x100m
plot as seen from above. Textract's `v1.tables` contains **none of
this** — it only shows up as scattered single-character `other_text`
(`S`, `5`, `N`, `2`, `M`, `IV`, `MM/`, etc.) near the left margin,
plus the two text labels "CAN DENSITY" and "4) CAN Comp"/"CAN. COMP".

- **Form 1 CAN DENSITY** (`crop_topleft.png`): all 4 quadrants read as
  **"S"** (Sparse). Fairly legible, but flagged since it's hand-drawn.
- **Form 1 CAN. COMP** (`crop_cancomp.png`): NW="2", NE="N", SW="N",
  SE="N". The "2" doesn't map cleanly onto the printed
  "Exotic/Mixed/Native" legend (no obvious "2" option) — flagged as
  the most uncertain single cell on the page.
- **Form 2 CAN DENSITY** (`crop_bottom_candensity.png`): same 2x2
  layout, but the handwriting is more cursive/looping — read as **"S"**
  again by visual similarity to Form 1, but Textract's own `other_text`
  read these same marks as `"55"`/`"55"`/`"5"`, i.e. it's genuinely
  ambiguous between "S" (Sparse) and "5". Flagged.
- **Form 2 CAN. COMP** (`crop_bottom_cancomp.png`): same 2x2 layout,
  cursive — read as **"M"** (Mixed?) across all 4 quadrants, by
  contrast with Form 1's "N"-dominated grid. Flagged; Textract's
  `other_text` read fragments as `IV`/`MM/`/`M`/`It` — also consistent
  with "M" but very low confidence (as low as 23.3).

This is the **4th distinct variant of "structure missing from
v1.tables"** seen across the 5 PDFs (after PDF2's clean 2-col grid,
PDF3's mis-keyed numbered lists, PDF4's "none"): here it's **two small
spatial (2x2 quadrant) grids per form**, each requiring (a) recognizing
the "N over S" compass framing from a crop, and (b) reading 4 short
handwritten single-char/word cells per grid.

## Main tables — pass-through with flags on anomalies

Both "6) Alien trees" tables (6x7, 5 data rows) and both "7) Alien
plant prevalence" tables (11x7/12x7, ~10 data rows) are **transcribed
essentially as Textract read them** (checkbox cells as `[X]`/`[ ]`/`X`/
empty), per the same "dense grid, minimal correction" approach as
PDF4. Cells flagged as anomalous (don't fit the `[X]`/`[ ]`/`X`/empty
checkbox pattern):

- Form 1, table 6, row "Silver oak", Quarter4: `"Y [X]"` — stray "Y"
  prefix on a checkbox.
- Form 1, table 7, row "Lantana", Quarter3: `"y [X]"`.
- Form 1, table 7, row "Wedelia": Quarter2=`"Y"` (no brackets),
  Quarter4=`"X"` (no brackets) — inconsistent with the bracketed `[X]`
  convention elsewhere.
- Form 1, table 7, row "Montanoa": Quarter1=`"7"`, Quarter2=`"X"`,
  Quarter3=`"x"` — `"7"` is likely an OCR misread of a checkbox mark.
- Form 2, table 6, row "Spathodea", Quarter1: `"&"`.
- Form 2, table 6, row "Eucalyptus", Quarter4: `"[X] r"` — stray "r"
  suffix.
- Form 2, table 7, row "Lantona", Quarter3: `"[X] A"` — stray "A"
  suffix.
- Form 2, table 7, row "Wedelia": Cover=`"Httigh"` -> guessed
  **"High (?)"**.
- Form 2, table 7, row "Montanaa": Quarter3=`"X"`, Quarter4=`"X"`
  (no brackets, like Form 1's Wedelia row).
- Form 2, table 7, row "Polygonum": Cover=`"how"` -> guessed
  **"low (?)"**.
- Form 2, table 7, last row (r12, conf 34.9 across all cells) —
  **dropped** as a page-edge scan artifact, not a real data row
  (analogous to PDF3's binder-clip noise).

## "Other species" entries (between the two tables on each form)

- Form 1, after table 6: `"Other species: Coffee"` (key_value, conf
  94.7) — clean.
- Form 1, after table 7: `"Other species:"` blank (key_value, conf
  88.2) — not filled in.
- Form 2, after table 6: `"Other species: coffee."` (key_value, conf
  94.0) — clean, lowercase variant of Form 1's.
- Form 2, after table 7: `"Other species:"` blank (key_value, conf
  90.9) — not filled in.

## Open question for codex: Form 2's missing "5) Disturbance"

Form 1 has a clear "5) Disturbance: Grazing/Firewood/.../Tree Cutting/
metal wiresd, lines." entry (`other_text`, conf 88.7) between "4) Canopy
composition" (y=0.141) and the alien-trees table (y starts 0.183).

Form 2's equivalent vertical gap is y=0.596 ("4) Canopy composition")
to y=0.636 (table2 starts) — **no key_value or other_text falls in this
band** for "5) Disturbance". Two possibilities: (a) Form 2's
Disturbance field was left blank by the surveyor, or (b) Textract
missed it (the band is narrower than Form 1's, ~0.04 vs ~0.03 — actually
similar size, so (a) seems more likely, but not crop-verified). Golden
leaves this **blank + flagged** as a genuine open question — a good test
of whether codex crops this region and finds something Textract missed.

## Notes / what this PDF stress-tests

- **Two complete, near-identical form-sheets on one page** — does
  codex keep them as two cleanly-separated sections (matching the two
  `Grid no:` / `Data sheet for 100 x 100 m grid` headers), or does it
  merge/confuse rows from the two forms?
- **Marginal 2x2 quadrant grids (CAN DENSITY / CAN. COMP)** — a 4th
  variant of "structure missing from v1.tables", and the first one
  requiring spatial (not just list) reconstruction from a crop.
- **Repeated checkbox-table pattern** — same 6x7/11x7 column layouts
  used twice; tests whether codex's per-cell transcription is
  consistent across the two repeats (e.g. does it normalize `"Y [X]"` /
  `"[X] r"` / `"[X] A"` the same way both times, or treat each
  occurrence independently).
- **Form 2's possibly-missing "Disturbance" field** — a genuine "did
  Textract miss something, or is it actually blank" question that only
  a targeted crop can resolve.
