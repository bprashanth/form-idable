# Evaluation and benchmark workflow

This is the entry point for evaluating extraction models, pipeline changes and
review UX. Production runtime code lives in
`../good-shepherd/agents/formidable/high_pipeline/`; the similarly named
`benchmarks/wide/` modules are an experimental workspace and are never copied
into a production image.

The accepted control is recorded in `chronology/015_*`: 14 PDFs, 68 pages,
micro semantic F1 0.913 versus Low 0.887, with 14/14 artifact and browser gates
passing. Do not replace that control with the result of a single form.

## First decide what is changing

| Experiment | What to hold fixed | Minimum useful gate | Production action |
| --- | --- | --- | --- |
| Model or prompt | pipeline, IR, selector, UX and fixtures | API usage + exact-cell controls + five-form diversity set | none until the 14-form gate passes |
| Harness or pipeline | saved model responses where possible, fixtures and UX | artifact validator + paired score/review-capture comparison | promote reviewed code into Good Shepherd, then build High image |
| Review/Analytics UX | saved High artifacts and backend contracts | mocked Playwright all-page visual suite | PWA-only release after local screenshots |
| Backend API contract | old PWA behavior and both workers | backend tests + real Low and High smoke jobs | backend first, backward compatible |
| End to end | frozen Low and prior High | 14 forms / 68 pages + production browser sweep | backend, then PWA, then chronology acceptance |

Do not claim that an API-only model call represents High. Current High contains
an agentic primary, geometry mapping, two literal readers, deterministic route
selection, ecology, workbook construction and review/Analytics contracts.
Architecture ablations and model substitutions must be labeled separately.

## Controls before spending model calls

For every experiment record:

- Formidable and Good Shepherd commit IDs;
- exact fixture IDs and prior output used as control;
- model/provider/version, reasoning setting and authentication path;
- prompt/schema hash or source commit;
- raw input, cached-input, output and reasoning usage per call;
- durable vendor-list cost and actual promotional bill as separate values;
- semantic precision/recall/F1, per-form tails and review-error capture;
- page/table/row/column parity, blank specificity, duplication and omission;
- paths to raw outputs, validators and screenshots.

Include negative controls: known blank cells, deliberately sparse forms,
multi-page forms, repeated values, merged headers, handwritten marginal notes
and forms where a plausible ecological value is intentionally unusual. A model
must not get credit for silently deleting hard cells or changing layout.

## Local promotion ladder

Stop at the first failed stage and record the failure in chronology.

1. **Request contract:** one page from `eval_09`; confirm valid schema, page and
   cell coordinates, usage capture and no blank invention.
2. **Representative form:** all six pages of `eval_09`; compare content,
   geometry and known-error capture with the saved production High result.
3. **Diversity set:** `eval_05,07,09,11,13`; inspect individual tails rather
   than only aggregate F1.
4. **Exact synthetic controls:** require correct physical columns/spans, page
   parity and zero unsupported fills in known blank cells.
5. **All-form gate:** all 14 real PDFs and 68 pages; validate every delivered
   workbook, canonical cell, review box, ecology flag, page render and crop.
6. **Local browser gate:** load saved artifacts through the PWA, visit every
   page and Analytics, assert exact red/orange counts and save screenshots.
7. **Production smoke:** deploy with the appropriate Good Shepherd release
   mode; its automated gate runs real Low and High jobs.
8. **Production all-form/browser gate:** required for model, layout, selector,
   artifact-contract or major UX changes. Record job IDs and screenshots.

Minor copy/style changes do not require paid model replay, but must still build
and run the relevant mocked browser tests.

## Model and harness experiments

API-key cost and model substitutions live in `benchmarks/api_cost/`; start with
its README. Keep production High frozen while experimenting. Raw responses and
run directories are gitignored.

Typical progression:

```bash
python benchmarks/api_cost/unified_pipeline.py --pages 1

python benchmarks/api_cost/run_openrouter_unified.py \
  --reasoning none

uv run --with openpyxl --with pillow --with pymupdf \
  python benchmarks/wide/validate_high_sweep.py \
  --root benchmarks/high_runs/additive_v1
```

Use `--reuse-existing` or saved provider responses for pipeline/selector
ablations so a stochastic reread is not mistaken for an algorithmic gain.
Never tune thresholds on the same form later reported as held-out evidence.

An experiment is ready to promote only when its change is deliberately applied
to Good Shepherd's `high_pipeline/` and the production container is rebuilt.
Formidable benchmark files themselves are not production inputs.

## UX-only visual benchmark

UX work should use saved artifacts, not rerun models. This isolates human-review
behavior from model variance and cost.

```bash
cd pwa
npm install
npx playwright test

HIGH_SWEEP_ROOT=../benchmarks/high_runs/additive_v1 \
  npx playwright test tests/high-sweep-visual.spec.js
```

The all-page suite verifies decoded source pages, workbook rows, red
transcription boxes/cells, orange ecology boxes/cells and read-only Analytics.
Screenshots are written below `benchmarks/high_visuals/` and should be manually
opened at full resolution before accepting layout or review changes.

## API-only production benchmark

Use this when evaluating backend extraction without changing the UI. Mint a
Cognito token as described in `docs/ops.md`, then run:

```bash
FORMIDABLE_API_URL=https://hachry61xe.execute-api.ap-south-1.amazonaws.com/prod \
FORMIDABLE_ID_TOKEN="$TOKEN" \
python benchmarks/wide/run_prod_high_sweep.py \
  --state benchmarks/high_runs/prod_sweep_candidate/state.json \
  --parallel 3
```

Download and score the resulting artifacts with the same frozen evaluator.
This validates API routing and extraction, but not what a human sees.

## End-to-end production browser benchmark

After the API sweep completes and the PWA candidate is live:

```bash
cd pwa
FORMIDABLE_PROD_URL=https://fomoscribe.netlify.app \
FORMIDABLE_PROD_USERNAME="$TEST_USERNAME" \
FORMIDABLE_PROD_PASSWORD="$TEST_PASSWORD" \
FORMIDABLE_PROD_SWEEP_STATE=benchmarks/high_runs/prod_sweep_candidate/state.json \
  npx playwright test tests/production-high-sweep.spec.js
```

This is the acceptance gate for changes spanning extraction and UX. Inspect the
saved review and Analytics screenshots for all forms; passing assertions alone
does not certify that handwriting, table layout or overlays are visually useful.

## Acceptance rules

- Never accept on aggregate F1 alone; report worst-form deltas.
- Never treat token-bag equality as layout correctness.
- Never treat model agreement as truth without blank/geometry controls.
- Ecology remains suggestion-only and is scored separately from transcription.
- Report how much of the known-error set the red queue captures and how much
  human review it demands.
- Use durable vendor prices for architecture decisions; show temporary provider
  discounts separately.
- If extra calls buy a small average gain while worsening tails or attention
  quality, stop and route the uncertainty to a human.

The current Mid/API measurements and exact commands are in
`benchmarks/api_cost/README.md`. The accepted High release evidence is in
`benchmarks/HIGH_ADDITIVE_V1.md`.
