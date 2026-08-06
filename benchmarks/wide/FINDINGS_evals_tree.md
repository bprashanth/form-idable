# Tree/ecology eval — can a local private model match frontier models on real partner forms?

**Eval set:** 14 real scanned partner datasheets (`eval_forms/eval_01..14`,
68 pages) supplied from the project's `evals/` directory — leaf-litter
biomass, growth & survival monitoring, tree phenology transects, regeneration
plots, seed/seedling germination grids, vegetation plots, dendroband and
census sheets, bird checklists. Portrait and landscape, printed structure
filled in by hand, real pens, real photocopies, spiral binding, ink blots.

**Goldens:** built by cross-converter consensus (`consensus.py`). 3–5
independent models transcribe each form; per token we keep the **median
count** across converters; the best-F1 transcription supplies the structural
skeleton; cells the majority does not support are dropped and consensus tokens
the skeleton missed are appended. The result: every golden's token multiset
equals exactly what a committee of frontier models agrees the page says.
`eval_02` additionally has a full human-style cell-by-cell adjudication
(`GOLDEN_NOTES.md`, 14 contested cells resolved) and was used to validate the
method — the tool independently isolated the same single contested cell
(58 vs 38) that the adjudicator had resolved.

**Scoring:** `wide_diff.py` — the nightly regression's tolerant token-multiset
diff, extended with precision and F1. `num_f1` is the headline.

## The contamination caveat (read this before the table)

Every model that helped build the goldens is **advantaged** on this eval:
codex, gemini-3.6-flash, qwen3-vl-32b, qwen3-vl-235b and glm-4.6v all
contributed. Every **local** model is clean — none of them ever touched a
golden. So the comparison is deliberately tilted *against* the local models,
and any local win here is a **lower bound**, not a flattering result.

The honest framing of what this eval measures: *how close does a model get to
what a committee of frontier models agrees the page says.*

## Results

All 14 forms, one run per model.

| model | numF1 | numR | numP | wordF1 | $/form | sec/form | status |
|---|---|---|---|---|---|---|---|
| codex CLI (agentic, crops/zooms) | 0.923 | 0.935 | 0.925 | 0.798 | ~subscr | **649** | ADVANTAGED (built goldens) |
| qwen3-vl-32b (OpenRouter, 7 forms) | 0.901 | 0.918 | 0.897 | 0.807 | 0.0039 | 99 | ADVANTAGED (built goldens) |
| **gemini-2.5-flash** | **0.789** | 0.826 | 0.817 | 0.796 | 0.058 | 102 | **clean — the bar** |
| **Qwen3-VL-2B + LoRA (local, ours)** | 0.668 | **0.856** | 0.635 | — | **0** | 60 | clean |
| qwen3-vl-8b (OpenRouter) | 0.605 | 0.789 | 0.620 | 0.525 | 0.0084 | 169 | clean |

## The tuned 2B: best-in-class reading, broken stopping

The mean (0.668) badly undersells this model. Decomposed:

- Its **recall is 0.856 — higher than gemini-2.5-flash's 0.826.** A 2B model
  running locally at $0 perceives these forms better than the frontier API.
- **8 of 14 forms stop cleanly** (cell_frac < 2). On those: **num F1 0.826**,
  above gemini's 0.789 overall.
- On the other 6 it never emits EOS, running off into arithmetic progressions
  (`37.7,6.4 / 37.8,6.4 / …`) and confabulated species names. Precision falls
  to 0.06–0.29 while **recall stays 0.83–0.97** — it had already read the page
  correctly before it started inventing.

It beats gemini-2.5-flash outright on 5 of 14 forms, and beats **codex** on
eval_13 (0.966 vs 0.955):

| form | tuned 2B | gemini-2.5-flash | codex* |
|---|---|---|---|
| eval_07 LEMoN annual census | **0.938** | 0.731 | 0.994 |
| eval_12 dendroband quarterly | **0.960** | 0.756 | 0.990 |
| eval_13 sapling survival | **0.966** | 0.959 | 0.955 |
| eval_01 leaf-litter (34% zeros) | **0.445** | 0.231 | 0.883 |

### Why it over-produces — and the fix

Over-production tracks how **sparse** the real form is relative to the training
corpus. Every one of the 1,020 training forms is densely filled, so the model
learned "keep emitting rows". eval_03 has the smallest golden (142 cells) and
the worst over-production; eval_02/eval_05 are dense like training and stop at
cell_frac ~1.

