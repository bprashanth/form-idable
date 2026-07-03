# Compare — codex output.xlsx vs golden.xlsx (GridVegetation100mx100m.pdf, page 1)

**Result: strong structural match on the hardest test.** 89,655 tokens
(highest of the 5 PDFs — two full forms, 8 crops, 4 new quadrant-grid
sections). Same 92-row layout, both forms cleanly separated, all 4
CAN DENSITY/CAN. COMP grids independently recovered as `v2_meta.json`
new sections with matching bboxes.

## Two-form separation — correct, identical

Codex wrote "Data sheet for 100 x 100 m grid -- Form 1 (Grid M13)"
and "-- Form 2 (Grid L13)" as title rows, matching golden's explicit
separator approach. The section row numbers for both tables (6 and 7),
both "Other species" entries, and both quadrant grids all land on the
same row numbers as golden (92-row output with same skeleton). **There
was no form-bleeding or row-interleaving** — the hardest aspect of this
stress test (keeping two near-identical stacked forms cleanly separated)
was handled without difficulty.

## Canopy quadrant grids (the core new-structure test) — 4/4 recovered

Both golden and codex independently produced a 2x2 West/East ×
North/South grid for each form's CAN DENSITY and CAN. COMP sections,
and `v2_meta.json` contains all four with accurate bboxes:

| Grid | Golden reading | Codex reading |
|---|---|---|
| CAN DENSITY M13 | S,S,S,S (all flagged) | S,S,S,S (all flagged) |
| CAN. COMP M13 | **NW=2(?)\***, NE=N\*, SW=N\*, SE=N\* | NW=N\*, NE=N\*, SW=N\*, SE=N\* |
| CAN DENSITY L13 | S(?),S(?),S(?),S(?) (all flagged) | S(?),S(?),S(?),S(?) (all flagged) |
| CAN. COMP L13 | M(?),M(?),M(?),M(?) (all flagged) | M(?),M(?),M(?),M(?) (all flagged) |

The only divergence is **CAN. COMP M13 NW quadrant**: golden (from
`crop_cancomp.png`, zoom 8) read it as `"2"` (numerically ambiguous);
codex (from `crop_left_grids.png`, a taller strip covering all four
margin grids at once, zoom 8) read it as `"N"`. Both flagged yellow.
Given the cursive mark, either is plausible — and in fact codex's
whole-strip crop likely gave a better read of relative letter heights
across the grid, making its `"N"` possibly more accurate. Both surface
the uncertainty correctly.

## OCR garble normalization — codex more aggressive than golden

Across both forms, codex fixed a set of garbled Cover/checkbox values
that golden left as literal Textract reads (flagged or passed through):

| Cell | Golden | Codex | Assessment |
|---|---|---|---|
| Table 7-M13, Mikania Cover | "lm" | "low" | Codex correct |
| Table 7-M13, Gliricidia Cover | "100" | "low" | Codex correct |
| Table 7-M13, Pohyjorum Cover/species | "lon"/"Pohyjorum" | "low"/"Polygonum" | Codex correct on both |
| Table 7-L13, Wedelia Cover | "Httigh (?)*" (flagged) | "High" (not flagged) | Codex correct, golden over-flagged |
| Table 7-L13, Polygonum Cover | "how (?)*" (flagged) | "low" (not flagged) | Codex correct, golden over-flagged |

This is the strongest normalization performance of the 5 PDFs —
codex correctly resolved all 5 garbled Cover values to their intended
1-3 scale words, without any of them appearing in golden correctly. The
pattern ("lm", "lon", "Httigh", "how", "100") is entirely OCR noise on
the same word "low" / "high" written in similar cursive. Codex's crop
context likely helped confirm these.

## Checkbox normalization — stylistic divergence

Codex replaced Textract's `[X]` bracket-checkbox notation with "X" or
"tick" and treated `[ ]` (empty checkbox) as a blank cell. Golden kept
Textract's notation literally (`[X]`/`[ ]`/`X`/empty).

