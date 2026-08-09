# Experiment 011 — plain-language architecture, fatigue, and the human boundary

Date: 2026-08-09

## Purpose and status

This checkpoint restates experiments 000–010 as a simple sequence and answers
the product questions they raised: what production actually does, how the new
evaluation was isolated, where the POC and data live, which errors remain, how
much each proposed stage costs, and where adding more AI stops buying reliable
value.

Nothing described here has been deployed. The production backend was not
modified. The extraction POC is a local pipeline in `benchmarks/wide/`; the
only product integration is an optional, backward-compatible review-manifest
view in the existing PWA.

## The story, one experiment at a time

### 1. Audit production and the old score

Production gives a PDF and an extraction prompt to one Codex CLI agent. The
agent renders pages, chooses crops, writes one `v2` worksheet, and may colour
uncertain cells yellow. That is visual self-checking, not evaluation: Codex
does not see a golden workbook and does not compute its own accuracy.

The separate nightly `xlsx_diff.py` was intentionally a loose regression
alarm. It flattened all non-empty cells from every sheet, split them into word
and number tokens, checked recall, and did not penalise extra tokens. Its own
docstring says that it catches crashes or dropped tables rather than certifying
transcription. Consequently it could not detect row/column shifts, page
flattening, modal stamping, or invented values.

### 2. Make the evaluator prove itself before scoring models

We mutated perfect candidates into known failures: blank output, a 10% subset,
modal fill, shifted/swapped columns, shuffled/slipped rows, flattened pages,
duplicates, phantom rows, invented blank fills, and harmless formatting noise.
The old content score could remain 1.000 after a column shift, row shuffle, or
six-page flatten. Exact position F1 fell to 0.133, 0.440, and 0.000.

The replacement evaluation therefore reports separate axes: page and shape,
occupied positions, exact cell values, omissions, false fills, duplicates,
constancy, off-mode accuracy, and modal/null controls. Exact-layout claims use
exact synthetic truth; content-consensus real goldens do not pretend to be
universal layout goldens.

### 3. Establish the exact live baseline

The actual six-page production artifact scored 0.725 on phenology values, made
65 false fills, and flattened six paper pages into one sheet. A no-vision
modal/null control scored 0.783. Production therefore appeared respectable on
the old 0.899 token score while doing worse than a trivial control on the
target columns.

### 4. Introduce an intermediate representation (IR)

The canonical IR gives every item a page, table, row, column, bounding box,
literal primary reading, optional peer readings, confidence, and review state.
Raw provider JSON is saved before assembly. This makes layout and provenance
testable and lets a reviewer return to the exact source region.

### 5. Try tiles and two readers

A generic page first receives a structure-only pass, then a reader sees a page
overview plus four overlapping high-resolution tiles. Gemini 3.6 Flash reached
0.839 phenology, 0.891 overall value accuracy, and 16 false fills. Tiling did
not beat an older simple whole-page 3.6 result (0.854 phenology), so its proven
value is source localization rather than a standalone accuracy gain.

Gemini 3.5 and 3.6 disagreed on 393/3,209 values (12.25%). That small set held
roughly 63% of remaining errors, about five-fold enrichment. The peer is useful
for deciding where a person should look, not for silently changing the value.

### 6. Zoom disagreements and add a third reader

Targeted full-height column strips preserved ruled row order and paired disputed
columns with printed anchors. Gemini 3.1 Pro reread all 393 disputes, but naive
majority fell to 0.813 phenology and direct Pro replacement reached 0.838,
neither beating the unchanged 3.6 primary at 0.839. The extra stage cost $0.454
and 209 seconds summed provider latency. Correlated models are not independent
voters; more tokens can add regressions.

### 7. Build exact synthetic controls and visually reject bad generators

The accepted v5 corpus has 84 forms from 42 pages of 35 real blank ecology
templates, 20,238 ruled cells, 8,178 written values, 14 semantic kinds, clean
and degraded variants, strikes/dots/blanks, merged spans, and six empty
overproduction controls. Its audit reports zero value, bbox, type, overlap, or
merge-contract violations.

Earlier versions were rejected because the generator put person names in
species-code fields, wrote in merged headers, created phantom cells, and lost
multiline/merged structure. This showed that the benchmark generator can cheat
as easily as the model if it is not visually and mechanically audited.

### 8. Use a trusted blank form as a layout oracle

When identity is truly known, vector lines and text from the blank define the
exact merged cell lattice; the vision model only supplies literal handwriting.
Corrected literal F1 was 0.9644 for Gemini 3.6 whole-page over five compatible
forms and 0.9671 for Gemini 3.5. Blanket row bands bought little, cost 71% more
and 40% more latency in the paired pilot, and introduced two false fills.
Page-versus-band disagreement captured most errors and is more useful as a
review selector than an automatic replacement rule.

