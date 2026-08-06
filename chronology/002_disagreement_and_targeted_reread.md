# Experiment 002 — canonical tiling, disagreement, and targeted reread

Date: 2026-08-06

## Hypotheses

1. A page-aware canonical schema plus overlapping high-resolution tiles will
   outperform the existing whole-page Gemini extraction.
2. Independent-model disagreement will concentrate transcription errors.
3. A stronger third model, shown only disputed cells at higher effective
   resolution, can safely resolve those disagreements.

## Design

- Added `canonical.py`: page/table/row/column identity, nested headers, source
  boxes, per-model readings, explicit disagreements, validation, and one output
  worksheet per paper page.
- Added `structured_pipeline.py`: one schema call and two independent extraction
  calls per page, using an overview plus four overlapping 2x2 tiles. Provider
  JSON is saved immediately and can be rebuilt without another API call.
- Ran all six pages of `eval_09` with Gemini 3.5 Flash and 3.6 Flash.
- Added `targeted_reread.py`. Its first dry run exposed that model row boxes
  drift after skipped/non-consecutive IDs. The paid pass was blocked until this
  was fixed.
- Replaced row-coordinate crops with full-height column strips. Each strip pairs
  the printed ID/species anchor with at most four disputed columns, includes
  every physical row, and preserves ruled-row order on skewed pages.
- Reread all disagreements with Gemini 3.1 Pro Preview, low thinking. Calls are
  resumable per page.

## Results on eval_09 (n=1 form, 6 pages)

### Two-reader canonical pass

- 3.5 Flash alone: phenology accuracy **0.793**, value accuracy **0.849**,
  false fills **59**.
- 3.6 Flash alone: phenology accuracy **0.839**, value accuracy **0.891**,
  false fills **16**.
- Existing plain-page 3.6 result: phenology accuracy **0.854**.
- The canonical first-reader display: phenology accuracy **0.793**.
- Disputed cells: **393 / 3,209 (12.25%)**.
- On golden valued cells, agreement regions were **94.0%** accurate; disputed
  regions were approximately **29%** accurate under the first-reader display.
  The 12.25% review set captured roughly 63% of remaining errors: about 5x
  concentration over indiscriminate review.
- Full pass cost: **$0.923**, summed provider latency **388 s**.

The tiled canonical pass did not beat the strongest simple extractor. Its value
is provenance and error localization, not a standalone accuracy gain.

### Pro targeted reread

- Requested/returned/applied: **393 / 393 / 393**; no missing decisions or
  canonical validation errors.
- Cost: **$0.454**; summed provider latency: **209 s**.
- Two-of-three candidate majorities: **327**; three-way conflicts: **66**.
- Naive majority display: phenology accuracy **0.813**, value accuracy **0.872**,
  false fills **25**.
- 3.6-default with Pro directly replacing every disputed value: phenology
  accuracy **0.838**, value accuracy **0.890**, false fills **27**.
- 3.6 alone remained better: **0.839 / 0.891 / 16**.
- Pro confidence was nearly constant and did not separate corrections from
  regressions.
- Candidate-majority valued cells were only **44.9%** correct; unresolved
  three-way cells were **6.7%** correct under the first-value display. The
  models are correlated readers, not independent voters.

## Decisions

1. Keep full-height column strips: they solve a real localization failure and
   are sector-agnostic.
2. Keep disagreement as a reviewer-attention signal.
3. Reject automatic majority voting and reject a paid third pass as a default
   accuracy stage on current evidence.
4. Candidate majorities remain yellow/reviewable, not green/accepted. A future
   policy must be calibrated on held-out forms and must beat 3.6 alone.
5. Do not infer a per-column or per-page switching rule from this single test
   form. Continue with exact synthetic ground truth and multiple real form
   archetypes.
