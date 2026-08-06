# Experiment 006 — span-aware exact layout and the local v2 orchestrator

Date: 2026-08-06

## Why v4 was superseded

The known-template extractor scored well on exact coordinates, but exporting
and visually opening its workbook exposed two structural defects that the v4
golden shared and therefore could not penalise:

1. merged physical cells were written only at their starting Excel coordinate,
   leaving phantom narrow gaps instead of `colspan`/`rowspan` merges;
2. tall/multiline headers whose internal rule stopped at the header boundary
   were absent from both the golden and output.

The first merged bird workbook was also horizontally split and unstyled after
multi-page assembly. Cause: OpenPyXL internal style IDs are workbook-local; the
merger copied `_style` IDs instead of public style components. It now copies
font/fill/border/alignment/protection and page setup explicitly.

These were visual/product failures despite good token scores. v4 remains the
record of earlier value-reading experiments but is not used for new layout
claims.

## Span-aware vector lattice

`gen/fill_template.py` now retains the established three-sided elementary-cell
detector and adds only strict four-sided merged faces that do not overlap an
existing cell. Every cell records `rowspan` and `colspan`; exact goldens contain
the matching Excel merged ranges. Multiline vector text is ordered by y then x
instead of x alone.

The strengthened `audit_synthetic.py` checks:

- unique start coordinates and valid normalized boxes;
- exact value equality between JSON and workbook;
- semantic value contracts;
- positive integer row/column spans;
- no atomic-coordinate overlap between spans;
- exact equality between declared spans and workbook merged ranges.

Accepted corpus: `benchmarks/wide/struct_eval_v5_exact_spans/`.

- 84 forms from 42 real blank-template pages (35 files).
- 20,238 ruled cells and 8,178 written cells.
- 14 semantic kinds, including 456 species, 1,129 Y/N, 668 percentages,
  524 decimals, and 223 dates.
- 0 value, bbox, type, span-overlap, or merge-contract violations.
- Six deliberately empty pages remain blank-overproduction controls.

The bird workbook now renders as one landscape page with the species header,
comments header, grouped 0–5/5–10 minute headers, physical subcolumns, all 20
data rows, borders, shaded print, blue literal values, and no phantom gap.

## Model evidence carried forward and refreshed

Bird, sapling, and foliar v5 pages are pixel-identical to v4 and have identical
writable target sets. Their raw saved model responses were reused, while the
workbooks and scores were rebuilt against span-aware goldens. Soil gained 63
previously invisible writable cells and changed pixels, so no old soil response
was reused.

On the five compatible page forms:

| reader/view | forms | exact micro F1 | correct | wrong | omitted | false fills | known cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.6 whole page | 5 | 0.9682 | 396 | 9 | 8 | 0 | $0.3366 |
| Gemini 3.5 whole page | 5 | 0.9707 | 397 | 8 | 8 | 0 | $0.3848 |
| Gemini 3.6 row bands | 4 | 0.9813 | 314 | 5 | 0 | 2 | $0.4545 |

Whole-page 3.6 versus bands disagrees on 13/708 writable cells (1.84%) and
captures 87.5% of its errors; the error rate is 53.85% inside disagreement and
0.14% in agreement. The earlier decision stands: use disagreement to target
review, not blanket bands or automatic replacement.

Fresh Gemini soil calls returned persistent 429 after the bounded 10/20/30
second retries; no response or reported charge resulted. Two Claude CLI reads
were run with a $0.45 maximum each. Both returned all 109 exact IDs with no
schema/ID violations. Session token logs were contaminated by unrelated
internal records, so only the budget upper bound is retained; actual cost and
latency are unknown.

Claude soil results:

| condition | exact F1 | correct | wrong | omitted | false fills |
| --- | ---: | ---: | ---: | ---: | ---: |
| clean | 0.9296 | 33 | 2 | 1 | 0 |
| hard photo/degradation | 0.9014 | 32 | 2 | 1 | 2 |

Visual audit confirmed every error. Clean failures were `111`→`/11`, a dot
(meaning zero) omitted, and `8.4`→`6.4`. Hard failures were two letter
confusions, one omission, and two strike-throughs incorrectly emitted as
`~`/`—`. They are reading/notation failures, not layout loss.

A provisional single-reader queue at confidence ≤0.80 selects 4/109 clean
cells and 19/109 hard cells. `review_capture_eval.py` shows it captures all
3 clean and all 5 hard errors: combined error recall 100%, queue precision
8/23 (34.8%), and review burden 23/218 (10.6%). This is promising but calibrated
on only one model/form pair; disagreement remains the preferred signal when a
peer reader is affordable.

## Updated safe routing

On v5, geometry-only fingerprint scores still overlap completely:

- 42 true pairs score 0.178–0.992;
- 3,444 different pairs score 0–0.991;
- threshold 0.95 gives 11.9% recall and still 10 false matches.

The pixel-support matcher forced top-1 gets 76/84 and top-2 gets 79/84. The
provisional score ≥0.50 and runner-up margin ≥0.02 abstention gate accepts
70/84 (83.3%) with 70/70 correct observed routes: 45/56 dev and 25/28 test.
This is retrospective calibration and still requires an independent phone-
photo set.

`template_labels.py` provides the second required channel: IDF-weighted overlap
between printed labels from the generic structure stage and vector text from
the candidate blank. On real unknown eval09, five pages fail pixel matching;
page 5 passes pixels but its printed-label score is only 0.255 with zero margin,
so the entire six-page document safely remains generic.

## Local v2 orchestrator

`benchmarks/wide/pipeline_v2.py` now ties the evidence-backed pieces together
without any AWS code or operation:

1. cache one sector-agnostic structure pass per paper page;
2. score the blank registry by pixel support;
3. confirm the candidate independently from printed labels;
4. use the exact span-aware template path only if every page passes both gates;
5. otherwise reuse the cached structure in the generic two-reader pipeline;
6. emit literal workbook/canonical data, `formidable-review-v1`, and a separate
   ecology report.

Mixed known/unknown documents currently take the all-generic route. This gives
up an optimisation but avoids a brittle merged coordinate contract. The
structure response is cached with request metadata, so fallback does not make
the same model call twice.

The full known branch was exercised from cached bird evidence with zero new
provider calls. It produced `route.json`, a one-page span-aware `output.xlsx`,
`review_manifest.json`, `ecology_review.json`, and `run.json`; the review
manifest validator found no duplicate IDs or primary-value overwrites.

## Decisions

1. v5 is the accepted exact-layout corpus. v4 is historical only.
2. Visual workbook export is a mandatory gate in addition to exact metrics.
3. Exact routing requires both pixel and printed-label channels and may abstain.
4. Whole-page reading remains the default; a peer reader buys a small,
   concentrated review queue. Bands are an optional diagnostic reader.
5. Low-confidence review is a useful single-reader fallback but not yet a
   cross-model calibrated confidence score.
6. Do not edit or deploy the production worker yet. The local pipeline still
   lacks an independent routing photo set and a complete refreshed multi-family
   model suite because Gemini is rate-limited.
