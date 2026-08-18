# 017 — API cost meter and Mid experiment plan

Date: 2026-08-12

## 1. The baseline was frozen before experimentation

No production file, image, task definition or AWS resource was changed. The
baseline is Formidable `e8b075b`, Good Shepherd `7d0d9ff`, and the controlled
production evidence in `benchmarks/high_runs/prod_additive_v1/`.

That evidence is still the quality benchmark: High has micro semantic F1 0.913
versus Low 0.887, precision 0.922 versus 0.854, and a 13.52% red review queue.
It contains 14 PDF forms, 68 pages, 204 structured calls and 3,834,459 combined
subscription tokens. Those combined tokens are not an API bill.

## 2. Why the old token number cannot answer cost

The structured High helper invoked Codex subscription calls and parsed only the
CLI's final `tokens used` total. It did not expose input, cached input,
cache-write, output or reasoning buckets. The agentic primary likewise used an
implicit account/default model. Multiplying the combined total by any one
price would misprice the run, and omitting the primary would understate it.

The cost experiment now reports two numbers:

1. exact structured roles: Luna structure + Terra/Luna literal readers;
2. API-key agentic replay: the same production prompt/tool workflow, pinned to
   GPT-5.6 Sol and run in an isolated Codex home.

The second model pin is explicit because the historical primary did not record
its resolved model. It is a reproducible replay assumption, not false
historical precision.

## 3. The local meter

`run_cli_structured.py` uses the actual High structured Codex 0.147.0 CLI, while
`run_agentic_primary.py` defaults to the production High image's Codex 0.144.4
agent binary. Both authenticate in a temporary `CODEX_HOME`, save complete
JSONL streams and never read the user's subscription `auth.json`. They price
the final cumulative usage event rather than summing cumulative events.

`benchmarks/api_cost/openai_responses.py` adds a direct API-key Responses API
adapter without editing `structured_pipeline.py`. Each saved call retains the
provider's complete raw usage object and the dated price table used. Cache
writes are priced at 1.25x uncached input, cached reads at the documented
discount, and reasoning is reported but not added a second time because it is
already part of output tokens. This lower-overhead path is for Mid; its High
preset is an ablation, not the exact current-architecture meter.

Eight unit tests exercise payload shape, model-specific reasoning compatibility,
nested usage parsing, cache accounting, the no-double-count rule, compact-schema
expansion and missing-peer handling. All runner dry runs pass. A live GPT-5 nano
request reached the Responses API, validated the corrected `minimal` reasoning
shape, and then stopped at `credit_balance_exhausted` before inference.

## 4. The provider audit blocked paid inference cleanly

The available OpenAI key can list models but returns
`credit_balance_exhausted` on generation. Gemini reports depleted prepayment
credits, OpenRouter has used $35.03935 against $35.00, and the discovered
Anthropic key is invalid. No key value was printed or written.

The user required API-key evidence and prohibited falling back to Codex login
for Mid. Therefore no subscription run was substituted and no estimated result
was labelled measured.

## 5. What the Mid experiment will test

The first serious candidate keeps the parts of High that reduce human fatigue:

- one compact GPT-5 nano call maps generic page structure and reads values;
- GPT-4.1 nano independently rereads at most 10% of low-confidence cells;
- the canonical IR aligns outputs and creates genuine red disagreements;
- deterministic geometry, distribution and ecology/GBIF checks remain;
- ecology stays orange and suggestion-only.

A single GPT-5 nano version is included only as an ablation. It is cheaper, but
its confidence flags are not equivalent to independent disagreement and cannot
inherit the review-capture claim.

## 6. Cost feasibility before spending

Using the saved 3,834,459 combined structured tokens only as an intentionally
wide sensitivity analysis, the current structured High portion would be about
$12.37, $19.24 or $26.11 for the 14-form mix if output comprised 25%, 50% or
75% of the opaque total. These are not measured costs and exclude Sol primary.

Even a naive assumption that a unified nano call uses one third of the old
three-call token volume forecasts roughly $1.38-$3.14 per 100 observed-mix
forms as output share rises from 25% to 75%, including a 10% peer allowance.
That does not yet prove the `$1/100` target. The compact row-center schema is
intended to reduce output materially beyond one third; only raw usage can tell
whether it succeeds. The live usage meter is the decision source.

The `$1/100` goal also needs two definitions:

- API model budget: plausible enough to benchmark with nano models;
- total service budget: impossible under the current compute shape, because
  observed 2-vCPU/4-GB ARM Fargate time alone is about $1.46/100 forms.

Thus an accepted Mid could meet $1/100 in model spend while total spend remains
above it. Meeting $1/100 all-in requires replacing the long agentic primary and
downsizing the task after measuring CPU/memory headroom.

## 7. Gates and stopping rule

The experiment progresses from one page, to eval_09, to a five-form diversity
set, then to all 14 PDFs. Promotion requires content precision/F1, exact layout,
review error capture, artifact consistency and visual all-page checks together.
A cheap run that loses layout, fills blanks or creates an unfocused queue fails
even if its token-bag score looks good.

The precise commands, candidate order and numerical gates are recorded in
`benchmarks/api_cost/README.md`.