Inference-side mitigation (`repetition_penalty=1.05`, `max_tokens=4096`) is
worth having and already default in `wide_bench.local_oneshot` — it lifted
eval_01 0.186 -> 0.445, eval_04 0.069 -> 0.339, eval_03 0.148 -> 0.257 with
recall untouched. But it treats the symptom.

**The fix is training-data distribution: sparse fill as a first-class
parameter.** The partner's own `form4` (Seed Germination) is ~90% empty rows —
the exact shape the model has never seen. This is formgen v3's top priority,
ahead of even the handwritten-vernacular and phone-camera work.

### Per-form numF1, clean models

| form | gemini-2.5-flash | qwen3-vl-8b |
|---|---|---|
| eval_01 leaf-litter biomass | **0.231** | **0.084** |
| eval_02 growth & survival | 0.985 | 0.808 |
| eval_03 regeneration plot | 0.776 | 0.643 |
| eval_04 bird checklists (24pp) | 0.687 | 0.843 |
| eval_05 tree plots 20x20 | 0.901 | 0.857 |
| eval_06 vegetation plots | 0.836 | 0.140 |
| eval_07 LEMoN annual census | 0.731 | 0.365 |
| eval_08 survival/growth | 0.920 | 0.158 |
| eval_09 tree phenology | 0.865 | 0.733 |
| eval_10 grid vegetation 100x100 | 0.928 | 0.862 |
| eval_11 seed/seedling codes | 0.563 | 0.512 |
| eval_12 dendroband quarterly | 0.756 | 0.946 |
| eval_13 sapling survival | 0.959 | 0.796 |
| eval_14 sapling growth | 0.909 | 0.724 |

The spread matters more than the mean: gemini-2.5-flash ranges 0.23–0.99 and
qwen3-vl-8b 0.08–0.95 across the same 14 real forms. A field-deployable
extractor needs the floor raised, not just the average.

## Failure mode discovered: repetition collapse on dense repeated-value grids

`eval_01` (leaf-litter biomass) has 567 numbers in its golden, of which
**191 are the value `0`** (34%) — field workers write a lot of zeros and dots.
Both clean models collapse into repetition loops on it:

| model | symptom | numF1 on eval_01 |
|---|---|---|
| gemini-2.5-flash | one output line of **36,609 chars** of repeated `0000…` | 0.231 |
| qwen3-vl-8b | one output line of **38,843 chars** | 0.084 |

This is not a golden artefact — the golden agrees with the 5-converter
consensus (567 nums / 259 words), and the advantaged models handle the form.
It is a real, reproducible failure of cheap VLMs on dense repeated-value
tables, and it is exactly the kind of page these partners produce.

The synthetic `ecology__litter_biomass` archetype in the training corpus was
built with the same property (heavy dot=0 and "0" cells), so eval_01 is the
sharpest single test in the suite of whether targeted synthetic data repairs a
measured failure mode.

## Training data (what the local model was taught)

`gen/formgen2.py` — 1,020 synthetic forms, goldens exact by construction,
17 archetypes × 60. The decisive change over round 1 is **real ink**: digits
and single-letter code cells are composited from **NIST SD-19** hand-print
(26,040 glyphs, 62 classes × 7 writer cohorts; one cohort per form so a sheet
looks like one person filled it), instead of handwriting fonts. Degradation is
Augraphy (bleed-through, dirty rollers, photocopy, folds, shadows) plus page
furniture (spiral binding, bulldog clips, staples, edge-curl shadow).

Eight archetypes were designed from the real eval domain after inspecting it:
phenology transect (grouped LEAVES/FLOWERS/FRUITS single-char grid over shaded
columns, non-sequential tree numbers, multistem comma lists, row-spanning
DEAD/DRY annotations), growth & survival (printed prior value + handwritten
new value in the same cell, NA dashes, circled row numbers), litter biomass
(decimals, dot=0, asterisk footnotes + legend, ditto line down a column,
rotated marginal numbers), germination code grids (two side-by-side sub-tables
of single letters over alternating shading), regeneration tallies, GBH plots,
soil microclimate (incl. soil temperature), nursery upkeep. Nine
health/education/livelihoods archetypes carry sector breadth.

Eval and training are disjoint: the 14 partner forms were never trained on.

## Caveats

- One run per model per form; treat gaps under ~0.05 as noise.
- The goldens are model-consensus, not human ground truth, except `eval_02`.
  A systematic error shared by all converters would pass unnoticed.
- `eval_04` (24-page bird checklists) is the weakest golden — the converters
  diverged most there (950 consensus tokens had to be appended to the base).
- Costs for codex are subscription-auth; its 649 s/form is measured.
