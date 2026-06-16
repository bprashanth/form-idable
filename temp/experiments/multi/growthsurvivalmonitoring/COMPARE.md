# Compare — codex output.xlsx vs golden.xlsx (GrowthSurvivalMonitoring.pdf, page 1)

**Result: very close match.** 48,292 tokens. Codex independently made the
same two non-trivial OCR corrections as the golden, and flagged the same
single uncertain cell (with a different but equally-flagged guess).

## Data table (16 rows x 13 cols)

- **Identical** cell-for-cell except trivial `1` vs `1.0` formatting
  (A06/A12 Basal_Dia cols) and one cell:
- **A02 Shoot_L #2** (Textract raw: `"J"`): golden left it as `J*`
  (yellow, "couldn't confirm"); codex changed it to `-*` (yellow,
  "handwritten dash that Textract misread"). **Both flagged this cell as
  uncertain** — different guesses, same conclusion that it needs human
  review. Good outcome either way.
- **A11 Basal_Dia_1 #2** (Textract raw: `"a.t"`): both golden and codex
  independently corrected to `0.7`. ✓
- **A16 Basal_Dia_2 #2** (Textract raw: `"111"`): both golden and codex
  independently corrected to `1.1`. ✓
- Header row: identical column reconstruction (`Basal_Dia_1 (cm) #1/#2`,
  etc.) — codex split the paired-measurement headers correctly without
  being told the exact convention, just from `v1.json` table[1]'s
  layout.

## Header metadata / title / "6 month later survival"

- Both preserve the title "Growth and Survival Monitoring Datasheet" and
  all 4 metadata fields (Grid ID, Starting date, Ending date, Observers).
  Codex also added a "Page 1" row from `other_text` (golden omitted it —
  harmless either way).
- **Observers spelling**: golden guessed "Rajeshi Sivdas, Nanda, Arun,
  Sundar"; codex guessed "Rajesh, Sivdas, Nandu, Arun, Sundar" — both
  flagged yellow as uncertain. Same conclusion, different guesses (as
  expected for illegible handwriting).
- **"6 month later survival" section** (table[0] col3, header-only, no
  data on this page): golden made this an explicit second
  section/footer with a "(no data recorded on this page for this
  section)" note. Codex instead kept Textract's table[0] literally — the
  label sits in the same row as "Grid ID"/"Annual growth" (row 4, col 3),
  with nothing below it. **Codex did not fabricate a fake empty table,
  but also didn't make the "this is a separate section with no data
  here" reading as explicit as the golden.** Both are defensible; golden
  is slightly more reviewer-friendly.

## Takeaway for scope/descope

- On a clean, well-ruled table (Textract table detection worked well),
  codex+Textract+crops converges to essentially the golden, including
  catching 2 genuine OCR errors via crops and correctly flagging the one
  genuinely ambiguous cell. **No prompt/tooling changes needed for this
  case.**
- The one soft gap: a Textract table that has a "title-only" cell
  pointing at a section with no data on this page (e.g.
  "6 month later survival") isn't surfaced as explicitly as it could be.
  Minor — not worth a prompt change on its own, but worth watching across
  the other 4 PDFs to see if it recurs (e.g. GridVegetation's two
  form-sheets, PDF 5).
