# Experiment 001 — evaluation gate and exact production baseline

Date: 2026-08-06

## Hypothesis

Before comparing models, a scorer must reject outputs that preserve the token
bag while corrupting the document. A useful baseline must also be the exact
live production artifact, not the similar but different Codex benchmark prompt.

## Work

- Added `benchmarks/wide/integrity_eval.py` and its reproducible suite runner.
- Downloaded the reported production job's workbook, crop manifest, and run log
  read-only from S3 to
  `eval_forms/eval_09/outputs/_production_1266657/`.
- Ran adversarial golden-as-candidate mutations: blank, 10% row subset, modal
  fill, column shift, adjacent-column swap, row shuffle, partial row slip, page
  flatten, duplicate rows, phantom rows, invented blank fills, and harmless
  formatting noise.
- Asked a separate Cursor/Claude agent to act as a hostile scientific reviewer
  of the scorer design. It made no edits.

## Evaluator result

The integrity gate passes on both eval_09 and a newly generated exact-layout
template form.

On eval_09, the position-blind content score remains 1.000 after shifting every
column, shuffling rows, or flattening six pages into one. Strict exact-cell F1
falls to 0.133, 0.440, and 0.000 respectively. A perfect 10% row subset retains
precision 1.000 but recall falls to 0.088. The modal filler has off-mode
accuracy exactly 0 by construction.

Metrics are deliberately separated:

- `content_anywhere`: historical token recovery; position blind.
- `occupied_position`: structural occupancy at exact page/row/column.
- `exact_cell`: correct value at exact page/row/column.
- `offmode_accuracy_all` and balanced class recall: resistant to modal filling.
- page, shape, false-fill/extra-position, duplicate, constancy, and oracle modal
  controls.

Strict coordinates remain diagnostics on the real content-consensus goldens,
not accuracy headlines. They are valid headlines only on exact-layout goldens.

## Exact live production baseline: eval_09 (n=1)

- Old multiset ALL-F1: **0.899**.
- Positional phenology accuracy: **0.725**.
- Oracle modal null phenology accuracy: **0.783**.
- Row coverage: **1.000**; false fills: **65**.
- Workbook: one `v2` sheet for six paper pages; page-layout F1: **0.000**.
- Five candidate columns are at least 98% constant; no golden column is.
- Six crops total: one near-whole-table crop per page, no targeted rereads.
- Runtime: 191 seconds; Codex reported 52,368 tokens.

This reproduces the prior diagnosis from the live artifact, not merely its
write-up. Production is below a no-reading control on the hand-filled target
columns while appearing strong under the old score.

## Independent-review corrections accepted

1. `cellacc.py` accuracy excludes missing rows; coverage must be incorporated
   into an all-golden-cell denominator before generalising it.
2. Off-mode accuracy is a cleaner modal-filling control than a single aggregate
   null comparison.
3. Anchor alignment must use printed fields only; evaluated handwriting must
   never help choose its own alignment.
4. `consensus_fix` is positionless content inside the golden and must be
   quarantined from positional evaluation.
5. The existing 76 “exact” synthetic forms discarded their cell coordinates,
   and random column typing sometimes contradicts labels.

## Synthetic-contract repair

`gen/fill_template.py` now emits, for newly generated forms:

- `layout_golden.xlsx`, preserving page/row/column coordinates;
- `ground_truth.json`, containing every ruled cell, normalized and point-space
  bounding boxes, printed/written/blank state, expected value, mark type, and
  semantic value kind;
- generic label-driven value types (date, time, species, local name, count,
  measurement, percentage, temperature, pH, coordinate, etc.) with width-based
  fallback instead of purely random typing.

The old corpus is unchanged. A new corpus must be generated so historical
numbers remain reproducible.

## Decision

Proceed to a canonical, source-linked intermediate representation. New pipeline
experiments must produce page/table/row/column identity and region provenance;
CSV token bags are retained only for historical comparison.