### 9. Test model diversity without assuming a universal winner

Gemini rankings reversed by form family: 3.5 was slightly stronger on a small
set, but 3.6 was substantially stronger on held-out foliar browse. Claude
Sonnet 5 was strong on one bird page and useful as a diversity reader, but its
CLI overhead/cost was not attributable enough for a production claim. Cursor
GPT-5.4 Mini returned valid schemas yet omitted nearly all handwriting on two
sparse forms (literal F1 0.1053 and 0.0000), so it was rejected.

That Cursor result exposed another evaluator bug: a workbook score of 0.9535
was possible while missing all four handwritten stream values because printed
labels dominated the denominator. Literal handwriting and deterministic layout
are now scored separately.

### 10. Keep ecology downstream of transcription

Hard physical constraints, robust within-form outliers, GBIF taxonomy, and
optional occurrence evidence emit findings but never edit the literal. Five
large GBH outliers were all transcribed correctly, giving outlier status 0/5
precision as an OCR-error detector. In a one-character deletion test, GBIF
suggested 13/29 taxa and all 13 suggestions were the correct canonical taxon.
This supports conservative suggestions, not automatic ecological correction.

### 11. Test safe template routing and find its limit

Geometry alone was rejected because related forms reuse grids. A pixel-support
gate retrospectively accepted 70/84 synthetic forms and was correct on all 70,
but on 78 frozen unknown real pages it falsely nominated a registered template
11 times (14.1%). Dense ruled forms share ink under lighting, crop, binding,
revision, and capture changes.

Pixels may shortlist; independent printed-label agreement must confirm. If any
page abstains or conflicts, the whole document currently uses the generic path.
Only one false candidate has an actual cached structure-label check, so exact
routing remains an experiment rather than a production promise.

### 12. Repair workbook layout after opening it visually

Visual review found missing merged headers, phantom narrow cells, broken copied
styles, and a reviewer that kept showing sheet one while the paper image moved
to later pages. The v5 lattice records row/column spans, merged ranges are
audited, styles are copied safely, and the PWA maps paper page N to worksheet N.
Layout metrics and actually opening the artifact are both mandatory gates.

### 13. Build attention-first review and enforce an immutable primary

The optional PWA view has separate all-cell, transcription-attention, and
ecology-anomaly lenses. Clicking an attention item opens its exact source box.
No peer or ecology suggestion is auto-applied.

A final audit caught two orchestration defects: peer and primary were passed in
the wrong order, and a blank primary was replaced by the first non-empty peer.
Preserving the primary literally, including blank and numeric zero, reduced the
reconstructed artifact from 61 false fills to 16 without changing 0.839
phenology or 0.891 overall value accuracy.

## The proposed system in very simple terms

1. **Make page images.** Keep page identity; never concatenate pages into an
   anonymous token stream.
2. **Map the printed form.** Gemini 3.5 Flash currently performs a
   structure-only pass: fields, tables, physical columns, headers, and boxes.
   It is not asked to infer ecological values.
3. **Ask whether a trusted blank is known.** Pixels only nominate a candidate;
   printed labels must independently confirm it on every page. If uncertain,
   abstain.
4. **Choose layout.** Confirmed new/known forms use the exact blank vector
   lattice. Legacy or unknown forms use the generic canonical grid from step 2.
5. **Read literally once.** Gemini 3.6 Flash is the provisional immutable
   primary. Blank stays blank. No ecological correction is allowed here.
6. **Optionally read a second time.** Gemini 3.5 Flash is the current peer.
   Differences create a small human review queue; they do not change the file.
7. **Run ecology QA separately.** Physical impossibilities, distribution
   outliers, taxonomy and occurrence evidence create a second queue labelled
   “surprising observation,” not “OCR error.”
8. **Deliver a page-shaped workbook and evidence.** Each paper page has its own
   sheet; each flagged cell links to its source box and retains all readings.

The default legacy tier should stop after the primary unless the project buys
the peer-review tier. The third model is not in the suggested automatic path.

## Model fatigue versus human fatigue

**Model fatigue** is shorthand for failure caused by an unbounded agent or by
optimizing the wrong score: dropping late rows, inventing repeated values,
flattening structure, copying a modal pattern, or spending more tokens on
self-consistent but correlated guesses. Models do not experience fatigue as a
person does, but the product symptom is similar. The defenses are bounded
stages, immutable raw evidence, strict schemas, blank/null controls, fixed
denominators, and mutation-tested evaluation—not asking one agent to inspect
and certify itself indefinitely.

