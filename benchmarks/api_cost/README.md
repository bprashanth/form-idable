# Local API-cost experiment

This is additive benchmark tooling. It does not change the deployed Low or High
workers, and experiment outputs remain local.

The follow-up apples-to-apples High model/reasoning/open-weight gate is recorded
in `../../chronology/019_fair_high_model_roi_and_reasoning.md`.  In particular,
the compact Mid results below must not be described as full High substitutions.

## What is frozen

- Formidable baseline commit: `e8b075bf5497bdd36cb5f97797092992b41d3e8a`
- Good Shepherd baseline commit: `7d0d9ff9c6657c7829986680f2afda8d15c0603c`
- Production High evidence: `benchmarks/high_runs/prod_additive_v1/`
- Representative cost fixture: `benchmarks/wide/eval_forms/eval_09/`
  (`TreePhenologyTwoTrails.pdf`, six pages)

Current High is two independently measurable pieces:

1. the Low-compatible agentic primary, whose model was implicit in production;
2. Luna structure plus Terra and Luna literal readers on every page.

The API-key replay pins the agentic primary to `gpt-5.6-sol`. That matches the
host default and current `gpt-5.6` alias, but it is a replay assumption rather
than proof of the model selected by the historical production account. The
structured roles are exact.

## Measured result and two-price rule (2026-08-12)

All experiments used API-key authentication. No Codex subscription login, AWS
deployment, or local model was used. Raw provider usage is saved per call in
ignored local artifact directories.

```bash
set -a
source ../good-shepherd/agents/formidable/.env
set +a

# Exact High structured roles through OpenRouter: 18 calls on eval_09.
python benchmarks/wide/structured_pipeline.py --form \
  benchmarks/wide/eval_forms/eval_09 \
  --schema-model openrouter:openai/gpt-5.6-luna \
  --models openrouter:openai/gpt-5.6-terra,openrouter:openai/gpt-5.6-luna \
  --tag api_high_openrouter_meter_full_v1

# Agentic primary in an isolated API-key Codex home.
python benchmarks/api_cost/run_agentic_primary.py --provider openrouter \
  --model openai/gpt-5.6-sol
```

Every result has two prices:

- **durable estimate** reprices the captured token buckets at the model
  developer's standard list price. This is the planning number;
- **experiment bill** is the actual OpenRouter generation cost/rate at the
  time of the run. It is useful for reconciling the experiment, but never for
  long-term architecture selection when it includes a promotion.

OpenAI's official prices are Sol $5/$30, Terra $2.50/$15 and Luna $1/$6 per
million input/output tokens, with cached reads at one tenth of input and cache
writes at 1.25 times input. During these experiments OpenRouter billed Terra at
$1/$6 and Luna at $0.10/$0.60, with the corresponding discounted cache rates.
OpenRouter explicitly identifies such rates as promotional and changeable.

Audited sources (accessed 2026-08-12):

- OpenAI model comparison/list prices:
  `https://developers.openai.com/api/docs/models/compare`
- OpenAI GPT-5.6 cache-write rule:
  `https://developers.openai.com/api/docs/guides/latest-model`
- Google Gemini Developer API standard pricing:
  `https://ai.google.dev/gemini-api/docs/pricing`
- OpenRouter's warning that provider promotions can change:
  `https://openrouter.ai/collections/discounted-models`

On the six-page `eval_09` representative form:

| component | measured usage | durable official list | experiment bill/rate |
| --- | --- | ---: | ---: |
| Sol production tool-loop replay | 167,146 input (138,267 cached), 6,521 output, 652 reasoning; cache-write bucket omitted | $0.40916-$0.44526 | $0.40916-$0.44526 modeled; no generation cost object |
| Luna structure | 15,323 input, 2,580 cached, 12,725 cache-write, 6,793 output | $0.05694 | $0.00569 actual |
| Terra full literal reader | 43,004 input, 42,986 cache-write, 33,490 output | $0.63673 | $0.25469 actual |
| Luna full literal reader | 43,004 input, 42,986 cache-write, 30,698 output | $0.23794 | $0.02379 actual |
| structured subtotal | 18 calls | **$0.93161** | **$0.28418 actual** |
| full High replay | primary + structured | **$1.34076-$1.37686/form** | **$0.69334-$0.72944/form modeled** |

