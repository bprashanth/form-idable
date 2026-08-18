# 018 — OpenRouter cost frontier and Mid result

Date: 2026-08-12

## 1. The API-key blocker was removed without touching production

The user funded the existing OpenRouter key. Balance verification showed
$14.96065 available before the experiment. Every inference used that API key;
no Codex subscription login, local model, AWS deployment or push was used.
Formidable stayed at baseline `e8b075b` and Good Shepherd at `7d0d9ff`.

The harness now retains every structured call's raw OpenRouter usage object,
including prompt, cached, completion and reasoning tokens, provider name,
generation ID and actual billed cost. Codex 0.144.4 was also configured as a
custom OpenRouter Responses provider, allowing the real production tool loop
to run with API-key accounting.

## 2. Current High was metered on one representative six-page form

`eval_09` is TreePhenologyTwoTrails, the form used throughout earlier High
evaluation. The exact structured roles cost $0.28418 for 18 calls: $0.00569
Luna structure, $0.25469 Terra reader, and $0.02379 Luna reader. Terra was
89.6% of the structured bill.

The Sol agentic primary used 167,146 input tokens, of which 138,267 were
cached, plus 6,521 output and 652 reasoning tokens. Official OpenAI pricing
puts it at $0.40916-$0.44526 because the Codex event omits the cache-write
bucket. Repricing all three structured roles at official OpenAI
list prices, including 1.25x cache writes, gives $0.93161. The durable full-High
estimate is therefore **$1.34076-$1.37686 for this form**. The experiment's
discounted OpenRouter rates imply $0.69334-$0.72944, but the CLI did not return a generation cost
object for Sol, so that total is modeled rather than an exact provider bill.
An account-balance delta around the run was confounded and is not a bound.

The structured pair alone scored 0.821 semantic F1; Sol primary alone scored
0.884; production High scored 0.943. This confirms the production quality is
from complementary selection, not any one reader.

## 3. Compact Luna created a real Mid floor

One no-reasoning Luna call per page consumed the overview plus four quadrants
and emitted generic structure and literal values together. On `eval_09` its
captured usage costs $0.17786 at official OpenAI list and was billed $0.01779
under the OpenRouter promotion. It scored 0.920 semantic F1 (0.915 precision,
0.925 recall), only 2.3 points below High. No reasoning tokens were used.

Across five diverse real forms and 19 pages, the same architecture used $0.59939
at official Luna list: **$11.99/100 forms** or **$3.15/100 pages** at that mix.
The actual promotional bill was $0.05994: $1.20/100 forms or $0.315/100 pages.
Micro semantic F1 was 0.9063. Individual deltas from production High were
-0.087, -0.011, -0.023, -0.056, and +0.002, so the average is good but the tail
is not deployable.

The visual workbook inspection found readable, aligned tables, but also excess
blank vertical space from estimated physical rows and overconfident green
styling. A one-reader untouched cell must not be presented as verified.

## 4. Repetition and diversity were separated experimentally

Starting from the identical saved Luna primary:

- a second targeted Luna reread raised cost from $0.01779 to $0.02813 and
  caught no additional known errors;
- a targeted Gemini 3.5 Flash Lite reread raised cost to $0.04852 and found 14
  additional known errors, increasing strict red capture from 14.47% to 20.43%;
- 12 of those 14 gains came from page 1, while pages 2, 4 and 5 gained none.

Thus model diversity has measurable value, but page-wide peer routing wastes
most of it. The next design should target categorical/metadata/contract-risk
regions, not run two full readers everywhere.

## 5. Controls prevented a false success claim

On a held-out synthetic sapling form, Luna matched 98.8% of writable geometry,
read 93.81% of written values exactly, and made zero false fills over 152 blank
cells. On a hard metadata form, exact written recall fell to 42.86% while blank
specificity stayed 100%. Luna flagged none of those errors, and a targeted
Gemini pass agreed with the mistakes and also caught none.

A held-out understorey form produced rows with more values than declared
columns. The pipeline failed them rather than deleting a guessed slot. Safe
repairs were restricted to deterministic implications: illegible implies
review, missing *trailing* values become null/review, out-of-page centers clamp
to the declared table, and a zero-column label-only footer becomes free text.

This demonstrates why two-model agreement, model confidence, and pretty output
cannot serve as correctness oracles. Deterministic geometry/coverage controls
and human escalation remain necessary.

## 6. Other candidate results

Gemini 3.5 Flash Lite was reopened after durable repricing showed the initial
“7.9 times Luna” comparison was an artifact of Luna's promotion. Unlike Luna,
Gemini's measured $0.30/$2.50 rates match Google's official standard list. On
`eval_09`, full Gemini cost $0.08909 and scored 0.932, improving compact Luna's
0.920 at half its durable $0.17786 cost. That single result did not survive the
diversity gate: Gemini scored 0.705 on `eval_05`, hard-failed an overlong row
on `eval_07`, scored 0.845 on `eval_11`, and 0.758 on `eval_13`. The four
completed forms cost $0.18206. Visual inspection found semantic column shifts,
omitted handwriting, and mishandled ditto/multi-value cells. Gemma 4 was no
cheaper for this workload, much slower, emitted no useful uncertainty, and
eventually returned malformed JSON.

Agentic Luna improved the hard `eval_05` from 0.659 to 0.690 at $0.07416
official list ($0.00742 promotional), still below High's 0.746. A second hard
form reversed that apparent win: on `eval_11`, agentic Luna scored 0.729 versus
compact Luna's 0.894, emitted 1.45 times the golden cell count, and cost
$0.13667 official list ($0.01367 promotional), over twice compact Luna's
$0.06431 list cost. It is rejected as a general Mid stage.

## 7. Durable-price correction

Long-term decisions use the model developer's standard list price, not an
aggregator promotion. OpenAI lists Sol at $5/$30, Terra at $2.50/$15 and Luna
at $1/$6 per million input/output tokens, with 1.25x cache writes. OpenRouter
billed the saved Luna runs at one tenth of that price and labels provider
discounts promotional and changeable. Google lists Gemini 3.5 Flash Lite at
$0.30/$2.50, matching the measured OpenRouter rate.

The dated source-of-truth links are recorded in `benchmarks/api_cost/README.md`;
raw provider usage and experiment prices remain in the ignored per-run
artifacts. This keeps future repricing separate from historical billing.

Thus the attractive `$1.20/100 forms` Luna result is an opportunistic bill, not
the architectural cost. The durable estimate is `$11.99/100 forms` for this
five-form mix. Both remain recorded so a temporary discount can be used without
being mistaken for the business case.

## 8. Decision

Do not deploy this Mid yet. Compact Luna's promotional bill meets the ideal
target, but its durable price does not, and two real forms plus the metadata
control fail the tail-quality/review-capture gates. Full Gemini's four completed
forms average $4.55/100 forms and $1.40/100 pages at durable Google list price,
but it hard-fails the fifth form and has larger content/layout losses on three
of the four completed forms.

The recommended next research architecture is a cheap vendor-list first pass,
deterministic IR/geometry/coverage checks, compact Luna or diverse Gemini only
on calibrated high-risk regions, ecology after transcription as deterministic
orange suggestions, and mandatory human review for hard structural ambiguity.
Full Gemini's friendly-form win and diversity-form failures show why model
identity cannot replace the gate. The evidence argues against agentic Luna as
a default, a third general model, or a same-model targeted retry.
