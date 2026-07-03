# Golden reference — GrowthSurvivalMonitoring.pdf, page 1

Built by: rendering `v1_overview.png` (zoom 2) + several targeted crops
(`crop_table.png`, `crop_rows11_16.png`, `crop_row17.png`, `crop_remarks.png`)
at zoom 4-8, cross-checked against Textract's `v1.json` table (table[1],
17x13).

## Structure (5 sections)

1. Title: "Growth and Survival Monitoring Datasheet"
2. Header metadata (from Textract table[0], 4x3 — col1=labels, col2=values,
   col3 mostly empty):
   - Grid ID: I13
   - Starting date: 15-09-2025
   - Ending date: 17-09-2025
   - Observers: Rajeshi Sivdas, Nanda, Arun, Sundar (handwritten names —
     best-guess spellings, low confidence)
3. Section label "Annual growth" (this is the title of the main data table —
   it appears as a header cell in table[0] col2 row1)
4. Main data table (Textract table[1], 17 rows incl. header x 13 cols).
   **The header row is split across columns** (e.g. "Basal_Dia_2" and "(cm)"
   land in separate cells) because each measurement has 2 reading columns —
   reconstructed as `<Measurement> (cm) #1` / `#2` for Basal_Dia_1,
   Basal_Dia_2, Shoot_L, Crown_Dia. 16 data rows (S.no 1-16, T_no A01-A16).
5. Section label "6 month later survival" (table[0] col3 row1) — this is the
   title of a *second* data table that does **not appear on this page**
   (col3 is empty for all 4 rows of table[0]). Likely lives on a later page
   of the 3-page PDF. Flagged — on a single-page run this section has no
   data to show.

## Corrections made vs raw Textract table[1]

- Row 11 (A11, Syzygium densiflorum), col5 (Basal_Dia_1 #2): Textract read
  `"a.t"` — visually this is `0.7` (confirmed via `crop_rows11_16.png`).
- Row 16 (A16, Palaquium ravii), col7 (Basal_Dia_2 #2): Textract read `"111"`
  — visually this is `1.1` (a middle-dot `1·1` misread as three `1`s,
  confirmed via `crop_row17.png`).
- Row 2 (A02, Dimocarpus longan), col9 (Shoot_L #2): Textract read `"J"`.
  Could not get a clean enough crop to confirm — left as-is and
  **yellow-flagged** (I11 in golden.xlsx) as genuinely uncertain.

## Notes

- This is a clean, well-ruled landscape table — Textract's table detection
  worked well here (unlike TreePlots' borderless ground-cover grid). The
  main risk for the agent is **not** missing structure, it's (a) correctly
  splitting the 2-reading-per-measurement header, and (b) the "6 month later
  survival" section-without-a-table being either fabricated or silently
  dropped.
- "NA"/"-" entries (rows 2, 8, 14, 15) are real recorded values (tree died /
  not measured), not missing data — should be transcribed as literal `NA`
  and `-`, not left blank.
