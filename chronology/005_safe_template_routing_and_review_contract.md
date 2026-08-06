# Experiment 005 — safe template routing and a two-lens review contract

Date: 2026-08-06

## Goal

Turn the known-template extraction result into a safe conditional pipeline.
Using exact blank geometry with the wrong form is worse than falling back, so a
recogniser must be allowed to abstain. The output also needs a stable contract
that keeps transcription disagreement separate from ecological anomalies.

## Geometry-only template recognition is rejected

`benchmarks/wide/evaluate_template_geometry.py` evaluates the existing
sector-agnostic rule-line fingerprint over all 80 synthetic forms. A positive
pair is the clean/hard fill of the same blank template page; 3,120 pairs are
different pages.

- 40 true pairs; score range 0.352–0.991.
- 3,120 different pairs; score range 0–0.991.
- At threshold 0.70: 57.5% true-pair recall and 194 false matches.
- At threshold 0.95: 10% recall and still 10 false matches.

Forms from related protocols legitimately reuse grids, so rule geometry is not
an identity. The worst false pairs are NVS recce pages and other related field
forms. Geometry may shortlist candidates but must never route by itself.

The OpenCV dependency was unavailable and repo policy prohibits adding a
dependency without approval. `template_id.py` now has a NumPy/Pillow local-
contrast fallback and a bounded RANSAC comparison. The negative conclusion is
stored in `struct_eval_v4_exact_semantic/template_geometry_eval.json`.

## Blank-pixel support with abstention

`benchmarks/wide/template_match.py` independently measures how much printed ink
from each enrolled blank page is supported by the filled scan. Handwriting is
treated as extra ink rather than evidence against a template. This uses no
ecological semantics and no model call.

Forced top-1 classification gets 75/80 forms correct and top-2 gets 77/80. A
forced classifier is still unsafe. The provisional gate requires:

- top score at least 0.50; and
- margin over the runner-up at least 0.02.

That gate accepts 69/80 forms (86.25% coverage) with 69/69 correct routes in
this corpus. By declared split it accepts 43/52 dev forms and 26/28 test forms,
with no observed wrong route. The rejected 11 forms safely fall back to the
generic pipeline.

This threshold was selected after examining this corpus, so the 69/69 result is
retrospective calibration, not an unbiased production guarantee. It needs an
independent set of phone photos, rotations, partial pages, and revised editions.
The route should eventually require the free printed-label overlap already
available from the generic structure pass as a second channel. Conflicting
pixel and label signals must abstain.

## Review contract

`benchmarks/wide/review_manifest.py` emits `formidable-review-v1` for either
known-template artifacts or the generic canonical representation.

Its invariants are:

1. The primary reader's literal value is always the displayed value.
2. A peer reader contributes an alternative and review priority, never an
   automatic replacement.
3. Every review item includes page and normalized source box when available.
4. Ecology findings live in a separate `ecology_anomalies` view and cannot
   overwrite literal transcription.
5. Blank target cells remain in the contract, so false-fill integrity is
   reviewable and cannot disappear from denominators.

On the bird Sonnet/Gemini pilot, the contract contains 120 writable cells and
only three transcription-review items. Visual audit shows:

- `r3_c5`: Gemini `A`, Sonnet `D`, truth/source `D`;
- `r5_c0`: Gemini `YSTJ`, Sonnet `JJTJ`, truth/source `YJTJ` (both wrong);
- `r6_c3`: Gemini `1`, Sonnet `Y`, truth/source `Y`.

Thus disagreement captures all three primary errors, while correctly refusing
to pretend the third reader always resolves them.

On real eval09, the same contract contains 3,195 table cells, 393 transcription
attention items, and 26 separate ecology findings. The 393-cell queue is the
12.25% disagreement slice already shown to contain most extraction errors;
ecology findings include the correctly transcribed GBH outliers and taxonomy
suggestions in their own lens.

Artifacts:

- `struct_eval_v4_exact_semantic/template_match_eval.json`
- `test__bird_grassland_point_count__p0__v0/template_outputs/review_manifest_gemini36_claude.json`
- `eval_forms/eval_09/canonical_outputs/canonical_v1_full/review_manifest.json`

## Pipeline decision

```text
generic page structure/read
          |
          +-- pixel candidate + printed-label confirmation both pass
          |       -> exact blank lattice + one whole-page literal reader
          |
          +-- otherwise
                  -> generic canonical, one sheet per paper page

either route -> optional peer reader -> disagreement review queue
             -> separate ecology QA -> anomaly/suggestion review queue
```

Do not add QR codes merely to identify one-off forms. A printed stable template
ID could be useful for newly designed repeated protocols, but recognition of
legacy/random uploads must remain content-based and abstaining. OMR anchors may
help alignment on future form designs; they do not solve handwritten reading or
unknown-layout extraction by themselves.
