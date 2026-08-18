# 019 — Fair High model ROI, reasoning and open-weight gate

Date: 2026-08-12

This experiment answers a correction to 018: the earlier compact Luna and
Gemini tests were useful Mid candidates, but they were **not the full High
architecture**.  This chapter separates agent-model swaps, bounded-reader
swaps, and architectural ablations so their scores are not conflated.

Nothing was deployed or pushed.  All new model calls used API keys.  The
production Low and High images remained untouched.

## 1. What “the same High pipeline” means

High has six distinct steps:

1. a Low-compatible open-ended Codex agent builds an xlsx and crop manifest;
2. a bounded vision call maps each page into a canonical geometry schema;
3. two bounded literal readers independently fill that same schema;
4. deterministic health/coverage logic chooses the primary or a structured
   reader and produces red disagreement evidence;
5. deterministic ecology logic adds orange suggestions but never edits data;
6. the canonical workbook, review manifest and Analytics artifacts are built.

Three comparison classes must therefore be named separately:

- **Exact agent harness substitution:** the same production prompt, Codex CLI,
  tools and container; only the primary model/reasoning setting changes.
- **High role-contract substitution:** the same page images, crops, prompts,
  JSON schemas, two-reader comparison, selector, ecology and UX artifacts;
  provider-native structured API transport replaces Codex CLI for the bounded
  calls.
- **Architecture ablation:** one compact call per page or targeted rereads.
  These are Mid candidates, not exact High substitutions.

The earlier five-form compact Luna/Gemini result belongs to the third class.

## 2. Exact Codex-agent primary substitutions

All rows below used the same six-page `eval_09` input, production High
container, production extraction prompt, render/crop tools, and API-key Codex
CLI.  Durable price reprices captured token buckets at the model developer's
standard list price; reasoning tokens are already included in output tokens.

| Primary | reasoning evidence | F1 | precision | recall | cell ratio | durable cost/form |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Sol, inherited setting | 652 reasoning tokens | 0.884 | 0.850 | 0.920 | 1.051 | $0.409–$0.445 |
| Luna, inherited setting | 1,556 | 0.839 | 0.790 | 0.894 | 1.018 | $0.123–$0.132 |
| Terra, inherited setting | 2,308 | 0.231 | 0.778 | 0.136 | 0.114 | $0.246–$0.265 |
| Sol, explicit none | 0 | 0.662 | 0.520 | 0.912 | 1.402 | $0.627–$0.675 |
| Sol, explicit low | 582 | 0.863 | 0.852 | 0.874 | 0.975 | $0.405–$0.441 |

The Sol-none run is especially important.  It did not merely lose accuracy:
it generated many extra words/labels, cost more because the tool loop became
longer, and the existing High selector accepted it as the primary.  The final
High replay therefore stayed at 0.662 instead of falling back to the 0.925
structured result.  This is a newly measured selector vulnerability.  The
right fix is an independent fabrication/volume/label-coverage gate, not simply
“turn reasoning up.”

The adjacent explicit-low run recovered most of the quality, finished in 135
seconds instead of 291, and cost slightly less than the inherited Sol run, but
remained 0.021 F1 below it.  `none` is therefore rejected; `low` is a plausible
latency setting only if the 14-form gate shows that its lower recall/code F1 is
acceptable.  Reasoning effort is not monotonic cost: removing it made the agent
wander and generate more ordinary output.

The unchanged High selector also accepted the low-reasoning 0.863 primary over
the available 0.925 Gemini structured reader.  Thus both explicit settings
expose the same general issue: the selector's truth-free support checks can
mistake peer support for correctness when the primary and peers share enough
values.  A model/reasoning swap cannot be released without selector calibration
on held-out exact controls.

Luna is the only plausible cheaper primary from this small gate: about 70%
cheaper than Sol for a 0.045 F1 loss.  Terra is dominated by Luna.  On this
fixture, however, all three inherited-setting primaries were rejected when
paired with the saved Gemini structured evidence, so the final delivered
workbook was identical 0.925.  That shows a possible future cost saving:
preflight structure/quality and skip the expensive primary when it has little
chance of being selected.  It does not yet prove the primary can be removed on
the diverse set.