**Human fatigue** comes from comparing thousands of spreadsheet cells against
paper, especially when the spreadsheet no longer resembles the form. The
defenses are page-shaped layout, exact source zoom, a 10–15% prioritized queue,
separate transcription and ecology questions, keyboard-friendly correction,
and form-level distributions that reveal patterns without asserting that an
outlier is wrong.

The handoff boundary is explicit: once a peer or zoomed third reader fails to
beat the primary under frozen truth, additional AI is evidence for a human, not
permission to overwrite. A project may instead accept the measured residual
error if its use does not justify review.

## Error taxonomy

The four broad classes in the question are real, but the evaluation found more:

| class | examples | primary defense |
| --- | --- | --- |
| Layout/structure | missing columns, row shifts, page flattening, bad merges | canonical IR, exact lattice, page/shape metrics, visual opening |
| Literal perception | cursive, pencil, dots, strikes, tallies, single-letter codes | primary reader, source zoom, peer disagreement |
| Capture/geometry | skew, crop, shadow, binding edge, perspective, blur | rendering/alignment, abstention, capture guidance; do not assume template identity |
| Ecology/semantics | plausible rare taxon, impossible percentage, real distribution outlier | separate evidence-backed QA; zero silent edits |
| Omission/coverage | skipped rows/pages/metadata, sparse marks missed | exact denominators, page coverage, written-cell recall |
| Commission/hallucination | invented rows, false fills, repeated modal values | blank controls, false-fill metrics, immutable primary |
| Alignment/identity | correct value attached to wrong row, wrong blank template | printed anchors, exact IDs, dual-channel routing |
| Notation semantics | dot means zero, strike means blank, tick/tally conventions | explicit form instructions plus targeted review |
| Output/serialization | valid JSON but lost merged cells/styles/sheet mapping | schema validation, span-aware exporter, browser/workbook tests |
| Calibration/routing | confidence not comparable across models/families | held-out calibration, abstention, per-family reporting |
| Evaluation leakage | goldens influenced by a model, printed labels hide missed handwriting | frozen sets, literal-only scorer, provenance and controls |
| Human interaction | correction attached to wrong page/cell, queue overload | page-qualified keys, exact bboxes, burden/recall targets |

## Cost and the point of diminishing returns

Measured on the six-page eval_09 artifact; provider latencies are summed, not
guaranteed wall-clock service times:

| automatic path | measured cost | provider latency | submitted phenology | role |
| --- | ---: | ---: | ---: | --- |
| Production Codex | subscription, not comparable | 191 s runtime | 0.725 | current production |
| Structure + Gemini 3.6 primary | about **$0.435** | about **216 s** | **0.839** | proposed default candidate |
| Add Gemini 3.5 peer | about **$0.923 total** | about **388 s total** | 0.839, primary unchanged | optional attention tier |
| Add Gemini 3.1 Pro and majority-vote | about **$1.377 total** | about **597 s total** | **0.813** | reject automatic voting |
| Add Pro as direct dispute replacement | about **$1.377 total** | about **597 s total** | 0.838 | reject automatic replacement |

The peer's return is not a higher automatic score; it is concentrating roughly
63% of errors into 12.25% of cells. The third model cost another $0.454 and
made the automatic artifact no better. That is the measured AI-to-human handoff.

Known-template costs are not directly comparable because the saved pilots use
different pages/denominators. In the paired six-form pilot, 3.6 whole-page cost
$0.3083 and row bands cost $0.5283 for only +0.0043 initial exact F1 and two
false fills. Do not buy blanket zoom merely because it is available.

## Three graphs for the product argument

### Graph 1 — automatic accuracy versus cumulative AI cost

Use cumulative cost on x and submitted phenology accuracy on y:

| point | x cost | y accuracy |
| --- | ---: | ---: |
| 3.6 primary | $0.435 | 0.839 |
| + peer, primary remains immutable | $0.923 | 0.839 |
| + Pro direct replacement | $1.377 | 0.838 |
| + Pro majority | $1.377 | 0.813 |

Annotate the peer point “review signal gained, no auto-edit.” The flat and then
falling curve makes the no-more-automatic-AI boundary visible.

### Graph 2 — review burden versus error recall

Plot selected-cell percentage on x and captured-error percentage on y. Include
random review as the diagonal. eval_09 disagreement is (12.25%, ~63%), about
five times the random concentration. Add the soil confidence point (10.6%,
100%) in a different colour and label it “two forms only; uncalibrated.” This
graph explains why focused human review can be cheaper and safer than another
automatic reader.

