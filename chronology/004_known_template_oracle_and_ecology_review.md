# Experiment 004 — known-template oracle, model disagreement, and ecology review

Date: 2026-08-06

## Questions

1. If a blank form is available, can its vector lattice guarantee output layout
   while a vision model is limited to reading handwriting?
2. Does pre-tiling or model diversity improve extraction enough to justify its
   cost, or is it better used to select review regions?
3. Can ecological knowledge safely correct values, or should it remain a
   separate evidence-backed review stage?

## Known-template extractor

`benchmarks/wide/template_pipeline.py` uses the blank template's vector rules
as the layout oracle. ORB aligns the filled scan to the blank, and the model is
asked only for values at enumerated `rN_cN` cells. The renderer can send one
whole aligned page or exact row bands. Every request saves its image, target
boxes, raw response, token/cost metadata, and an exact-lattice workbook.

This is intentionally a conditional path. It is valid only after template
recognition passes; an unknown form must retain the sector-agnostic page
pipeline. Template geometry supplies no ecology values and is not allowed to
fill blanks.

## Six-form paired pilot

The paired set contains clean/hard variants of three held-out template
structures: bird point count, sapling diameter, and soil submission. It has 359
nonblank cells and 800 writable cells including blanks.

| reader | view | exact micro F1 | correct | wrong | omitted | false fills | cost | provider latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.6 Flash | whole page | 0.9735 | 349 | 9 | 1 | 0 | $0.3083 | 133.2 s |
| Gemini 3.6 Flash | row bands | 0.9778 | 352 | 7 | 0 | 2 | $0.5283 | 186.7 s |
| Gemini 3.5 Flash | whole page | 0.9902 | 355 | 4 | 0 | 0 | $0.3590 | 128.7 s |

Blanket bands cost 71% more and add 40% provider latency for +0.0043 micro F1,
while introducing two false fills. They are rejected as the default.

Page-versus-band disagreement occurs in only 15/800 cells (1.875%) but captures
8/10 whole-page errors. Whole-page error rate is 53.3% in the disagreement set
and 0.255% elsewhere: more than 200-fold enrichment. The band reader is only
one net correction better, so disagreement is useful as a review trigger, not
as permission to replace the page answer.

Gemini 3.5 versus 3.6 disagrees in 11/800 cells on this six-form subset and
captures 9/10 3.6 errors. Gemini 3.5 is six net cells better there. That ranking
does not generalise: on a held-out foliar-browse form, 3.6 scores 0.9438 exact F1
while 3.5 scores 0.8876. The seven-form aggregate is 0.9676 for 3.6 and 0.9698
for 3.5, masking the form-specific reversal. No reader is globally dominant;
model selection needs a broader stratified suite.

The reproducible aggregator is
`benchmarks/wide/summarize_template_runs.py`; its current output is
`benchmarks/wide/struct_eval_v4_exact_semantic/template_run_summary.{json,md}`.
It scores all writable cells, including blanks, and derives micro metrics from
counts rather than averaging F1.

## Independent Sonnet 5 pilot

The already-authenticated Claude CLI read the same saved bird-page evidence and
wrote a schema-compatible JSON result. It returned all 120 requested cells,
including blanks, with no missing, extra, or duplicate IDs. Exact F1 is 0.9828:
57/58 nonblank cells correct, one wrong, no omissions or false fills. Against
Gemini 3.6 on that page, three disagreements capture all three Gemini errors;
Sonnet is uniquely correct twice and both are wrong differently once.

The agent session used Claude Sonnet 5 and, after deduplicating repeated JSONL
message records, reports 39,663 one-hour cache-write tokens, 241,511 cache-read
tokens, 10 uncached input tokens, and 6,943 output tokens across extraction and
validation. At the August 2026 introductory API-equivalent rates ($4/M one-hour
cache writes, $0.20/M cache reads, $2/M input, $10/M output), that is about
$0.2764. The CLI used an authenticated subscription, so this is a comparable
API-equivalent estimate, not an asserted invoice charge. Its agentic overhead
is too large for a production cell reader; a direct structured API request is
needed before a fair cost/latency comparison. The locally stored Anthropic API
key returned 401, so no direct Anthropic charge occurred.

Official pricing and model references:

- https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching

## Ecology review stage

`benchmarks/wide/ecology_review.py` is deliberately downstream of literal
transcription. It can emit findings and annotate the canonical workbook, but it
never silently edits a value.

Checks are divided by evidence type:

- hard physical/domain constraints for percentages, pH, coordinates, and
  temperature;
- robust within-form distribution outliers, labelled as anomalies rather than
  transcription errors;
- GBIF taxonomic matching, with confidence and edit distance;
- optional nearby occurrence evidence when coordinates exist.

On real eval09, the within-form check flags five GBH values from 535–710 cm.
Visual/source comparison shows all five were transcribed correctly: 0/5
precision for extraction-error detection. This proves that distribution
outliers deserve a separate reviewer lens but must never be auto-corrections.

The taxonomy pass produces 21 findings and only one medium-strength proposed
normalisation: `Semecarpus travancorica` to GBIF's
`Semecarpus travancoricus` (GBIF confidence 96, edit distance 2). The literal
species extraction was otherwise perfect. On a synthetic one-character-
deletion test of 29 clean species names, it suggests 13 corrections; all 13
resolve to the correct GBIF canonical taxon, for 44.8% sensitivity at 100%
observed taxon precision. This supports a conservative suggestion layer, not a
general spellchecker.

The annotated eval09 workbook is
`benchmarks/wide/eval_forms/eval_09/canonical_v1_full/output_ecology_review.xlsx`.
It retains literal cell values and places 26 findings in an ecology-review
sheet and orange source-cell comments.

Official GBIF references:

- https://techdocs.gbif.org/en/openapi/v1/species
- https://techdocs.gbif.org/en/openapi/v1/occurrence
- https://techdocs.gbif.org/en/data-processing/taxonomy-interpretation

## Decisions

1. Keep the exact-template path: it guarantees lattice fidelity when a trusted
   blank template has been recognised.
2. Use one whole-page reader by default. Do not blanket-tile every page.
3. Surface reader/view disagreement as a high-priority review queue. Do not use
   majority vote or automatic replacement: correlated readers are often wrong
   together, and the third reader did not establish a reliable adjudication
   rule.
4. Keep ecological reasoning downstream and provenance-preserving. Hard
   impossibilities, statistical anomalies, taxonomic suggestions, and
   occurrence evidence must be visibly distinct.
5. Do not pick a universal model from a six- or seven-form aggregate. Rankings
   reverse by form family; expand the held-out suite once provider rate limits
   clear and report family/degradation strata.
6. The reviewer needs both cell-level uncertainty/disagreement and a separate
   form-level anomaly view. They answer different questions.

## Remaining limitations

- Synthetic hard variants use intended pre-degradation values. A sampled human
  legibility ceiling is still required.
- One Sonnet page demonstrates useful provider diversity, not generalisation.
- The exact-template branch requires a calibrated recognition threshold and a
  safe fallback for unknown or revised forms.
- Provider 429 responses stopped the expanded Gemini suite after the foliar
  form. Runs are resumable; repeated retries were intentionally avoided.