## 3. High role-contract reader substitutions

The exact production High wrapper was replayed over fixed agentic primary and
saved two-reader evidence.  No golden values participate in routing.

| Structured roles, full 6-page form | final route | F1 | red review cells | ecology orange | structured cost |
| --- | --- | ---: | ---: | ---: | ---: |
| current Luna structure + Terra/Luna readers | structured fallback | 0.821 | 851/3,610 (23.6%) | 5 | $0.932 durable list; $0.284 promotional bill |
| Gemini 3.5 structure + Gemini 3.5/3.6 readers, no reasoning | structured fallback | 0.925 | 394/3,500 (11.3%) | 5 | $0.923 standard list |
| saved production High artifact | production selector | 0.943 | 1,156/3,493 (33.1%) | 11 actionable | subscription usage, not metered API cost |

The API replay of current OpenAI roles is not a deterministic reproduction of
the historical subscription run: sampling/transport/defaults differed.  Its
0.821 result must not replace the saved production 0.943 quality baseline.
It is useful for captured cost and for showing that the selector—not any one
reader—created the saved production result.

On page 1, where all candidates were rerun over identical evidence:

| Pair | transport | F1 | red fraction | provider latency | price |
| --- | --- | ---: | ---: | ---: | ---: |
| Gemini 3.5/3.6, explicit low/no actual thinking | direct strict API | 0.989 | 1.05% | 85 s summed | $0.145 |
| same Gemini pair | Codex CLI structured harness | 0.990 | 0.43% | 194 s summed | $0.478 repriced |
| Qwen3-VL 32B/8B Instruct | direct strict API | 0.968 | 65.5% | 218 s summed | $0.009 observed/list-compatible |

The CLI-mediated Gemini result is only 0.001 better but costs about 3.3 times
as much on this page.  Codex injected much larger context and Gemini 3.5 used
20,453 reasoning tokens across structure/reading despite a low request; direct
strict Gemini used zero reasoning tokens.  For bounded literal reading, direct
structured transport is the better architecture.  For the open-ended agent,
the Sol-none failure shows the opposite: reasoning is valuable.

The Qwen pair reads content surprisingly well for its token price but produces
a practically unusable red queue.  Visual inspection shows entire correct rows
painted red because two Qwen sizes differ in spelling, blanks, and formatting.
Normalization/calibration is required before this becomes a human-guidance
system; raw disagreement cannot ship.

## 4. Exact synthetic blank/layout control

The held-out sapling sheet has exact writable-cell and blank truth.  It was not
used in any routing decision.  This control catches shared systematic errors
that a real-form token multiset score misses.

| Pair | geometry match | exact written recall | blank specificity | red queue | error capture | queue precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.5/3.6 | 91.98% | 72.87% | 95.37% | 38.82% | 15.0% | 6.52% |
| Qwen 32B/8B | 59.49% | 1.55% | 87.04% | 43.46% | 73.05% | 100% |

The Qwen spatial score is harmed by severe row geometry shifts; its queue
captures many errors because almost everything is wrong/red.  Gemini produces
a much better workbook, yet two readers agree on shared one-row shifts, so only
15% of known errors are reviewed.  This proves:

- two-model agreement is not a correctness oracle;
- review accuracy needs geometry, blank preservation, row identity and coverage
  signals independent of model confidence/disagreement;
- a high aggregate token F1 can coexist with a product-breaking row shift.

The earlier compact-control result (93.81% exact written recall, 100% blank
specificity on this form, but no captured errors on the hard metadata control)
remains evidence for the same conclusion.

## 5. Open-weight models and tuning

The repository already contains a larger, clean open-weight study.  It should
not be erased by one High-format gate:

- Stock/local Qwen3-VL-8B was the strongest private default in the earlier
  one-shot reader architecture, around 0.89 numeric F1.
- A Qwen3-VL-2B LoRA trained on synthetic forms improved from roughly 0.46–0.48
  to 0.88 numeric F1 in the first broad experiment, and a later density-aware
  version demonstrated that training distribution fixes stopping/fabrication.
