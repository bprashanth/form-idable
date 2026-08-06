# GOLDEN_NOTES — eval_02

## What this form is

A three-page, landscape-orientation **"Growth and Survival Monitoring Datasheet"**
from a tree-restoration monitoring plot (Grid ID I13, surveyed 15–17 Sep 2025).
Page 1 carries a small metadata block (grid ID, start/end date, observers) plus
the first block of the tree table; pages 2 and 3 continue the same table under a
repeated printed header. Each row is one tagged sapling (`T_no` A01–A39, then
B01–B21; `S.no` 1–60 with no gaps) and records four measurements plus a
survival code (A/B/Dr/D) and free-text remarks.

The structurally important feature: **every measurement column is split into two
sub-columns** — a machine-printed *prior* value (the previous survey's
measurement, pre-printed onto the form) and a *handwritten* new value written by
the field crew alongside it. The metadata block labels these two passes
"Annual growth" (the handwritten column, filled in) and "6 month later survival"
(a second pass column that is **blank throughout this form**). The golden keeps
both values per column, in reading order: printed first, handwritten second.

## Golden layout

Sheets `page1`, `page2`, `page3`. Data table is 13 columns:

```
S.no | T_no | Species | Basal_Dia_1 printed | Basal_Dia_1 handwritten
                      | Basal_Dia_2 printed | Basal_Dia_2 handwritten
                      | Shoot_L printed     | Shoot_L handwritten
                      | Crown_Dia printed   | Crown_Dia handwritten
                      | Survival (A/B/Dr/D) | Remarks
```

The printed header row spans each measurement pair with a single merged label,
so the header row carries the label in the first sub-column and an empty cell in
the second — that is what is actually printed on the page.

Row counts: page1 = 16 data rows (S.no 1–16), page2 = 22 (17–38),
page3 = 22 (39–60). Total 60. Sequence verified contiguous 1–60; T_no verified
A01–A39 then B01–B21.

## Notation decisions applied

- **Handwritten dash = no entry.** Many rows have a printed value (or printed
  `NA`) with a hand-drawn strike-through dash in the adjacent handwritten
  sub-column, meaning "nothing recorded this pass". Per spec those handwritten
  cells are left **empty**; the printed value (including a printed `NA`) is
  retained. Affected rows: 2, 8, 14, 15, 17, 36, 37, 42, 44, 46, 50 (all four
  measurement pairs), and row 56 (Crown_Dia handwritten only).
- **Decimal points** are written by the crew as a raised mid-dot (`1·5`).
  Transcribed as `1.5`.
- **Handwritten `1.0`, `0.9` etc. keep the trailing digit** as written; printed
  values keep their printed form (e.g. printed `1` stays `1`, not `1.0`). All
  measurement cells are stored as text so trailing zeros survive.
- **Circled S.no**: rows 11, 13 (page 1) and 26 (page 2) have their serial number
  circled by hand. Circle dropped, value transcribed (per spec).

## Converter-disagreement adjudications

Converters: `gemini-3.6-flash` (G), `qwen3-vl-32b` (Q), `codex CLI` (C).

