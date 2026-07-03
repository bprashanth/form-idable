# Compare — codex output.xlsx vs golden.xlsx (RegenerationPlot5mx5m.pdf, page 1)

**Result: strong structural match.** 48,330 tokens (same ballpark as
PDF1's clean table — this page is short, only 4 filled data rows).

## Header metadata

- Date, Data collectors, Type/Year restored (blank), GPS point all match.
- Site: codex read "Condura A01" vs golden's "Condure Aol" — same
  ambiguous handwriting, both flagged yellow. Same conclusion, different
  guess (as expected).
- **Canopy densitometer checkbox**: codex read the checkmark as marking
  "open"; golden guessed "closed". The checkmark sits ambiguously between
  the words "closed/open" in the source — **genuine disagreement on an
  ambiguous mark, and both flagged it yellow.** This is exactly the kind
  of cell a human reviewer needs to resolve.

## Main table — tally marks (the focus of this PDF)

| S No | Species | Seedlings | Saplings |
|---|---|---|---|
| 1 | both flagged, similar guess ("Vdct Mdl" / "Vdet mdl") | **1 = 1**, both agree, neither flagged | **4 = 4**, both agree, neither flagged |
| 2 | both flagged, similar guess ("Ficus exas" / "Ficus exims") | golden guessed `5*` (bundled-tally read); codex wrote `"symbol/mark*"` — **did not commit to a count** | **1 = 1**, agree |
| 3 | "Lantana" — exact match, neither flagged | empty, agree | **1 = 1**, agree |
| 4 | both flagged, similar guess ("Xanthus flav" / "Xanthus flow") | empty, agree | **1 = 1**, agree |

- **3 of 4 tally marks (the unambiguous single-stroke ones) were read
  identically and correctly by both** — codex handles standard tally
  notation fine.
- **The one ambiguous "bundled" tally mark (row 2 Seedlings, the
  "$"-like symbol)**: golden committed to a best-guess count (`5`,
  flagged); codex instead wrote a non-numeric placeholder (`"symbol/mark"`,
  flagged) and explicitly called this out in its summary as "not a clear
  tally/dot/blank-line notation." **This is a real scope question**: the
  production prompt says "tally marks... are a count — sum them to an
  integer." Codex's behavior here (refuse to count when the mark doesn't
  match the documented tally patterns, flag instead) may be *more*
  correct than forcing a number — but it means the cell is left
  non-numeric rather than blank-and-flagged. Worth a small prompt
  clarification: when a mark looks tally-like but doesn't fit `I`/`II`/
  `III` etc., leave the cell **blank** (not a text description) and flag
  it, so downstream spreadsheet consumers don't choke on a string in a
  numeric column.

## Bottom species-list sections — both recovered, with v2_meta.json

Codex correctly identified both off-table sections and wrote
`v2_meta.json` with matching bboxes:
- "Canopy above SAT" — `1) Spathodea` (exact match with golden). For
  item 2, codex captured **more detail** than golden: `"Arotexylon
  (crossed out); Tetramilis"` vs golden's `"[species crossed out]
  Tetramilis"` — codex actually read the crossed-out genus name, golden
  didn't attempt it. Both flagged.
- "Other species" — codex: `Pely gomms / grany / Chrohostum / Brackers`
  vs golden: `Polygonum(?) / ?(illegible) / Chrisholum(?) / Brackens(?)`.
  Both are best-effort guesses at the same illegible handwriting, both
  flagged on every cell. Item 4 (`Brackers`/`Brackens`) essentially
  agrees.

## One real miss: the binder-clip / stray-mark artifact

Codex added a row `"Top-left note: Done"` (flagged) for the black
binder-clip + stray handwritten initial in the page's top-left corner.
Golden explicitly classifies this as **noise to ignore** per
`system_prompt.md`'s "ignore stray entries that don't fit any group"
rule — it's a scanning artifact, not form data. Codex included it
anyway (flagged, so a reviewer would see it's odd, but it's still a
spurious row in the output).

## Takeaway for scope/descope

- Codex+Textract+crops again recovers all the *structure* correctly
  (table, both off-table species lists, `v2_meta.json`), and handles
  standard tally marks correctly.
- Two small, concrete prompt refinements suggested by this PDF:
  1. For tally-like marks that don't cleanly parse as `I`/`II`/`III`/
     etc., the prompt should say "leave blank + flag" rather than
     allowing a free-text placeholder in what should be a numeric cell.
  2. The "ignore stray marks/artifacts (binder clips, stray initials,
     scan debris)" guidance could be more explicit — right now codex
     errs on the side of including everything (flagged), which is safe
     but adds clutter for genuinely irrelevant scan artifacts.
