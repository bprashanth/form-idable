# Golden reference — LeafLitterBiomass.pdf, page 1

Built by: rendering `v1_overview.png` (zoom 2), `crop_bottom.png` (bbox
0.0,0.85,1.0,1.0, zoom 3) and `crop_remarks.png` (bbox 0.75,0.6,1.0,0.75,
zoom 6), cross-checked against `v1.json`'s table (31x9), key_values (9),
and other_text (27 entries).

## Structure (3 sections)

1. Header metadata (from `v1.json` key_values, with 2 corrections — see
   below):
   - Date of Collection: 24/10/25
   - Date of Fresh Measurement: 24/10/25
   - Date of Dry Measurement: 26/10/25
   - Location: Candura
   - Data collectors: Khushi, Shiva, Navin
   - Avg Cloth Bag Wt: 56.172 g
   - Avg Packet Wt. (10 covers): 3.747 g
   - Note: * = w/o cover

2. "Fresh weight measurements" table (Textract table[0], 31x9 incl. 5
   trailing empty rows → 25 data rows, C1-C25). Header:
   `Trap ID, Fresh/Dry, Leaf, Twig, Flower, Fruit, Seed, Other, Remarks`.
   **The "Remarks" column is column 9 — Textract's table only captured 8
   columns (cols 0-8, col 0 always empty), so Remarks is entirely
   missing from `v1.tables`.** It is visible in `v1_overview.png` as the
   rightmost column of the ruled table, and one entry in it (rows
   ~19-21) contains a 3-line handwritten note: "Note = Take avg wt. of
   Dry cloth bags as well." — this note is **not present anywhere in
   `v1.json`** (not in tables, not in other_text). The section label
   "Fresh weight measurements" is **inferred** (no literal title text
   exists on the page for this table).

3. "Dry weight measurements (per-trap, traps 1-10)" — a section that
   exists **only as 22 loose handwritten `other_text` entries** near the
   bottom of the page (y≈0.89-0.91), not in any `v1.tables` entry. Two
   columns of 10 values each (traps 1-10, read off as `"<trap>.<value>"`,
   e.g. `"10.4.18"` = trap 10, value `4.18`), each column terminated by a
   row-label (`"Packet"` / `"cloth"`). Reconstructed as:
   `Trap | Packet wt (g) | Cloth wt (g)`, traps 1-10.

## Corrections made vs raw Textract

- `key_values['Avg Cloth Bag Wt:']` = `'g'` (number missing) — the
  number `'56.172'` is a separate `other_text` entry (x=0.629, y=0.116,
  conf 96.6) right next to it. Merged into `"Avg Cloth Bag Wt: 56.172 g"`
  — **yellow-flagged** (merge across two Textract entities, not
  verified against the image at high zoom).
- `key_values['Avg Packet Wt. (10 covers): g']` = `''` (empty) and a
  separate, oddly-named `key_values['Packet-']` = `'3.747'` — these are
  almost certainly the same field (Textract mis-grouped the key/value
  split). Merged into `"Avg Packet Wt. (10 covers): 3.747 g"` —
  **yellow-flagged** for the same reason as above.
- Trap IDs normalized: Textract read several as `'CI'`, `'06'`, `'07'`,
  `'C 8'`, `'C 9'`, `'C 10'`...`'C 16'`, `'( 17'`, `'C24 C 24'`,
  `'C5 C 5'` — all normalized to `C1`...`C25` (sequential, unambiguous
  from row order).
- "Fresh/Dry" column: Textract read stray marks (`'T'`, `'4'`, `'.'`,
  `'1'`) on rows C1, C10, C24, C25 and nothing on the other 21 rows —
  these are illegible checkmark-like marks, left blank in the golden
  (not transcribed as values).
- A handful of single-cell OCR garbles in the data columns were
  normalized to `0` and **yellow-flagged**: C6 Flower (`'D'`→`0`), C8
  Seed (`'D i'`→`0`), C11 Flower (`'U'`→`0`), C19 Fruit (`'B'`→`0`).
  `*`/`A` suffix annotations (e.g. `0.05*`, `0.19A`) were preserved
  as-is — these look like real notation, not OCR noise.
- New "Dry weight measurements" section (item 3 above): trap 1's Packet
  value is ambiguous — `other_text` has both `'2364'` (conf 82.5) and
  `'1.3.64'` (conf 91.3) at nearly the same position; took `1.3.64` →
  `3.64` and treated `'2364'` as a stray scribble/correction mark.
  Trap 6's Cloth value (`'59.65.9'`, conf only 55.4) doesn't fit the
  `"<trap>.<value>"` pattern as cleanly as the rest — took it as `59.65`.
  Both **flagged orange** (extra-uncertain, on top of the whole
  section's yellow flag) in `golden.xlsx`.

## Notes / what this PDF stress-tests

- Unlike PDF1 (GrowthSurvivalMonitoring), where Textract's table
  detection was essentially complete, here **Textract's table is
  missing an entire column** (Remarks) that is clearly visible as a
  ruled column in `v1_overview.png`. An agent relying on `v1.tables`
  alone (without looking at the overview/crops) would silently drop the
  Remarks column and its 3-line handwritten note entirely.
- The "Dry weight measurements" section is the same *class* of problem
  as TreePlots' borderless ground-cover grid and PDF1's empty "6 month
  later survival" section: **structure that exists only as scattered
  `other_text` with no ruled lines**. Here it's especially hard because
  the text is rotated ~90° and the two value-columns are interleaved
  with stray scribbles (the `'1'` and `'2364'` noise entries) — a good
  test of whether the agent groups by bbox correctly and ignores noise
  per the "ignore stray entries" rule in `system_prompt.md`.
- `v2_meta.json` records section 3 as a `new_sections` entry, matching
  the convention in `system_prompt.md` step 4.
