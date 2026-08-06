# Experiment 010 — system decision and production cut

Date: 2026-08-06

## Outcome

The local prototype is materially better than the exact live production
artifact on the reported phenology form, while being more honest about what it
does not know:

| eval_09 system | phenology accuracy | modal-null | false fills | page layout |
| --- | ---: | ---: | ---: | --- |
| live production Codex | 0.725 | 0.783 | 65 | 1 sheet for 6 pages |
| local generic primary (Gemini 3.6) | **0.839** | 0.783 | **16** | 1 sheet per page |

This is +0.114 absolute phenology accuracy and 49 fewer false fills (75.4%
reduction). It also preserves page/table/row/column identity and source boxes.
The evidence is still one real six-page form, so this proves a better local
candidate for the reported failure—not universal production superiority.

The primary-only generic path cost about $0.435 in measured Gemini-equivalent
API charges and 216 seconds summed provider latency for six pages: $0.088/42 s
for structure plus $0.347/173 s for the 3.6 readings. Production took 191
seconds and reported 52,368 Codex tokens; subscription cost is not comparable.

## Proposed system

```text
input PDF/images
      |
      v
sector-agnostic page structure (cached)
      |
      +-- pixel candidate ----+
      |                       |
      |                printed-label confirmation
      |                       |
      |                 both pass on every page?
      |                    /             \
      |                  yes              no / mixed
      |                  |                    |
      |          exact blank lattice     generic canonical grid
      |                  \                    /
      +------------------- primary literal reader
                                  |
                         optional peer reader
                                  |
                   disagreement/confidence review queue
                                  |
                   separate ecology plausibility queue
                                  |
                    page-shaped xlsx + source evidence
```

The first reader in the model list is the immutable primary. A regression test
now enforces this: the earlier orchestrator accidentally passed peer before
primary on the generic fallback. Peer and ecology stages may add evidence but
cannot overwrite the literal.

## Stage-by-stage decision

| stage / idea | measured evidence | incremental cost / latency | decision |
| --- | --- | --- | --- |
| Integrity and adversarial scoring | shifts, shuffles, flattening, subsets, duplicates, phantoms, modal fill and blank invention all fail for the intended reason | local only | **required gate** |
| Generic canonical primary | eval_09 3.6: 0.839 phenology, 0.891 value, 16 false fills versus production 0.725/65 | about $0.435 and 216 s for 6 pages including structure | **production candidate after broader frozen eval** |
| Overview + four overlapping tiles | canonical tiled 3.6 scored 0.839 versus older simple page 0.854; no standalone accuracy gain | included in $0.347 reader cost; more image tokens | **keep for provenance now; ablate overview-only next** |
| Gemini 3.5 peer | 393/3,209 disagreements (12.25%) captured about 63% of first-reader errors, roughly 5× enrichment | +$0.488 and +172 s on eval_09 | **optional quality tier / review selector** |
| Gemini 3.1 Pro targeted reread | $0.454/209 s; majority 0.813 phenology and direct replacement 0.838, both no better than 3.6 alone at 0.839 | +$0.454 and +209 s | **reject as default; never auto-vote** |
| Exact known-template lattice | corrected literal F1 0.9644 for 3.6 whole-page on 5 forms; exact spans/merges and source cells | $0.3366 total across 5 saved runs | **experimental opt-in** |
| Blanket row bands | earlier +0.0043 workbook F1 for +71% cost/+40% latency and two false fills; corrected four-form literal F1 0.9799 but non-identical denominator | expensive | **reject as default; use only as disagreement reader** |
| Pixel template recognition | retrospective v5 70/84 accepted, 70/70 correct; frozen unknown real pages falsely nominated 11/78 (14.1%) | local only | **shortlist only, never identity** |
| Printed-label confirmation | rejected the eval_09 false pixel candidate; xlsx-token proxies rejected 11/11, but only 1 actual structure-gate negative exists | reuses cached structure | **required, insufficiently externally validated** |
| Geometry-only recognition | v5 true and false scores overlap to 0.992/0.991; at 0.95 only 11.9% recall and 10 false matches | local only | **reject** |
| Claude Sonnet 5 diversity | bird literal F1 0.9828 and useful disagreements; soil literal F1 0.8776; CLI cost attribution unreliable | bird API-equivalent estimate $0.276; soil ≤$0.45/page budget only | **research reader, direct API test required** |
| Cursor GPT-5.4 Mini | metadata literal F1 0.1053; stream form 0.000 despite exact JSON/IDs | subscription cost unavailable | **reject for transcription** |
| Ecology hard bounds/outliers/GBIF | five GBH outliers were 5/5 correctly transcribed (0/5 as OCR-error detector); deletion test suggested 13/29 taxa, 13/13 correct canonical taxon | local + optional GBIF network | **separate suggestions only, zero silent edits** |
| QR/OMR redesign | not benchmarked; one-off uploads gain little from a fingerprint. Stable IDs/anchors could help future repeated protocols, not legacy/random forms | form redesign/field operations | **do not require; evaluate only for new repeated forms** |

The known-template numbers in experiment 006 included deterministic printed
labels and are not model-reading headlines. Experiment 007 supersedes them
with source-aware literal F1. Layout integrity and literal reading remain two
separate scores.

