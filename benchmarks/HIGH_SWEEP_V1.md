# High v1 — all-PDF production gate

Date: 2026-08-11. Candidate commit: `dc72a30` plus documentation commits.

## Decision

High passes the additive production gate as an opt-in workflow, not as a
replacement for low. Across every current PDF it improves aggregate semantic
F1 from 0.887 to 0.923 and precision from 0.854 to 0.939. It has lower recall
(0.907 versus 0.924), and five individual forms regress on raw transcription,
so red review evidence remains essential.

The frozen low workbooks are the control. High provider responses were saved,
then all 14 forms were rebuilt through the same final post-processing code so
late layout fixes could not benefit only selected forms. The independent audit
requires exact PDF/page/workbook parity, one page sheet per paper page, a valid
normalized bbox and xlsx coordinate for every target, matching canonical/xlsx
values, complete review coverage, unique review IDs, decoded page renders and
existing crop files.

## Aggregate result

| Metric | Low | High |
| --- | ---: | ---: |
| Semantic F1 | 0.887 | **0.923** |
| Semantic recall | **0.924** | 0.907 |
| Semantic precision | 0.854 | **0.939** |
| Numeric F1 | **0.965** | 0.958 |
| Word F1 | 0.807 | **0.869** |
| Semantic coded-mark F1 | 0.874 | **0.939** |

- Forms/pages: 14/14 and 68/68.
- Artifact/layout errors: zero.
- Canonical targets including blanks: 18,993.
- Red transcription review: 1,756 cells (9.25%).
- Orange ecology review: 36 cells. A further 630 non-actionable catalogue
  checks are collapsed as information in Analytics and never enter the queue.
- Measured provider cost: $7.4874 total, $0.1101/page. Per-form model cost was
  $0.17336–$1.35275. Fargate compute is additional and uses the same 2 vCPU /
  4 GB size as low.

## Per-form result

| Fixture | Pages | Low F1 | High F1 | Delta | Red / targets | Orange | Model cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| eval_01 | 4 | 0.728 | **0.935** | +0.207 | 102 / 1,114 | 0 | $0.44810 |
| eval_02 | 3 | 0.928 | **0.957** | +0.029 | 27 / 790 | 4 | $0.29441 |
| eval_03 | 3 | **0.856** | 0.840 | -0.016 | 27 / 117 | 0 | $0.17336 |
| eval_04 | 24 | 0.811 | **0.820** | +0.009 | 106 / 1,731 | 8 | $1.35275 |
| eval_05 | 3 | 0.689 | **0.699** | +0.010 | 57 / 466 | 4 | $0.30221 |
| eval_06 | 4 | **0.872** | 0.803 | -0.069 | 71 / 471 | 4 | $0.33454 |
| eval_07 | 6 | **0.970** | 0.953 | -0.017 | 83 / 4,065 | 0 | $1.16571 |
| eval_08 | 3 | 0.834 | **0.906** | +0.072 | 221 / 1,463 | 0 | $0.48323 |
| eval_09 | 6 | 0.947 | **0.948** | +0.001 | 479 / 3,216 | 6 | $0.90338 |
| eval_10 | 3 | 0.574 | **0.749** | +0.175 | 189 / 637 | 0 | $0.47276 |
| eval_11 | 2 | **0.944** | 0.935 | -0.009 | 91 / 1,331 | 0 | $0.41648 |
| eval_12 | 3 | **0.993** | 0.982 | -0.011 | 11 / 1,555 | 0 | $0.45252 |
| eval_13 | 2 | 0.838 | **0.877** | +0.039 | 54 / 842 | 6 | $0.29957 |
| eval_14 | 2 | 0.933 | **0.962** | +0.029 | 238 / 1,195 | 4 | $0.38842 |

The material regression is eval_06: low expands several difficult handwritten
species names more successfully. The peer often contains a useful fuller
alternative and high marks those cells red, but the immutable primary is not
silently replaced. A tested rule that promoted a longer peer prefix changed
only four cells and improved F1 by 0.003, far too little to justify weakening
the provenance contract. The other four regressions are 0.009–0.017.

## Layout failures found by the gate

Token F1 did not detect either failure below because the same token bag was
present in the wrong columns or duplicate rows. Both were caught by page-shaped
IR, review load, source inspection and browser rendering.

- On eval_11, both readers returned 30 rows on each side but their Y scales
  drifted. Guarded ordinal alignment restored the visible 30+30 rows and left
  91/1,331 red cells.
- On eval_12, one reader omitted a leading blank column. The old comparison
  made 933/1,633 cells red and produced 46 rows on a visible 40-row page.
  Response-wide leading/trailing-blank alignment restored 39/40/40 rows and
  reduced review to 11/1,555 without changing token F1.

## Browser and container gates

- All Python contract/evaluation tests pass.
- The production PWA bundle builds.
- 33 Playwright tests pass: 18 product flows, one real smoke artifact, and one
  all-page review/Analytics gate for each of the 14 PDFs.
- Every source page was opened manually. Browser tests additionally decode all
  68 page images, compare exact red/orange overlay counts to the manifests,
  require real workbook rows and open at least one deterministic distribution
  chart per form.
- The high ARM64 worker image builds. The API cross-builds for amd64 and its
  no-AWS routing test proves low still uses task/container
  `formidable-worker/worker`, while high uses
  `formidable-high-worker/high-worker`.

Raw local evidence is intentionally gitignored at
`benchmarks/high_runs/sweep_v1/` (about 539 MB). The reproducible driver is
`benchmarks/wide/run_high_sweep.py`; the independent audit is
`benchmarks/wide/validate_high_sweep.py`; the browser gate is
`pwa/tests/high-sweep-visual.spec.js`.
