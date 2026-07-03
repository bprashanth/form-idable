# Gemini 3.5 Flash — GridVegetation100mx100m direct-PDF experiment

**Model**: `gemini-3.5-flash`  
**Prompt**: minimal (upload PDF → "extract all data as JSON sheets")  
**No Textract, no crops, one API call**

## Cost & speed

| Metric | Value |
|---|---|
| Input tokens | 1,881 |
| Output tokens | 3,901 |
| Total tokens | 14,577 |
| Cost (approx) | **$0.00175** |
| Elapsed | 56.8s |
| Forms extracted | **6** (3 PDF pages × 2 forms/page) |
| Cost per form | ~$0.00029 |

Compare to codex+Textract for the same PDF page 1 only:
- Textract: ~$0.05–$0.10/page
- Codex: ~89,655 tokens × Anthropic pricing ≈ $0.50+  
- **Gemini processed 3× more pages at ~100× lower cost per form.**

## What Gemini got right

### 1. All 6 form-sheets found and cleanly separated
The 3-page PDF contains 6 complete form-sheets (M13, L13 on page 1;
K11, J11-02 on page 2; N15, M15 on page 3). Gemini identified all 6,
named them by Grid no, and produced one metadata + one-alien-trees +
one-alien-plant-prevalence sheet per form. Clean separation, no
form-bleeding.

### 2. Metadata fields — excellent
All clean fields match exactly: GPS coords (correctly restored leading
"10." on M13), slope (correctly decoded "RO"→"20" for L13), dates
(correctly read as "29th Apr '16" across both page-1 forms). No
flagging needed here — all confident correct reads.

### 3. Canopy quadrant grids — condensed but correct
Gemini put the 2x2 quadrant data directly in the Metadata sheet as a
single field:
- M13 Canopy density: `"S, S, S, S"` ✓
- M13 Canopy composition: `"N, N, N, N"` — all N (matches codex, differs
  from golden's `"2, N, N, N"`)
- L13 Canopy density: `"S, S, S, S"` ✓
- L13 Canopy composition: `"M, M, M, M"` ✓

No spatial orientation info (N/West/East lost), but the values are
correct. For this form, compass direction probably doesn't matter much
(it's a 100m uniform grid).

### 4. Cover-field OCR garbles — correctly normalized (no prompt)
Without any schema or legend injection:
- M13 Mikania Cover: `"low"` (Textract raw: `"lm"`)
- L13 Wedelia Cover: `"High"` (Textract raw: `"Httigh"`)
- L13 Polygonum Cover: `"low"` (Textract raw: `"how"`)
- L13 species name: `"Polygonum"` not `"Pohyjorum"` ✓

### 5. Disturbance field — MORE complete than Textract+codex
- **M13**: Gemini read `"metal wires of nipping lines. Drip irrigat. pipes."` vs
  golden's `"metal wires(?), snares(?)"` and codex's `"metal wires"`.
  Gemini got more of the handwritten note.
- **L13**: Gemini read `"Eucalyptus."` — the bottom form's Disturbance field
  which Textract missed entirely and codex left blank after a crop.
  This is a genuine find: Gemini saw something there where Textract+codex
  saw nothing.

## What Gemini got different / worse

### 1. No uncertainty flagging
The prompt asked for `" (?)"` on uncertain reads. Gemini ignored this
and committed to everything confidently. This is a problem: a reviewer
has no signal for which cells need a second look. The Textract+codex
approach's yellow-fill convention is meaningfully better for uncertain
cells (dates, ambiguous checkboxes, OCR garbles).

### 2. Checkbox notation is inconsistent
Three different symbols appear in the output:
- `✓` = clearly checked checkbox (high-confidence read)
- `x` = explicitly marked but visually X-shaped (vs ✓-shaped)
- `α` = appears on pages 2-3 for some checkboxes — likely a different
  handwriting style (surveyor on pages 2-3 drew checkmarks with a loop,
  which Gemini interprets as "α") or genuine alpha symbols. Semantically
  equivalent to `✓` but visually Gemini flagged it differently.

No prompt guidance was given on how to represent checkboxes. For a
downstream database/analysis pipeline, `✓`/`x`/`α` being three
different values for "present" is a data-quality problem.

### 3. Some checkbox readings differ from Textract+codex
On M13 Alien trees:
- Maesopsis Quarter2: Gemini=blank (vs Textract/codex=✓/[X]) — gap
- Silver oak Quarter1: `x` vs golden's `[X]` — same meaning, notation only

On M13 Alien plant prevalence:
- Chromolaena Quarter4: Gemini=blank (vs golden/codex=[X]/X)
- Lantana Quarter2: `✓` (vs Textract's raw `"X"`, golden `"X"`)

These cell-level differences are consistent with "reading directly from
the image at lower resolution" vs. Textract's per-cell character
recognition. Some cells go the other way (Gemini finds a mark Textract
missed).

### 4. Canopy quadrant grids lose spatial structure
A flat `"S, S, S, S"` loses the NW/NE/SW/SE mapping that the original
2x2 grid encodes. Whether this matters depends on whether anyone
downstream actually uses the directional information.

### 5. "Other species" embedded in Alien trees table
Gemini adds an asterisk row at the bottom of the Alien trees table:
`"* | Other species | Coffee | ... "` — a reasonable choice but
different from a separate key/value entry. Minor structural variation.

## Comparison matrix: M13 page-1 key cells

| Field | Golden | Codex | Gemini 3.5-flash |
|---|---|---|---|
| Date | 29th Apr (?)* | 29th Apr '16 (?)* | 29th Apr '16 (no flag) |
| GPS | 10.31305 76.83210 (?)* | 10.31305 76.83210 (no flag) | 10.31305 76.83210 (no flag) |
| Slope M13 | 15 | 15 | 15 |
| Slope L13 | 20 (?)* | 20 | 20 |
| CAN DENSITY M13 | 2×2 grid, all S | 2×2 grid, all S | "S, S, S, S" (flat) |
| CAN COMP M13 | NW=2,NE=N,SW=N,SE=N* | all N* | "N, N, N, N" |
| CAN COMP L13 | all M* | all M* | "M, M, M, M" |
| Disturbance M13 | metal wires(?), snares(?)* | metal wires | metal wires of nipping lines. Drip irrigat. pipes. |
| Disturbance L13 | (blank, flagged)* | (blank, confirmed by crop) | "Eucalyptus." |
| Gliricidia Cover M13 | 100 (pass-through) | low | low |
| Wedelia Cover L13 | Httigh (?)* | High | High |
| Uncertainty flagging | yellow fill on ~15 cells | yellow fill on ~10 cells | **none** |

## Headline finding

Gemini 3.5-flash extracted 6 form-sheets from a 3-page PDF in 1 API
call for **$0.00175** with no Textract, no crops, and no prompt
engineering — and the structural accuracy on clean fields (GPS, slope,
canopy grids, species names, cover values) is high. The main gaps vs.
the Textract+codex pipeline are: (a) no uncertainty flagging, (b)
inconsistent checkbox notation (`✓`/`x`/`α`), and (c) some
cell-level checkbox read differences. Both (a) and (b) are promptable.

**If formidable turns into a Gemini-powered frontend**: the cost and
speed numbers are dramatically better than Textract+codex. The quality
gap comes down to whether the two promptable gaps (flagging + checkbox
normalization) can be closed with a better prompt, and whether the
`α`-checkbox ambiguity on pages 2-3 is real handwriting variation or
a Gemini artifact.