The CLI exposes exact token buckets but not the OpenRouter generation ID/cost
object, while the structured calls expose both. The Sol range treats its
unclassified non-cached input as ordinary input at the low end and cache writes
at the high end. Therefore `$0.69334-$0.72944` is a token-bucket reconstruction,
not an exact provider charge. An earlier account
balance delta around the Sol run was confounded by failed/unsaved calls and is
not used as a cost bound. For long-term planning, the representative High form
is approximately **$134.08-$137.69/100 six-page forms**, or
**$22.35-$22.95/100 pages**. It
must not be presented as the cost of the frozen 14-form mix, which was not
individually metered.

Every structured call's `.meta.json` and aggregate `run.json` retain the raw
Codex API usage object: input, cached input, cache-write, output and reasoning
tokens. `run_agentic_primary.py` retains the complete Codex JSONL
stream and extracts its final cumulative usage event without summing cumulative
events together. Reasoning tokens are already included in output tokens and are
never charged twice.

`run_structured.py high-structured` is retained as a direct-Responses ablation.
It preserves prompts, schemas and model roles but removes Codex CLI harness
context, so it must not be reported as the exact current High price.

## Mid frontier

The best measured floor is one compact no-reasoning Luna call per page. It
combines generic structure and literal values into the canonical IR, sends an
overview plus four quadrants, and keeps deterministic geometry/contract checks.

On the five-form diversity gate (`eval_05,07,09,11,13`), its experiment bill
was $0.05994 for 19 pages. At the official Luna list price, the same captured
usage is $0.59939: **$11.99/100 forms** or **$3.15/100 pages** at that mix.
The promotional equivalents are $1.20/100 forms and $0.315/100 pages. Micro
semantic F1 was 0.9063 (precision 0.9202, recall 0.8929). Individual deltas
from High were -0.087, -0.011, -0.023, -0.056 and +0.002. This is a useful Mid
floor, but not yet ready to replace High because the tail losses are too large.

The controlled `eval_09` frontier is:

| candidate | durable cost/form | experiment bill | semantic F1 | attention result |
| --- | ---: | ---: | ---: | --- |
| compact Luna, no reasoning | $0.17786 | $0.01779 | 0.920 | 10.34% confidence queue catches 42.98% of aligned cell errors |
| + targeted Luna peer (5%) | $0.28125 | $0.02813 | 0.920 | no additional known errors caught; dominated |
| + targeted Gemini 3.5 Flash Lite peer (5%) | $0.20859 | $0.04852 | 0.920 | strict red capture rises 14.47% -> 20.43%; 14 extra errors found |
| old Gemini 3.5/3.6 full pair | $0.92273 | $0.92273 | 0.920 | repeats the full form three times; poor ROI |
| current High | $1.34076-$1.37686 | $0.69334-$0.72944 modeled | 0.943 | production selector and review UX |

Gemini diversity is real but must be routed. On `eval_09`, 12 of its 14 extra
caught errors came from page 1; it added no capture on pages 2, 4 or 5. A
same-model Luna peer added none. A hard synthetic metadata control also fooled
both Luna and targeted Gemini with confident agreement, proving that “two
models” is not a complete safety mechanism.

Other candidates were stopped on evidence:

- Full Gemini 3.5 Flash Lite was reopened after durable repricing invalidated
  the promotional-Luna comparison. On `eval_09` it cost $0.08909 at Google's
  standard list and improved F1 from Luna's 0.920 to 0.932, especially on
  single-letter codes. Across the diversity gate it scored 0.705 (`eval_05`),
  hard-failed an overlong row on `eval_07`, 0.845 (`eval_11`), and 0.758
  (`eval_13`). The completed four forms cost $0.18206. Visual inspection found
  semantic column shifts, omitted handwriting, and mishandled ditto or
  multi-value cells. It is promising but not a standalone Mid.
- Gemma 4 cost about the same as Luna per page, was far slower, emitted no
  useful uncertainty, then returned malformed JSON before a full artifact.
- Agentic Luna improved hard `eval_05` F1 from 0.659 to 0.690 at $0.07416
  durable list cost ($0.00742 promotional), still below High's 0.746. On a
  second hard form, `eval_11`, it regressed compact Luna from 0.894 to 0.729,
  overproduced 1.45 times the golden cell count, and cost $0.13667 at list
  ($0.01367 promotional), versus compact Luna's $0.06431 list cost. It is not a
  general Mid default; any future use requires a truth-free route that predicts
  its narrow wins without increasing fabricated content and human fatigue.

