# Experiment 008 — pixels nominate; labels must decide

Date: 2026-08-06

## Pre-registered question

The v5 public-template corpus suggested that a pixel-support score of 0.50 and
a top-two margin of 0.02 could nominate exact-template candidates. Those
thresholds were fixed before opening this result. I then ran them once over 24
frozen real partner documents (78 pages), none of which belongs to the public
template registry. Seven documents are original phone photographs.

The test asks about false routing, not transcription. Its forms were already in
the repository, but they were not used to choose these thresholds.

## Result

The pixel channel falsely nominated a known template on 11/78 pages (14.1%).
Several scores were high:

- a real field photo was matched to a narrative bird protocol page at 0.792;
- three unrelated dense tables were matched to the same stream-habitat page at
  0.726–0.768;
- a phenology table was matched to a bird form at 0.621.

I rendered every accepted source page beside its proposed blank and inspected
the montage. All eleven are visibly different layouts. This is not an
annotation ambiguity.

This result is the required negative control: ruled tables share enough ink
support that a pixel score and margin cannot establish template identity.

## Independent channel

`pipeline_v2.py` already requires a generic structure pass to confirm printed
labels. For the only false candidate with a cached structure output (eval_09
page 5), that gate rejected the bird-form candidate: label score 0.255, zero
margin, wrong top template.

As a weaker diagnostic, I tokenised existing xlsx outputs for all eleven false
candidates. The label scorer rejected 11/11. These are explicitly labelled
proxies: some workbooks contain document-wide content and handwriting, so they
do not validate the structure-model gate.

## Decision

1. Pixel support remains a shortlist mechanism only. Its frozen-negative false
   candidate rate is 14.1%, not an identity precision claim.
2. Exact routing requires both pixel nomination and independent printed-label
   confirmation, and the whole document falls back if any page abstains.
3. The exact-template branch remains experimental until we collect real
   positive duplicate captures and cached structure outputs for the remaining
   false candidates. Synthetic same-template accuracy is insufficient.
4. Do not tune the pixel thresholds on this frozen cohort. Future routing
   changes must be compared against this unchanged one-shot result.

Reproduce without provider calls:

```bash
PYTHONPATH=benchmarks/wide python3 benchmarks/wide/frozen_routing_eval.py \
  --evals benchmarks/wide/eval_forms \
  --corpus benchmarks/wide/struct_eval_v5_exact_spans \
  --templates benchmarks/wide/downloads/templates \
  --manifest benchmarks/wide/template_registry_v2.json \
  --output benchmarks/wide/struct_eval_v5_exact_spans/frozen_routing_v2.json
```