| Cell | Candidates | Decision | Why |
|---|---|---|---|
| Header, Observers | G/C: `Rajesh, Sivdas, Nandu, Arun, Sundar` — Q: `Rajesh, Sivagiri, Nandu, Arun, Sundeep` | **Rajesh, Sivdas, Nandu, Arun, Sundar** | Cropped the observer line at max native zoom (~3 px/pt scan) and enlarged each name. Name 2 is six letters `S-i-v-d-a-s` with the writer's characteristic looped descender `s` — no `giri` strokes exist. Name 5 is `S-u-n-d-a-r`; there is no double-`e`/`p` and no `p` descender that `Sundeep` would require. |
| Header, Grid ID | G/C: `I13` — Q: `113` | **I13** | Printed text, seriffed capital `I` clearly distinct from the digit `1` in the same line. Classic `1` vs `I` confusion. |
| p1 r13 (A13) Crown_Dia handwritten | G/C: `27` — Q: `29` | **27** | The digit is over-inked/re-traced. Compared glyph-for-glyph with r12's `37` and r3's `67` in the same column: this writer crosses their `7` with a long horizontal bar and starts it with a flat top stroke. r13's second digit has exactly that structure (flat top + diagonal + crossbar), doubled by the re-trace. A `9` would show a closed bowl, which is absent. **Correction/re-trace noted; final intended value = 27.** |
| p2 r29 (A29) Shoot_L handwritten | G/C: `57` — Q: `55` | **57** | Crossed `7` again; the second glyph has the crossbar, not the `5`'s flat top bar + bowl. |
| p2 r29 (A29) Remarks | Q duplicated `main stem broke` onto r29 — G/C leave blank | **blank** | The remark cell is physically on row 30's line; row 29's Remarks cell is empty. Q row-slipped. |
| p2 r30 (A30) Basal_Dia_1 handwritten | G/Q/C: `1.4` | **1.4** | Confirmed, but note: there is a scribbled-out ink blob immediately left of `1·4` — an aborted first attempt. Final intended value `1.4`. |
| p2 r32 (A32) Species | G/C: `Diospyros ghatensis` — Q: `Diospyros ghantensis` | **Diospyros ghatensis** | Printed text; no `n` before `t`. |
| p3 r40 (B01) Basal_Dia_1 handwritten | G/C: `0.7` — Q: `0.4` | **0.7** | Crossed `7`; Q reads the crossbar as a `4`. Same failure mode at p3 r59 and r60. |
| p3 r43 (B04) Basal_Dia_1 handwritten | G/C: `1.7` — Q: `1.2` | **1.7** | Crossed `7`. |
| p3 r55 (B16) Crown_Dia handwritten | G: `58` — Q/C: `38` | **58** | Cropped at zoom 25. First digit has a straight horizontal top stroke joined to a single lower bowl = `5`. A `3` in this hand (cf. r54 `28`, r47 `42`) is two stacked curves with no straight top. Minority-report accepted against 2/3 agreement. |
| p3 r59 (B20) Basal_Dia_1 handwritten | G/C: `0.7` — Q: `0.4` | **0.7** | Crossed `7`. |
| p3 r60 (B21) Basal_Dia_1 handwritten | G/C: `0.7` — Q: `0.2` | **0.7** | Crossed `7`. |
| p3 r60 (B21) Crown_Dia handwritten | all: `15` | **15** | Spot-checked because the `1` is a bare vertical stroke abutting the cell border; confirmed `15`, not `5`. |
| p3 r56 (B17) Crown_Dia handwritten | G/Q wrote `-`; C blank | **blank** | It is a strike-through dash = no entry per spec, so the cell is empty. Note this is the only *isolated* dash on the form (the row's other three handwritten values are real numbers). |
| Species spellings (all pages) | Q mangles several: `Syzgium`, `Palaiquium ravi`, `Palauquium`, `ghantensis` | **printed forms** | Verified against crops: `Syzygium densiflorum`, `Syzygium rubicundum`, `Syzygium gardneri`, `Palaquium ravii`, `Palaquium ellipticum`, `Beilschmiedia dalzelli`, `Reinwardtiodendron anaimalaiense`, `Diospyros sylvatica`, `Diospyros ghatensis`, `Mesua ferrea (small_leaf)`, `Dysoxylum malabaricum`, `Litsea nigrescens`, `Litsea coriacea`, `Holigarna nigra`, `Heynea trijuga`, `Clausena indica`, `Knema attenuata`, `Dimocarpus longan`, `Cullenia exarillata`, `Drypetes wightii`, `Myristica beddomei`, `Vateria indica`. Note `dalzelli` (single terminal `i`) and `ravii` (double) are as printed, not normalised to accepted botanical spellings. |

## Remarks column — full list (verified at zoom 20)

- p1 r13 (A13): `top broken`  (lowercase `t`, crossed)
- p2 r30 (A30): `main stem broke`  (overflows into the right margin)
- p3 r41 (B02): `top dry`
- p3 r43 (B04): `Drying, leaf dry, borer attack`  (wraps onto a second line in the right margin, below the cell)
- p3 r51 (B12): `top broken`
- p3 r56 (B17): `top dry`
- p3 r59 (B20): `Broken`  (capital `B`, matching the writer's capital in `Drying`)

Case is as written: `top …` remarks are lowercase, `Broken` and `Drying` are
capitalised.

## Structurally unusual items

- **Split measurement columns** (printed prior + handwritten new) — the single
  most likely thing for a converter to collapse. Both values are kept.
- **"6 month later survival"** is a metadata-block column group that is entirely
  blank on this form. Transcribed as a label with an empty value so its presence
  is recorded.
- **Circled serial numbers** at S.no 11, 13, 26.
- **Row 52 (B13)** species `Reinwardtiodendron anaimalaiense` is printed on two
  physical lines inside one cell; joined into one value.
- **Row 43 (B04)** remark wraps outside the table border into the right margin.
- **Row 30 (A30)** remark also runs past the table's right border.
- **Ink-blot correction** at p2 r30 Basal_Dia_1 handwritten; **re-traced digit**
  at p1 r13 Crown_Dia handwritten.
- Page numbers `1`, `2`, `3` are printed in the top-left of each page; captured
  as a `Page,N` metadata row.
- No ditto marks, no row-spanning annotations, no footnote legends, no rotated
  marginal writing on this form. Margins were cropped and checked on all three
  pages — the only stray mark is a tiny pen tick left of S.no 44 (not a circle,
  not transcribed).

## Excluded — illegible

None. Every cell was resolved with reasonable confidence.

Lowest-confidence calls, in order (all transcribed, none omitted):
1. Observer name 5 `Sundar` — handwriting is a rapid scrawl; the final letter is
   a descending stroke consistent with this writer's terminal `r`.
2. Observer name 2 `Sivdas` — could conceivably be `Sivadas`; no vowel stroke
   is visible between `v` and `d`, so `Sivdas` as written.
3. p1 r13 Crown_Dia `27` — over-inked, see adjudication above.

## Rebuild note (round 2)

The original Opus-written golden.xlsx was accidentally overwritten by the
consensus builder. It was rebuilt from the SAME base (gemini-3.6-flash
per-tile) that this adjudication endorsed, and the consensus_fix sheet was
removed because its only entry (`38`) is the reading this document explicitly
rejects in favour of `58` (p3 r55 Crown_Dia). All adjudications recorded above
therefore still hold for the current file.