## Known-template corrected reader evidence

Saved provider responses were rescored without calls:

| reader / view | forms | literal micro F1 | correct | wrong | omitted | false fills | known cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.6 page | 5 | 0.9644 | 352 | 9 | 8 | 0 | $0.3366 |
| Gemini 3.5 page | 5 | 0.9671 | 353 | 8 | 8 | 0 | $0.3848 |
| Gemini 3.6 bands | 4 | 0.9799 | 292 | 5 | 0 | 2 | $0.4545 |
| Claude Sonnet 5 soil | 2 | 0.8776 | 43 | 4 | 2 | 2 | unknown |

The near-tie between Gemini readers is not a global ranking. On held-out
foliar browse, 3.6 literal F1 was 0.9265 versus 0.8529 for 3.5, reversing the
other small-form results. Use 3.6 as provisional primary and 3.5 as peer; do
not claim universal dominance.

## Synthetic/data conclusion

The accepted v5 corpus has 84 forms from 42 pages of 35 real blank ecology
templates: 20,238 cells, 8,178 written values, 14 semantic kinds, and zero
value/bbox/type/span/merge audit violations. It includes blanks, strikes, dots,
merged headers, sparse forms, clean/hard variants, and six blank controls.

It is useful for exact structure and anti-fabrication tests. It is not a human
legibility oracle and remains weaker than true field cursive/pencil. No range
from the generator is used to “correct” a real observation. The 24 real form
goldens remain frozen and are never training data.

## Reviewer/product decision

The local PWA prototype consumes optional `formidable-review-v1` and exposes:

- all page-shaped cells, with the correct workbook sheet per paper page;
- a transcription queue with exact bboxes, literal primary, and peer
  alternatives;
- a separate ecology queue with anomaly/taxonomy evidence and an explicit
  no-change notice.

The queue targets attention instead of pretending to adjudicate. On eval_09,
12.25% of cells contained roughly 63% of errors. On two soil forms, confidence
≤0.80 selected 10.6% of writable cells and captured 8/8 errors, but that
threshold is not calibrated beyond one model/form family. The PWA build and
15 browser tests pass; the backend endpoint is intentionally not wired or
deployed.

## Production cut line

Safe to port into a backend feature branch now, without enabling it for users:

1. integrity metrics and mutation regression tests;
2. canonical page/table/row/column representation and anti-fabrication prompt;
3. explicit primary-first reader ordering and cached raw provider evidence;
4. `formidable-review-v1` generation and optional PWA consumption;
5. separate ecology findings with a hard invariant of no literal overwrite.

Keep behind a disabled experiment flag:

1. exact-template routing and lattice extraction;
2. paid peer readers;
3. GBIF online lookups.

Do not port as automatic behavior:

1. pixel- or geometry-only template routing;
2. third-reader majority replacement;
3. blanket tiling/bands on every known page;
4. ecology-driven value replacement;
5. GPT-5.4 Mini transcription;
6. QR/OMR requirements for arbitrary legacy uploads.

## Evidence required before any production switch

1. **Broader real accuracy:** human-adjudicated, position-linked truth for a
   stratified frozen subset of at least the main scan/photo, sparse/dense,
   numeric/code/cursive families. Report per-family omissions, false fills,
   coverage and layout, not only a pooled F1.
2. **Human legibility ceiling:** two independent humans label a random sample
   of hard synthetic and real field cells as readable/value/illegible. Model
   errors on unreadable cells must not be counted as avoidable accuracy loss.
3. **Routing positives:** multiple independent phone captures of the same blank
   templates, including crop, skew, revision and partial-page conditions.
4. **Routing negatives:** run actual structure-label confirmation on all 11
   frozen pixel false candidates plus new revised/lookalike forms. Require zero
   observed false exact routes; coverage may abstain.
5. **Review calibration:** on held-out forms, target ≥60% error recall at ≤15%
   transcription review burden before making the peer tier the default.
6. **Cost/latency:** compare primary-only and peer tiers per paper page under
   direct provider APIs. CLI-agent token accounting is not sufficient.
7. **Shadow run:** produce v1 and v2 artifacts side-by-side, never replacing
   the user-visible workbook until integrity gates pass automatically and a
   human has reviewed the delta.

## Reproducible local entry points

```bash
# Exact synthetic contract
python3 benchmarks/wide/audit_synthetic.py \
  benchmarks/wide/struct_eval_v5_exact_spans

# Frozen unknown-template safety test (no provider calls)
PYTHONPATH=benchmarks/wide python3 benchmarks/wide/frozen_routing_eval.py \
  --evals benchmarks/wide/eval_forms \
  --corpus benchmarks/wide/struct_eval_v5_exact_spans \
  --templates benchmarks/wide/downloads/templates \
  --manifest benchmarks/wide/template_registry_v2.json

# Local route from cached structures (no provider calls)
cd benchmarks/wide
python3 pipeline_v2.py eval_forms/eval_09 \
  --templates downloads/templates \
  --registry template_registry_v2.json \
  --tag canonical_v1_full --reuse-structure --route-only

# Frontend
cd ../../pwa
npm run build
npx playwright test
```

No AWS deployment, backend mutation, local-model/GPU job, or push was performed.