- The remaining gap is real cursive/pencil ink and sector vocabulary; synthetic
  hand-print does not close it.
- DeepSeek-OCR 3B was high precision but weak on notation such as tallies,
  dots-as-zero, crossed cells and checkboxes.  A general instruction-following
  VLM is a better base for ecological forms.

The strict unchanged High request did **not** fit the currently capped local
servers: the 2B structure response truncated invalid JSON at the 8k context
limit, and the 8B reader server allows four images while High sent overview
plus declared crops.  No new GPU service was launched.  This is an
architecture/interface failure, not evidence that local perception is bad.
The local route needs a compatible evidence pack (for example overview plus
row bands), constrained row-count output and deterministic stitching, then the
same selector/ecology/review wrapper.

Hosted Qwen 235B returned an empty schema-valid reading in one gate; Gemma 4
stalled/malformed; neither justifies more full-form spend yet.  Qwen 32B/8B is
the first open-weight pair worth further calibration because its page-1 content
F1 is 0.968, but the 65.5% red queue fails the human-fatigue requirement.

Model flexibility tiers:

1. **Best tunable on this DGX:** Qwen3-VL 8B (quality base) and 2B (cheap
   iteration/distillation).  The existing LoRA path is already proven.
2. **Best large open-weight teacher candidate measured here:** Qwen3-VL 32B,
   paired with 8B only after value/status normalization.  A 235B deployment is
   too large for this box and is a hosted or multi-GPU teacher, not a local
   production candidate.
3. **Gemma:** tunable/open and attractive in principle, but this benchmark's
   hosted Gemma 4 call was slow and structurally unreliable; it is behind Qwen
   until a one-page strict-schema gate passes.
4. **OCR-specialists:** useful as a high-precision auxiliary signal, not the
   final notation interpreter.

Alibaba's official international list price for hosted Qwen3-VL Instruct is
$0.16/$0.64 per million tokens for 32B and $0.18/$0.70 for 8B.  These support
the observed low token cost, but self-hosting is not free: dedicated deployment
or owned-hardware utilization, power, operations and latency must be charged.

## 6. Ecology/anomaly guidance is deliberately model-independent

Changing the transcription models does not change the orange algorithm except
through the values it receives.  Current ecology uses:

- generic hard physical domains for percent, pH, latitude/longitude and
  temperature;
- robust within-page/table/column MAD outliers for measurement/count/temp
  columns with at least eight values;
- GBIF name matching, conservative edit-distance spelling suggestions, and
  optional nearby-occurrence context when the form itself supplies latitude
  and longitude.

It never silently edits a value.  On `eval_09`, all offline fair replays found
the same five large GBH values.  These are legitimate review suggestions, not
known transcription errors; no labelled ecological anomaly corpus yet exists,
so ecological precision/recall must not be claimed.  Unit controls verify that
150 C and pH 19 are flagged and that a one-character species repair can be
suggested without rewriting an unrelated common name.

## 7. ROI decision

There is no evidence for replacing production High immediately.

- Production High remains the quality standard: 0.943 on `eval_09`, 0.913
  micro F1 over 14 real forms versus Low's 0.887.
- The best near-High reader substitution is direct no-thinking Gemini 3.5/3.6.
  It gives 0.925 full-form F1 and a smaller red queue at about $0.923/form for
  all structured calls, before primary cost.  It is not yet a dramatic cost
  win, but it is simpler/faster than routing those models through Codex CLI.
- The best cheap content reader remains compact Luna or Gemini Lite with
  deterministic contracts, but the five-form tails and weak error capture
  prevent deployment as High.
- The highest-upside research path is tunable Qwen 8B/2B with template/row-band
  evidence plus independent geometry/blank controls.  Its purpose is not just
  lower token price; it can learn this exact IR and the observed real-ink error
  distribution.  It should first target the strict High contract and review
  queue calibration, not raw token F1.

Before any candidate can replace High it must pass the same 14-real-form gate,
the 84-form exact synthetic gate, and visual review with thresholds for content,
layout, blank invention, geometry, red error capture, red queue precision,
orange false alarms, latency and durable cost.  No single representative page
is a release claim.
