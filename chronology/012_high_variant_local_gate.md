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
- The high download adds an ecology audit sheet. Counting its repeated labels,
  observations and explanatory prose as transcription would falsely depress
  precision. Accuracy therefore scores the immutable page-only workbook; a
  separate packaging gate checks the deployed workbook's page order, styles,
  page count and final audit sheet.
- The first all-form sweep was stopped after eval 01 because a strict layout
  diagnostic exposed that the providers had correctly read marginal notes and
  legends into `free_text`, but the canonicalizer never attached that branch.
  The repair makes free text first-class in resolution, red disagreement
  review, xlsx, crops, analytics and ecology coordinate discovery. Rebuilding
  saved responses (no new calls) raised eval 01 semantic F1 0.828→0.838 and
  eval 13 0.872→0.882; eval 13 content cell fraction became exactly 1.000.
- A second stopped sweep found row-coverage disagreements could be hidden when
  only one reader emitted a row, and peer-only values could slide into primary
  position. Missing readings are now explicit and ordered by declared model.
  This initially exposed 437 red cells on eval 01, most caused by provider row
  boxes with swapped coordinate orders and harmless row-ID spelling drift.
  Sector-agnostic wide/short row-box repair plus strong geometric alignment
  reduced that to 129/1,168 targets (11.0%) while semantic F1 reached 0.935,
  versus low's 0.728. The residual queue reflects actual value/blank/coverage
  differences and is retained for human review.

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
- The x86_64 API image builds on this ARM host and its in-container effort
  routing test passes. The high release wrapper snapshots and asserts the low
  ECR digest and task-definition ARN before and after deployment.

This is a local checkpoint, not permission to claim all-form or production
success. Broader benchmark and production browser gates follow.

## Later all-form gate findings

- A six-page annual-monitoring form initially produced 59 rows on a page that
  visibly contained 49. The peer reader had omitted a whole Stem ID column,
  merged values such as `85` + `A` into `85A`, and shifted every later value
  left. A strict layout repair now runs only when a response is one column
  short on at least 90% of eight or more rows and the same numeric-ID plus
  one-letter signature holds on at least 90%. It uses no golden values. The
  rebuilt page counts are `49, 49, 49, 13, 39, 49`; false red review cells
  fell from 1,255/4,225 (29.7%) to 83/4,065 (2.0%). Semantic F1 stayed 0.953
  versus low's 0.970, so this is recorded as a layout/reviewer-fatigue repair,
  not an accuracy win.
- The first eight-PDF browser sweep loaded every page image and exact review
  overlay, but it also caught a real asynchronous-image test bug on page 4 of
  the 24-page bird form: DOM visibility can precede image decoding. The gate
  now waits for decoded natural dimensions over 500 px, checks red/orange
  overlay counts against each page manifest, requires real workbook rows, and
  opens a deterministic numeric or categorical chart. It produces one review
  and one Analytics screenshot for every PDF.
- On the dense three-page Survival and Growth notebook form, high semantic F1
  is 0.906 versus low's 0.834. Recall is similar (0.952 versus 0.963), while
  precision improves 0.736 to 0.864. The cost is $0.48323 and the red queue is
  286/1,503 cells (19.0%): high is materially safer, but this handwriting is
  still beyond the point where more model confidence should replace focused
  human review.
