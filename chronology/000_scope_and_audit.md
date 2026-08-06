# Experiment 000 — scope and initial audit

Date: 2026-08-06

## Goal

Build and benchmark a local successor to Formidable's current production
extractor. The successor may change both repositories and use paid API models,
but it must not deploy to AWS and must not use local models yet.

The system must improve actual cell recovery and reviewability, not merely a
position-blind token score. It should remain sector-agnostic through extraction,
with any ecology-specific inference isolated as an optional, measurable stage.

## Guardrails

- Start from the exact production prompt/harness baseline.
- Preserve the 24 frozen real-form goldens; never tune to individual answers.
- Use API models only for now and track every paid call.
- Evaluate omissions, false fills, row/column drift, page coverage, constancy,
  and layout/provenance separately.
- Check real page images visually as well as scoring workbooks.
- Keep ecology validation separate from visual transcription and retain the
  original reading whenever a validator suggests a correction.

## Initial observations

1. Production is a single Codex CLI agent with a crop utility and a prompt that
   requires structural completeness but makes value verification discretionary.
   It emits one workbook plus crop/page manifests.
2. `wide_diff.py` is a token-multiset metric. It cannot detect transposed or
   shifted cells, missing page boundaries, row renumbering, or modal stamping.
3. `cellacc.py` fixes that for eval_09 only by relying on its globally unique
   Tree No and hard-coded 15-column schema.
4. The 24 real goldens are content-consensus artifacts, not universal layout
   goldens. Several are flattened or unusually shaped and none preserve merged
   cells. They can support content claims, but cannot alone certify layout.
5. The repository already contains 76 exact synthetic forms filled into 38
   real blank ecology templates (`struct_eval/`) and a broader synthetic form
   generator. These should be reused and extended rather than replaced.
6. The existing working trees contain many pre-existing untracked files even
   though the active branches themselves have no tracked modifications. Those
   files are treated as user-owned and will be preserved.

## Evaluation decision

Use three distinct evidence tracks:

1. **Real-form content:** alignment-aware positional/record scoring, null
   controls, coverage, false-fill, and constancy checks.
2. **Exact synthetic structure:** page/table/row/column and cell-coordinate
   scoring on template-filled and generated forms with exact ground truth.
3. **Real-form reviewability:** visual page checks plus source-linked cell or
   region provenance in the candidate artifact.

No single aggregate number will be presented as proving all three.

## Next experiment

Build evaluator integrity tests using deliberately corrupted candidates
(blank output, modal fill, shifted columns, shuffled rows, duplicate rows,
flattened pages, and invented cells). An evaluator is accepted only if each
corruption fails for the expected reason before it is used to compare models.
