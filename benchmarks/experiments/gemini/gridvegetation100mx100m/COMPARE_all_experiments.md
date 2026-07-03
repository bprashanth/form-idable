# GridVegetation100mx100m — 5-experiment comparison

3-page PDF, 6 form-sheets (2 per page: M15×2, M13+L13, K11+JH-02).
Baseline golden covers M13 (page 2 top).

---

## Cost & speed summary

| Exp | Model / approach | Tokens | Cost | Time | Forms found |
|-----|-----------------|--------|------|------|-------------|
| 1 | gemini-3.5-flash + thinking (baseline) | 14,577 (incl. 8,795 think) | **₹13.23** | 56.8s | 6 |
| 2 | gemini-2.5-flash + thinking | — | ~₹1.96 | — | 6 (poor quality) |
| A | gemini-3.5-flash, no thinking, pdf-only | 6,157 | **₹0.24** | 24.7s | 6 |
| B | codex-only, no Textract (gpt-5.5) | 115,750 | ~$0.50–1.00 est | ~6 min | 6 |
| C | gemini-3.5-flash, no thinking, +v1.json | 33,212 | **₹0.57** | 28.7s | 6 |

*Codex cost estimated from token count × gpt-5.5 pricing; not directly billed here.*

**Cost observation**: 98% of exp 1's cost was thinking tokens. Disabling thinking (exp A) drops from ₹13.23 → ₹0.24 — a **55× reduction**. Adding Textract's v1.json (27K more text tokens) raises exp C to ₹0.57, still 23× cheaper than exp 1.

---

## Form coverage (all 6 forms, all 3 pages)

| Exp | All 6 forms found? | Page 3 (K11, JH-02) |
|-----|-------------------|---------------------|
| 1 (3.5+think) | Yes | Yes |
| A (3.5 no-think) | Yes — 24 sheets | Yes |
| B (codex-only) | Yes — 232 rows, single v2 sheet | Yes, plus correctly identified JH-02's Q1 continuous-line blanks |
| C (textract+3.5) | Yes — 25 sheets, incl. canopy sub-sheets | Yes |

All experiments successfully covered all 3 pages and all 6 form-sheets. No coverage gaps.

---

## M13 metadata quality (page 2 top — the golden form)

| Field | Golden | Exp 1 (3.5+think) | Exp A (3.5 no-think) | Exp B (codex-only) | Exp C (textract+3.5) |
|-------|--------|-------------------|----------------------|--------------------|----------------------|
| Grid no | M13 | M13 ✓ | M13 ✓ | M13 ✓ | M13 ✓ |
| Date | 29th Apr '16 | 29th Apr '16 ✓ | 29th Apr '16 ✓ | 29 Apr 2016 ✓ | 29th April '16 ✓ |
| GPS | 10.31305 76.83210 | 10.31305 76.83210 ✓ | 10.31305 76.83210 ✓ | 10.31305, 76.83210 ✓ | 10.31305, 76.83210 ✓ |
| Slope | 15 | 15 ✓ | 15 ✓ | 15 ✓ | 15 ✓ |
| Disturbance notes | metal wires(?), snares(?) | metal wires of nipping lines. Drip irrigat. pipes. ★ | metal wires, drip-irrigation ★ | metal wires + ringing lines; drip irrigation pipes (?) ★ | (blank in meta row) |
| Canopy density | S S S S (2×2) | "S, S, S, S" (flat) | "N: S, S \| S: S, S" (directional) | "S / S / S / S" in marginal notes | Separate sheet: NW=S NE=S SW=S SE=S ✓ |
| Canopy composition | 2\*,N,N,N (NW uncertain) | "N, N, N, N" | "N: M, M \| S: M, M" ✗ | "N / N / N / N" in marginal notes ✓ | Separate sheet: NW=N NE=N SW=N SE=N ✓ |

**★** = More complete than golden (Textract/codex missed parts of disturbance)

**Canopy grid**: Exp A got composition wrong (N→M). Exps B and C got it right.
Exp C's separate "Canopy Diagrams" sheet with NW/NE/SW/SE structure is the best representation of all.

---

## M13 checkbox quality: Alien trees table

Expected (golden/best-read): Silver oak Q1=absent, Q2-Q4=present; Maesopsis Q1-Q3=present, Q4=absent; Spathodea all absent; Eucalyptus all absent.

| Species | Q1 | Q2 | Q3 | Q4 | Exp 1 | Exp A | Exp B | Exp C |
|---------|----|----|----|----|-------|-------|-------|-------|
| Silver oak | absent | present | present | present | x/✓/✓/✓ ≈✓ | ✓/blank/✓/✓ ≈✓ | P/P/P/A ≈✓ | Tick/blank/Tick/blank ✗ |
| Maesopsis | present | absent? | present | absent? | ✓/blank/✓/blank ✓ | ✓/blank/✓/✓ ≈✓ | P/P/P/P (Q4 extra?) | Tick/blank/blank/blank ✗ |
| Spathodea | absent | absent | absent | absent | x/x/x/x ✓ | ✗/✗/✗/✗ ✓ | A/A/A/A ✓ | Tick/Tick/Tick/Tick ✗✗ |
| Eucalyptus | absent | absent | absent | absent | x/x/x/x ✓ | ✗/✗/✗/✗ ✓ | A/A/A/P (Q4 err?) | Tick/Tick/Tick/Tick ✗✗ |

**Exp C (Textract+Gemini) checkbox reads are badly wrong for M13.** Spathodea and Eucalyptus (absent species) show Tick across all quarters. The v1.json context (from page 1, covering M15 forms) appears to have confused the model when reading page 2's checkboxes. Adding Textract *hurt* quality here.