## Recommended Mid architecture shape

1. The first-pass model is not selected yet. Compact Luna passes the five-form
   artifact gate but costs $11.99/100 forms at list and misses tail content;
   Gemini is cheaper and better on `eval_09`, but fails the diversity gate.
2. Deterministic IR/geometry/coverage contract. Never guess how to delete an
   overlong row; hard structural ambiguity escalates to human/High.
3. Human attention includes model low-confidence cells plus every contract
   repair. Do not paint untouched one-reader cells green as if verified.
4. A diverse peer only on pages/regions selected by calibrated risk:
   categorical marks, metadata-heavy layouts, missing trailing values,
   row/column count mismatches, or coverage gaps. Do not run it on every page.
5. Keep ecology deterministic, orange, suggestion-only, and after literal
   transcription. It adds no model cost in the current implementation.
6. Human review is mandatory for overlong rows, zero coverage, or model/model
   agreement that fails deterministic domain/structure checks.

The exact-cell controls explain the safety rule. On the held-out sapling form,
compact Luna matched 98.8% of writable geometry, read 93.81% of written values
exactly, and produced zero false fills across 152 known blank cells. On a hard
metadata form, written recall fell to 42.86% while blank specificity remained
100%; neither Luna confidence nor a targeted Gemini peer caught those errors.
Another held-out understorey form produced overlong rows and was correctly
failed rather than “repaired” by deleting an unknown value.

## Promotion status

**Do not deploy yet.** At durable prices the experiment does not meet the ideal
$1/100-form target, and it also failed the individual-form quality and
review-capture gates. The best current research direction is to compare cheap
vendor-list readers as the first pass, then use compact Luna or cropped Gemini
only where IR/coverage evidence says risk is high. Full Gemini wins the
representative form but fails the diversity gate, so model identity cannot
replace the gate. Agentic Luna is now a rejected default, not a recommended
general second reader. Do not add a third general full-form model.

## Reproduction ladder

Do not spend the all-form budget immediately.

1. Run the unified targeted candidate on eval_09 page 1 as a request-shape and
   schema test:
   `python benchmarks/api_cost/unified_pipeline.py --pages 1`.
2. Run it on all of eval_09 and measure content, layout and review capture. It
   uses a second model only on a maximum 10% of low-confidence cells.
3. If it passes, run both candidates on eval_05, eval_07, eval_09, eval_11 and
   eval_13. These cover regular tables, long census layouts, phenology codes,
   seed/seedling notation and a sparse two-page form.
4. Only then run the 14-PDF / 68-page gate and visually open every page.

The live command is `run_openrouter_unified.py`; raw API usage and local outputs
are gitignored. Use `--reasoning none`, then add the peer only with a controlled
ablation from copied primary responses and `--reuse-existing`.

## Acceptance gates

Mid is not “best cheap model.” It is accepted only if the same run passes all
of these:

- aggregate semantic F1 no more than 0.03 below production High;
- no individual fixture falls more than 0.08 below production High;
- exact synthetic layout has no missing pages/tables/physical columns and no
  silent row or column shifts;
- precision remains at least 0.88, preventing cheap-model blank filling;
- red review is at most 20% of targets and captures at least 55% of known
  literal errors on exact-cell controls;
- red and orange remain separate; ecology never edits transcription;
- 14/14 PDFs, 68/68 pages pass artifact validation and browser visual review;
- marginal cost is reported against quality/error capture using vendor list
  price; $1/100 is ideal, while a higher price can be accepted only for a
  material tail-quality gain. Promotional provider cost is a separate column.

For cost normalization, report both `$ per 100 jobs at the frozen 14-form
mix` and `$ per 100 pages`. Never multiply the six-page eval_09 price by 100
and call it a representative 100-form price.

The `$1/100` threshold above is a model-API target. At the observed production
mean runtime, the existing 2-vCPU/4-GB ARM Fargate task alone is approximately
$1.46/100 forms. A total-service target below $1/100 therefore requires a
separate compute redesign (smaller task and shorter, non-agentic runtime) and
must not be claimed from model price alone.