- `[X]` → "X" or "tick" (inconsistently across codex's output, not
  distinguishable by pattern — probably just which part of the crop
  codex read each cell from)
- `[ ]` → blank cell (codex omits the "Comments / notes" column's `[ ]`
  entries entirely)
- "Y [X]", "[X] r", "[X] A", "&", "7" → plain "X" or "tick" (all
  resolved without flagging)

The last row is the key difference from golden: golden flagged all
these anomalous-notation cells as uncertain (`Y [X]`, `&`, `[X] r`,
`7`, `x`); codex silently normalized them all to "X"/"tick". Codex's
output is cleaner, but loses the signal that these cells had irregular
handwriting near the checkbox — potentially relevant if a reviewer was
trying to decide which cells to look at carefully.

**One concrete case where the pass-through wins**: `"[X] A"` on L13,
Lantana, Quarter3. The "A" may be a meaningful annotation (a note
about the quarter?), not just OCR noise. Codex discarded it; golden
preserved and flagged it. The pass-through flagged approach is safer
for these edge cases.

## Bottom disturbance field — confirmed blank by crop

Codex rendered `crop_bottom_disturbance.png` (bbox 0.11-0.90, y=0.595-
0.635, zoom 8) and confirmed the "5) Disturbance" row is genuinely
blank for Form 2 (not a Textract gap). This resolves the open question
from golden.md: the field was simply not filled in by the surveyor for
the L13 form. Codex's crop verified what golden couldn't determine from
`v1.json` alone — **a concrete example of the crop tool adding value
even for "probably blank" fields**.

## Bottom form, Maesopsis Quarter1 — minor disagreement

Table 6 (L13), Maesopsis row, Quarter1:
- Golden: blank (Textract table2[r3,c3] = `""`, conf 82.4)
- Codex: "tick" (marked as present)

Textract's read was empty (no checkbox found), but codex's crop of
the bottom tables region (`crop_bottom_tables.png`) appears to have
found a checkbox mark there. Could be a genuine checkbox that Textract
missed, or OCR noise from the adjacent cells. Left as an unresolved
discrepancy.

## Token and crop count — scales well

89,655 tokens vs. PDF4's 57,166 (the previous high). The increase
comes from 8 new crops rendered (vs. PDF4's 3-crop run), the longer
two-form page structure, and the quadrant-grid reading work. Still
well within a single, uncapped run — no truncation.

## Takeaways for scope/descope

- **Two-form structure handled cleanly**: no prompt change needed to
  handle multiple complete form-sheets on one page. The agent
  naturally scanned the full page, identified both `"Data sheet for
  100 x 100 m grid"` headers, and kept them separate.
- **Quadrant grids recovered without any special prompt guidance**:
  the CAN DENSITY / CAN. COMP marginal grids are a genuinely novel
  structure (not described in the system prompt) and codex found all
  four, built a West/East × North/South grid, and wrote `v2_meta.json`
  entries — just from the crop and reasoning about compass labels.
  No prompt addition needed.
- **Checkbox notation → normalize to plain mark or blank**: codex's
  implicit normalization (`[X]`→"X", `[ ]`→blank) is probably the
  right default for these forms, but the anomalous annotations like
  `"[X] A"` (stray note next to a checkbox) and `"Y [X]"` (stray
  character + checkbox) should arguably be preserved and flagged
  rather than silently dropped. A small prompt addition like "if a
  checkbox cell contains extra characters beyond `[X]` or `[ ]`,
  flag the cell and include the extra characters" would catch these.
- **Cover garble normalization as a `textract_minimize.py` candidate**:
  "lm", "lon", "Httigh", "how", "100" → "low"/"high" are all OCR
  garbles of the same 1-3 cover words on a form with a printed legend.
  A preprocessing step identifying the expected value set from the
  legend text (already in `other_text` as "Cover: 0=Absent,1=Low
  <33%,2=Med 33-67%;3=High>67%") and normalizing near-misses in the
  Cover column would save the agent's crop budget on a pattern that's
  purely an OCR artifact. Same class of fix as the PDF4 "Fallen
  column is Y/N" suggestion.