### Graph 3 — zoom cost versus marginal value

For the paired known-template pilot, compare 3.6 whole-page ($0.3083, 0.9735
initial exact F1, zero false fills) with bands ($0.5283, 0.9778, two false
fills). Show +71% cost and +40% latency for +0.0043 F1. This supports targeted
zoom only after a disagreement or human request, not blanket zoom.

A fourth useful safety graph would contrast the retrospective synthetic pixel
route (70/84 accepted, 70/70 observed correct) with the frozen real-negative
result (11/78 false candidates). It explains why a clean validation result can
collapse under domain shift and why abstention plus independent labels matter.

## Existing legacy forms versus a new marked-form programme

The product can offer two honest service levels rather than pretending all
paper is equally recoverable:

1. **Legacy/random upload.** Use generic structure plus one primary reader,
   optionally a peer. Never force a fingerprint match. Publish the measured
   per-family error range and require focused review when the use case needs
   higher assurance. The current single-form 0.839 is evidence for one failure,
   not yet an “0.8 guarantee.”
2. **Managed future protocol.** After the first legacy form is mapped and a
   person approves its digital schema, generate a clean version carrying a
   stable template ID/QR, revision number, page number, and registration/OMR
   anchors. Subsequent field sheets can route directly to a versioned exact
   lattice. The QR identifies the schema; anchors support alignment; neither
   proves the handwriting value. A measured “0.9” service level must still be
   earned on independent print–fill–scan/phone loops, including worn folders,
   shadows, crop, skew, revisions, photocopies, and partial pages.

This can create a sensible migration incentive: projects that tolerate the
legacy margin keep uploading old forms; projects that need lower layout risk
adopt the generated marked form. The system should always retain the generic
fallback for damaged codes and off-protocol uploads, and should warn rather
than silently applying a near-match template.

## Current production versus POC: exact relationship

They share the existing PWA repository but not the extraction backend path.

- **Production:** the sibling `good-shepherd/agents/formidable/worker.py` runs
  one Codex CLI prompt, uploads `output.xlsx`, pages/crops, and metadata to S3,
  and the deployed API/PWA serves those artifacts.
- **Local extraction POC:** `benchmarks/wide/pipeline_v2.py` orchestrates
  structure, routing, primary/peer readers, canonical output, ecology review,
  and manifests. It contains no AWS/deploy operation and is not called by the
  production worker.
- **PWA bridge:** the existing review page was extended to request an optional
  `formidable-review-v1`. If it is missing or malformed, production behaviour
  falls back to the existing crop/xlsx review. The production API does not yet
  serve that endpoint.

So this is not a second replacement web application, nor a modified production
server. It is a local alternative extraction engine plus a tested optional UI
contract inside the existing PWA.

## Where to inspect the POC and data

### Pipeline/code

- `benchmarks/wide/pipeline_v2.py` — local end-to-end orchestrator.
- `benchmarks/wide/structured_pipeline.py` and `canonical.py` — generic IR and
  literal readers.
- `benchmarks/wide/template_pipeline.py` — known-template exact lattice.
- `benchmarks/wide/integrity_eval.py` and `template_value_eval.py` — layout and
  literal evaluation.
- `benchmarks/wide/review_manifest.py` and `ecology_review.py` — the two review
  lenses.
- `pwa/src/views/JobReviewView.vue` — optional reviewer UI.

### Synthetic data

Inspect `benchmarks/wide/struct_eval_v5_exact_spans/`. Each form directory has
`input.pdf`, `layout_golden.xlsx`, `golden.xlsx`, `ground_truth.json`, and
`provenance.md`. Good examples include the bird point count, NRCS soil, NVS
metadata/understorey, stream habitat, and marine AGRRA forms. Open the PDF and
layout workbook side by side, then inspect JSON boxes/spans rather than trusting
the corpus-level score.

### Real POC artifact

The eval_09 canonical directory contains saved structure/extraction JSON for
six pages, `canonical.json`, primary-only workbooks, the combined `output.xlsx`,
`review_manifest.json`, ecology reports, and an ecology-annotated workbook. The
v2 output directory contains the route decision. These artifacts are local and
currently untracked; the chronological decisions and pipeline code are the
committed checkpoint.

## What must happen before a production switch

The remaining work is not another unbounded model call. It is broader frozen
evidence: human-adjudicated position-linked real truth by form/capture family,
a human legibility ceiling, real positive duplicate captures for routing,
actual label checks for all frozen false candidates, peer-queue calibration,
direct API cost/latency, and a shadow run that never replaces the current user
artifact until both integrity gates and human delta review pass.
