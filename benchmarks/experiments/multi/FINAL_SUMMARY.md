# Final summary: scope/descope recommendations
## 5-PDF codex+Textract experiment results

**Experiment**: Run the "exp2" recipe (Codex CLI in Docker, Textract
`v1.json` provided, crop access via `render_page.py`, `system_prompt_crops.md`,
no turn cap) on 5 PDFs spanning Tiers 1-3 of the Shankar POC scope,
each structurally distinct from the initial TreePlots20mx20m test.
For each: build a hand-made golden, run codex, compare.

---

## What the agent is already very good at (keep as-is)

### 1. Recovering all tables from v1.json

Across all 5 PDFs, codex correctly transcribed every Textract-detected
table into `output.xlsx`. Header rows merged correctly (PDF4's 2-row
header merged to 1, PDF2's label rows absorbed into section metadata).
Row/column counts matched golden in all cases. **No changes to the
pipeline needed for "standard" table transcription.**

### 2. OCR correction and ambiguous-cell flagging

Codex independently made the same light corrections golden made, without
being told the "right" answer:
- PDF1: Two digit corrections (A11 0.7, A16 1.1) — exact match
- PDF2: Header merged fields (Avg Cloth Bag Wt, Avg Packet Wt) — same
- PDF4: Two header corrections (Observers "Vanidas S Moorths"→"Vanidas
  & Moorthi", Start time "9:12 aM"→"9:12 am") — exact match
- PDF4: Structural fix for DEAD/DRY row (tree 30) — same fix, same
  flagged cell range, independently derived
- PDF5: Five Cover-field garbles ("lm", "lon", "Httigh", "how", "100" →
  "low"/"high") — all corrected, plus "Pohyjorum"→"Polygonum"

In every ambiguous case (canopy densitometer checkbox, Site field
handwriting, GPS leading digit), both golden and codex flagged yellow
with a best-guess — the uncertainty was surfaced correctly even when
the specific guesses differed. **The flagging convention is working as
designed. No prompt changes needed here.**

### 3. Recovering off-table sections (new_sections + v2_meta.json)

Four distinct "structure missing from v1.tables" variants were tested:
- **PDF2**: Clean 2-column dry-weight section — codex recovered it
  with matching v2_meta.json bboxes (slight row-attachment difference
  from golden, text matches)
- **PDF3**: Two numbered species-lists mis-keyed by Textract — codex
  recovered both, added MORE detail on crossed-out species name than
  golden
- **PDF4**: No off-table sections — both golden and codex correctly
  wrote no v2_meta.json
- **PDF5**: Four 2x2 marginal quadrant grids (CAN DENSITY + CAN. COMP
  × 2 forms) — codex independently identified all four, built the
  West/East × North/South structure, wrote v2_meta.json with accurate
  bboxes. **This was the hardest test and the clearest win**: these
  grids are not described in the system prompt at all, yet codex
  recognized them from the compass labels and spatial layout of the
  `other_text` fragments.

### 4. Multi-form page separation (PDF5)

Two complete near-identical form-sheets stacked on one page: codex
kept them cleanly separated with no row-bleeding between forms, even
though both forms have the same internal column structure and nearly
identical section headings. No prompt addition needed.

### 5. Dense grid pass-through (PDF4)

37×15 table (555 cells), single-char cells: codex matched golden
cell-for-cell including OCR artifacts in "Fallen" columns, plus made
the one structural fix (DEAD/DRY row) that both golden and codex
independently identified. No crop budget wasted on dense single-char
columns — the "don't zoom into individual cell values" guidance worked.

---

## What to actually scope/change

### KEEP in scope (no changes)

- Textract `analyze()` with TABLES+FORMS+LAYOUT on every page — all
  three feature types contributed across the 5 PDFs
- `v1.json` `simplify()` output (tables + key_values + other_text)
  as the agent's primary input — the agent uses all three consistently
- Crop tool (`render_page.py`, fractional bbox, zoom cap ~1568px) —
  used in every run, critical for quadrant grids (PDF5), tally marks
  (PDF3), off-table sections (PDF2/PDF3/PDF5), and confirming blanks
  (PDF5's bottom disturbance field)
- `v2_meta.json` `new_sections` format — used correctly on PDF2/3/5
- Yellow-fill flagging convention — working as designed across all 5

### DESCOPE — not needed

- Any attempt to crop and verify dense single-char numeric/categorical
  columns: the "don't zoom into individual cell values" guidance is
  correctly followed and prevents wasted turn budget on 555-cell
  tables. Codex does NOT need to verify each "Y"/"N"/"0"-"4" cell
  in a dense grid — it correctly passes them through.
- Any "retry" or multi-pass logic: all 5 runs succeeded in a single
  uncapped pass (48K–90K tokens, 2–9 crops each).

### PROMPT ADDITIONS (small, concrete)

**1. Ambiguous non-tally marks: blank+flag, not free-text description**

PDF3's row-2 seedlings: codex wrote `"symbol/mark"` (text string) in
a numeric column where golden wrote `5*` (numeric+flag). The production
prompt says "sum tally marks to an integer" but doesn't handle the case
where a mark looks tally-like but doesn't fit `I`/`II`/`III` etc.
Add: *"If a mark in a count column doesn't clearly parse as a tally,
dot, line-through, or blank, write the cell as blank and flag it — do
not write a text description, as that breaks numeric columns."*

**2. Extra characters adjacent to checkboxes: preserve and flag**

PDF5: codex silently dropped stray annotations like `"Y [X]"` → `"X"`,
`"[X] A"` → `"X"`. These may be meaningful (a note next to the
checkbox). The `"[X] A"` case on L13/Lantana/Quarter3 is a concrete
example where "A" could be a surveyor's annotation worth keeping.
Add: *"If a checkbox cell contains characters beyond `[X]` or `[ ]`
(e.g. `Y [X]`, `[X] A`, `[X] r`), flag the cell and include the extra
characters — don't silently discard them."*

**3. Scan-artifact exclusion needs to be more explicit**

PDF3: codex included a "Top-left note: Done" row for the binder-clip
scanning artifact + stray initial. The current "ignore stray marks"
guidance wasn't strong enough to override "looks like text, include
it". Add: *"A black rectangle or shadow in a corner (binder clip
artifact), a single letter or initial that doesn't belong to any form
field, or a page number in the margin are scan artifacts — do not
include them as data rows in output.xlsx."*

### TEXTRACT / PREPROCESSING IMPROVEMENTS (bigger changes, future work)

**4. Categorical-column normalization in `textract_minimize.py`**

PDF4's "Fallen" columns (Leaves/Flowers/Fruits Fallen) are ~90% Y/N/y
with scattered OCR garbles (Z, 2, 7, X, ", 8N). PDF5's "Cover" column
has "lm", "lon", "Httigh", "how", "100" as garbles of "low"/"high"
from a form that prints its own legend ("Cover: 0=Absent, 1=Low <33%,
2=Med 33-67%, 3=High >67%"). Both are columns where the expected
value set is small and inferable either from the column header or from
an adjacent printed legend.

A preprocessing step in `textract_minimize.py`:
- Detect columns where ≥80% of values fall in a small set
  (e.g. {Y, N, y}, {low, med, high}, {X, [ ], [X]})
- Normalize single-char outliers to the nearest value in that set
  (edit-distance 1: "Z"→"Y", "7"→"Y", "2"→"N"; "lm"→"low", etc.)
- Flag any cell that was normalized (so the agent/reviewer still sees
  the uncertainty)

This fixes OCR noise *before* the agent sees it, without requiring
crop budget, and would generalize across all ecology forms that use
these cover/presence/absence scales.

**5. GPS leading-digit normalization**

PDF5 Form 1: "1.31305 76.83210" (leading "10" OCR-dropped) vs
Form 2's correct "10.31309 76.83302". A simple sanity check in
`textract_minimize.py`: for GPS values extracted from a "Grid Centroid
GPS:" key, if the latitude is <9 but the page's other GPS values are
~10.x, prepend "10." and flag. Very specific but cheap.

---

## Token and crop budget summary

| PDF | Tier | Tokens | Crops taken | Result |
|---|---|---|---|---|
| GrowthSurvivalMonitoring | 1 | 48,292 | ~2 | Very close match |
| LeafLitterBiomass | 1 | 78,131 | ~4 | Strong match incl. missing col + off-table section |
| RegenerationPlot5mx5m | 2 | 48,330 | ~6 | Strong match, tally marks correct |
| TreePhenologyTwoTrails | 2 | 57,166 | ~3 | Essentially identical |
| GridVegetation100mx100m | 3 | 89,655 | 8 | Strong match, all 4 quadrant grids recovered |

**Tier 1-2**: 48K–78K tokens, predictable. **Tier 3** (two-form page):
89K — scales roughly linearly with page complexity. All within budget
for a single uncapped run.

---

## What this experiment answers

**Q: Can Textract + crops + the current prompt handle the full Shankar
scope?**

**A: Yes, for all structural patterns observed across Tiers 1-3:**
- Standard tables (PDF1-4): agent converges to golden or better
- Off-table numbered/grid sections (PDF2, PDF3): independently recovered
- Dense single-char grids (PDF4): correct pass-through
- Marginal spatial grids not in v1.tables (PDF5): independently found
- Two-form stacked pages (PDF5): cleanly separated

**The gaps are small and well-defined**, not architectural:
1. Ambiguous-mark → blank+flag rule (prompt, one sentence)
2. Extra-char-by-checkbox → preserve+flag rule (prompt, one sentence)
3. Scan-artifact exclusion (prompt, one sentence)
4. Categorical-column OCR normalization (textract_minimize.py, future)
5. GPS leading-digit normalization (textract_minimize.py, future)

None of these require changes to the tool set, the codex invocation,
the Textract call pattern, or the v1.json schema. The recipe as-is
is production-ready for Tiers 1 and 2, and close to production-ready
for Tier 3 with items 1-3 above added to the system prompt.