**Exp A** (no thinking, no Textract): Good Spathodea/Eucalyptus (all absent correct). Silver oak mostly right.

**Exp B** (codex-only): Spathodea correct (A/A/A/A). Eucalyptus Q4 questionable (A/A/A/P). Uses P/A instead of ✓/✗.

---

## M13 checkbox quality: Alien plant prevalence

Key rows (golden approximate from prior experiments):

| Species | Exp A (no-think) | Exp B (codex-only) | Exp C (textract+gemini) |
|---------|-----------------|-------------------|------------------------|
| Lantana | ✗/✗/✗/✗ | A/A/A/P | Tick/blank/Tick/Tick ✗ |
| Chromolaena | ✓/✓/✓/✓ | A/A/P/A | blank/blank/blank/blank ✗✗ |
| Mikania | ✓/✓/✓/✓ | P/P/P/P(?) | Tick/blank/Tick/blank |
| Wedelia | ✓/✗/✗/✗ | P/A/A/A | Tick/Tick/Tick/Tick ✗ |
| Gliricidia | ✓/✗/✗/✓ | P/A/A/P | Tick/Tick/Tick/Tick ✗ |
| Polygonum | ✓/✓/✓/✓ | P/P/P/P | Tick/Tick/Tick/Tick |

Exp C again shows systematically wrong readings (blank where present, Tick where absent). This confirms the Textract page-1 context actively interferes with visual reading of page 2.

---

## Uncertainty flagging

| Exp | Flags uncertain cells? | Method |
|-----|----------------------|--------|
| 1 (3.5+think) | No | (ignored prompt instruction) |
| A (3.5 no-think) | No | (ignored prompt instruction) |
| B (codex-only) | Yes | Yellow fill + openpyxl Comment; cell list at bottom of v2 |
| C (textract+3.5) | No | (ignored prompt instruction) |

Only codex-only produced uncertainty flags. The Gemini prompt asked for ` (?)` on uncertain reads — both Gemini variants ignored this. Codex was told to use yellow fill and did so.

---

## Structural observations

**Exp B (codex-only) standout findings:**
- Correctly identified Form 6 (JH-02) Q1 as a "continuous vertical line / no entry" and left blank with a comment. This is nuanced notation-rule compliance that the Gemini variants missed (they just left Q1 blank without explanation).
- Picked up extra species rows: `B. oak (?)`, `Entimena (?)`, `Polygonum: L (?)` with yellow flags.
- Canopy sketch values embedded in "Marginal notes" field — loses the 2×2 grid structure but values are correct.
- Single flat `v2` sheet for all 6 forms — harder for downstream parsing vs. multi-sheet approaches.

**Exp C (textract+gemini) standout finding:**
- Produced separate "M13: Canopy Diagrams" sheet with NW/NE/SW/SE structure — best canopy representation of all 5 experiments.
- But checkbox quality on pages 2-3 is severely degraded by the page-1-only Textract context. This is a **cross-page contamination problem**: v1.json covers only page 1 (M15 forms), and Gemini appears to use it as a template that bleeds into page 2-3 reading.

---

## Headline conclusions

### 1. Thinking tokens buy marginal quality at extreme cost
Disabling thinking cuts ₹13.23 → ₹0.24 (55×). Exp A's quality on clean fields (GPS, slope, dates, canopy density) is essentially identical to exp 1. Main loss: canopy composition error for M13 (N→M). Not worth ₹13 per PDF.

### 2. Textract v1.json as context actively hurts multi-page PDFs
When v1.json covers only page 1, feeding it to Gemini for a 3-page PDF causes cross-page interference on page 2-3 checkboxes. Exp C is the *worst* performer on M13 checkbox quality despite being the most expensive Gemini variant (₹0.57). If Textract is used with Gemini, it must cover the same page being read.

### 3. Codex-only is the most thorough but expensive in tokens
115,750 tokens vs ~6,000 for Gemini. Gets notation rules right (continuous line → blank with comment, P/A convention, yellow flags). Downsides: flat single-sheet structure, P/A notation differs from standard, canopy grid buried in free-text. Cost in Anthropic tokens is the main drawback for production.

### 4. Gemini 3.5-flash, no thinking, pdf-only (Exp A) is the sweet spot
- **₹0.24 for 6 forms** across 3 pages in 25 seconds
- All 4 Q columns populated
- Good checkbox reads on Spathodea/Eucalyptus (absent) and most Mikania/Polygonum
- Main fixable gap: no uncertainty flagging (promptable)
- Main non-promptable gap: some checkbox cell misreads (Q2-Q4 Silver oak)

### 5. The "formidable as Gemini frontend" question
Exp A demonstrates that a one-call Gemini approach at ₹0.24/3-page-PDF is viable as a first-pass transcription. The quality gaps vs. the Textract+codex pipeline:
- **Promptable**: checkbox normalization (currently ✓/✗/α mix), uncertainty flagging
- **Structural**: canopy quadrant grid loses spatial orientation (flat comma list vs. 2×2)
- **Non-promptable**: some checkbox cell misreads on ambiguous marks

The codex+Textract pipeline costs 200×+ more but produces: yellow-flag uncertainty signals, correct canopy 2×2 grids, proper `v2_meta.json` for off-table sections, and higher checkbox fidelity on ambiguous cells. For production use, a two-stage approach (Gemini first-pass + codex targeted review of flagged cells) is worth exploring.
