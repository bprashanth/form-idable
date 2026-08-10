# 012 — Additive High variant: local production gate

## Constraint

The existing Codex worker is the `low` product and must remain byte-for-byte
deployable as before. High is per job, additive, and cannot hide uncertainty by
letting a second model or ecological knowledge overwrite literal pixels.

## What was built

1. The upload contract now stores `effort=low|high`. Missing effort defaults to
   low for every historical job.
2. Low still launches task family `formidable-worker`, container `worker`.
   High launches the new task family/image `formidable-high-worker`, container
   `high-worker`.
3. High maps each page into a canonical, page-shaped schema, then uses Gemini
   3.6 Flash as the immutable primary and Gemini 3.5 Flash as the peer. Exact
   agreement is accepted; disagreement retains the primary and creates a red
   human-review region. There is no third-model vote.
4. A separate ecology stage applies generic physical bounds, robust
   within-column statistics, and GBIF taxonomy checks. It never edits a value.
   Medium/high findings create orange regions; informational taxonomy context
   appears only in Analytics.
5. High publishes page sheets, broad review crops, exact cell bboxes,
   `review_manifest.json`, `analytics.json`, `ecology_review.json`, canonical
   JSON and raw model evidence. The workbook keeps page sheets first and puts
   the ecology audit sheet last.
6. The PWA shows high/low at upload and in the dashboard. Low renders the old
   review surface. High adds always-visible red/orange page boxes, matching
   table hues, focused queues and a read-only Analytics tab.

## Failures caught by the local gate

- The first image omitted `xlsx_diff.py`, an import transitively required by
  the benchmark module. The container smoke test caught it before AWS.
- Direct Gemini returned a hard billing error: prepayment credits were
  depleted. OpenRouter was already configured and exposes the same Gemini
  3.6/3.5 models with structured vision, so only the billing gateway changed.
- The first recovery rebuild glob included `*.meta.json` as a page and created
  duplicate page numbers. The rebuild now excludes metadata and production
  refuses any canonical validation error.
- The ecology audit sheet was initially inserted before page 1, which would
  have broken page-to-workbook alignment and correction coordinates. It is now
  appended after all paper pages.
- Every taxonomy information note initially entered the orange queue (29
  items). The actionable queue is now 10; 19 informational notes remain in
  Analytics. This is a direct human-fatigue reduction.
- This ARM64 host would have built an image incompatible with the existing
  x86_64 Lambda. Deployment now explicitly cross-builds the handler for amd64,
  declares the new Fargate task ARM64, and has a high-only rollback path.

## First real form result

Fixture: `eval_13`, Sapling Survival Monitoring, two pages.

- 831 mapped cells; 752 filled; zero canonical validation errors.
- 24 reader disagreements (2.9% of mapped cells).
- 10 actionable ecology findings; 19 informational taxonomy notes.
- Provider time 154.3 seconds; measured model cost $0.34321.
- Broad crops plus exact cell boxes preserve page/workbook geometry.

The old evaluator treated a visible checkmark `✓` and a typed golden `X` as
different even though both mean a checked mark. Raw metrics remain unchanged,
but a new semantic metric canonicalises only these visibly equivalent marks.

| Metric | Low Codex | High dual reader |
| --- | ---: | ---: |
| Semantic all F1 | 0.838 | **0.872** |
| Semantic recall | **0.907** | 0.868 |
| Semantic precision | 0.778 | **0.877** |
| Numeric F1 | 0.955 | **0.982** |
| Word F1 | 0.753 | **0.837** |
| Output/golden cell fraction | 1.010 | **0.982** |

High wins overall and invents less, but the recall loss is real and must be
shown rather than averaged away. Red review regions are the mechanism for that
residual margin, not permission to silently choose the peer.

## Gates passed so far

- Python contract/style tests pass.
- Production PWA bundle builds.
- 18 mocked browser flows pass.
- One browser flow using the real high artifacts passes and was visually
  opened at `benchmarks/high_visuals/actual-eval13-*.png`.
- Actual high worker container builds and processes the two-page form.

This is a local checkpoint, not permission to claim all-form or production
success. Broader benchmark and production browser gates follow.
