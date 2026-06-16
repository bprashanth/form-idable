# Compare — codex output.xlsx vs golden.xlsx (LeafLitterBiomass.pdf, page 1)

**Result: strong match, including the two hardest structural recoveries.**
78,131 tokens (vs 48,292 for PDF1 — the extra crops for the missing
Remarks column and the bottom "Dry weight" section roughly doubled cost).

## Header metadata — both merges solved independently

Codex independently resolved **both** of the split key_value/other_text
merges identified in the golden:
- `Avg Cloth Bag Wt` → `56.172 g` ✓ (golden flagged this merge yellow;
  codex did it without flagging — apparently confident from a crop)
- `Avg Packet Wt. (10 covers)` → `3.747 g` ✓ (same)

All other metadata fields (dates, location, collectors, note) match
exactly.

## Main table (25 rows) — including the column Textract's table missed

- Codex reconstructed the full 9-column table **with the "Remarks"
  column**, which `v1.tables[0]` did not capture at all (it only had 8
  cols). It got there via its own crops (`crop_table.png`,
  `rot_crop_table.png`, `crop_remarks.png`).
- Found and transcribed the 3-line handwritten remark "Note = Take avg
  wt. of Dry cloth bags as well." on row C21/33 — golden placed this same
  note on C19, codex on C21. **Both found and correctly transcribed the
  note text; the exact row attachment differs by ~2 rows** (a fuzzy
  multi-row handwritten note spanning the table's right margin — minor).
- Trap IDs normalized to C1-C25, matching golden exactly.
- Data values match golden cell-for-cell (Leaf/Twig/Flower/Fruit/Seed),
  including the `*`/annotation cells (`0.05*`, `0.14*`, `0.08*`, `0.07*`,
  `0.19*`, `0.13*`, `0.20*`) — codex normalized `0.19A`→`0.19*` (golden
  kept `0.19A`), a trivial notation choice.
- **Fresh/Dry column**: codex read `C1` = `F` (golden left this column
  blank entirely, treating the stray Textract marks as noise). Codex's
  `F` is a sensible interpretation of the column header ("Fresh/Dry")
  and is arguably *better* than golden here — it's a real reading, not
  noise.
- Minor placement quirk: codex put the general footnote `"* = w/o
  cover"` into row C1's Remarks cell, whereas golden kept it as a
  page-level header note. Doesn't lose information, just a different
  home for a global annotation.

## New "Dry weight measurements" section — fully recovered

Codex added exactly the section golden built by hand: `Trap | Packet wt
(g) | Cloth wt (g)`, traps 1-10, **and correctly wrote `v2_meta.json`**
(`new_sections: [{sheet: "v2", rows: [44,55], bbox: [0.04,0.84,0.98,0.99]}]`)
per the system prompt's step-4 convention.

- Packet wt column: matches golden exactly for traps 2-10. Trap 1:
  codex got `3.64` (same as golden) and **flagged it yellow** for the
  same reason golden did (nearby crossed-out correction mark,
  `'2364'`/`'1.3.64'` ambiguity in `other_text`) — independent agreement
  on both the value and the uncertainty.
- Cloth wt column: matches golden exactly for traps 1-5, 7-10. **Trap 6
  differs**: codex read `52.65` (not flagged) vs golden's `59.65` (which
  golden itself flagged orange as low-confidence, raw Textract
  `'59.65.9'` at conf 55.4). Codex's crop-based reading at `52.65` fits
  the overall value range (51-59, except trap2's 65.87) at least as well
  as golden's guess — **this is a case where codex's crop access likely
  beat both Textract and the golden's guess**, though without ground
  truth from the physical sheet we can't be 100% sure.

## Takeaway for scope/descope

- This was the hardest of the 5 PDFs by design (missing table column +
  entirely off-table handwritten section, rotated text, interleaved
  noise markers) — codex+Textract+crops **fully recovered both
  structural gaps** and even out-performed the golden on one ambiguous
  cell (trap 6 cloth wt).
- The only "miss" is a ~2-row attachment-point error for a multi-line
  handwritten remark — cosmetic, the text itself was captured correctly.
- **No prompt/tooling gaps found here.** This is good evidence that the
  current `system_prompt_crops.md` + `render_page.py` + `v1.json`
  combination already handles "Textract missed a whole column" and
  "Textract scattered a whole section into ungrouped other_text" — the
  two failure modes we were most worried about going into this
  experiment.
- Cost note: 78K tokens for this PDF vs 48K for PDF1 — structural
  recovery work (extra crops, rotated-text reading) roughly doubles
  token spend. Worth keeping in mind for the final scope/descope summary
  if cost becomes a constraint (e.g. should "recover off-table sections"
  be a separate, optional pass?).
