# 014 — Additive subscription High: all-form release gate

Date: 2026-08-11

## Question

Can High use only the locally available authenticated subscriptions, preserve
Low as the default and frozen task, improve the delivered extraction without
silently voting over uncertain handwriting, and give a reviewer a materially
smaller, source-linked queue?

The answer is **yes as an opt-in reviewed workflow**, with an explicit caveat:
the available agentic reader is nondeterministic enough that High needs a
coverage gate and a structured fallback. It is not evidence that every fresh
model run is better than every historical Low run.

## Stage 1 — freeze the control

The release control is the historical Low corpus and the production Low
artifact itself:

- ECR digest
  `sha256:aacbe354d16bb79dda0ac30239e8d59a12b1353ab8ad75a245a5840fc21cc9bc`
- task definition `formidable-worker:15`
- missing `effort` still means `low`
- Low still launches container `worker` and publishes only the old artifact
  contract

High has a separate image, task family and container. The high-only deploy
wrapper snapshots the Low digest/task before deployment and refuses success if
either moves.

## Stage 2 — keep the Low-compatible agent, but do not trust it to certify itself

High first runs the same Low-compatible agentic extraction as a candidate
primary. It then independently runs three bounded structured calls per page:

1. Luna maps printed geometry and declares the page/table/cell schema.
2. Terra reads literal values into that schema.
3. Luna independently reads literal values into the same schema.

The peers receive no golden data and no form-specific value ranges. Raw JSON is
saved before assembly. Ecology is not present in any transcription prompt.

When the agentic workbook maps at least 80% of the peer-supported nonblank
evidence, High delivers that workbook unchanged. Only cells where both peers
agree against the primary enter the red queue. The peers never overwrite it.

## Stage 3 — detect model fatigue instead of retrying until a score looks good

Fresh agentic runs exposed a large nondeterminism failure that the frozen
historical score could not show:

- eval_09 first fresh primary: semantic F1 0.750
- retrying eval_09 produced a 432-row mostly blank template: F1 0.132
- eval_04 fresh primary: F1 0.596 versus historical Low 0.811

Repeating the same unbounded agent was therefore rejected. The useful signal
was coverage, not the model's self-confidence. If the primary maps less than
80% of peer-supported nonblank evidence, High discards that content and uses a
bounded structured reader. Every Terra/Luna disagreement then becomes red.

Terra is the declared fallback. Luna replaces it only if it contains at least
10% more nonblank evidence. This material-evidence threshold fixed eval_08:
a tiny coverage advantage had selected Luna at 0.798, while the declared Terra
reader scored 0.858. A targeted Sol reread was also rejected: on eval_03 it
scored 0.805 versus Terra's 0.816 after three extra calls.

Capacity/rate-limit errors retry at most twice. Completed page evidence is
resumable, so a failure on eval_02 or the 24-page eval_04 does not repay or
repeat successful calls. Other errors fail closed.

## Stage 4 — ecology remains a separate, suggestion-only question

The delivered literal workbook is fixed before ecology runs. Generic physical
bounds, robust within-form distributions and taxonomy context write an
`ecology_review` audit sheet and orange source boxes. They never edit a cell.
Analytics is calculated from the values actually delivered, not from peer-only
or unmapped evidence.

An independent audit found peer-only unmapped values in an early Analytics
artifact even though they were absent from the workbook. The final bridge now
clears their presented value and workbook coordinate while retaining raw peer
provenance. This is why artifact consistency is a release gate, not a UI detail.

## Stage 5 — all-form result

All 14 current PDFs, 68 pages, were processed and uniformly rebuilt from saved
raw evidence through the final code. `content.xlsx` is the selected extraction;
`output.xlsx` is the same content plus the ecology audit sheet.

| Fixture | Pages | frozen Low F1 | High F1 | Delta | Route | Red | Orange |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| eval_01 | 4 | 0.728 | 0.784 | +0.056 | agentic | 51 | 0 |
| eval_02 | 3 | 0.928 | 0.994 | +0.066 | agentic | 22 | 4 |
| eval_03 | 3 | 0.856 | 0.816 | -0.040 | Terra fallback | 76 | 0 |
| eval_04 | 24 | 0.811 | 0.785 | -0.026 | Terra fallback | 177 | 8 |
| eval_05 | 3 | 0.689 | 0.761 | +0.072 | agentic | 21 | 3 |
| eval_06 | 4 | 0.872 | 0.827 | -0.045 | agentic | 14 | 0 |
| eval_07 | 6 | 0.970 | 0.920 | -0.050 | agentic | 101 | 0 |
| eval_08 | 3 | 0.834 | 0.858 | +0.024 | Terra fallback | 501 | 0 |
| eval_09 | 6 | 0.947 | 0.951 | +0.004 | Luna fallback | 732 | 11 |
| eval_10 | 3 | 0.574 | 0.847 | +0.273 | agentic | 48 | 0 |
| eval_11 | 2 | 0.944 | 0.955 | +0.011 | agentic | 28 | 0 |
| eval_12 | 3 | 0.993 | 0.980 | -0.013 | agentic | 22 | 0 |
| eval_13 | 2 | 0.838 | 0.861 | +0.023 | agentic | 7 | 5 |
| eval_14 | 2 | 0.933 | 0.954 | +0.021 | agentic | 54 | 5 |

Macro semantic F1 improved 0.8512 to 0.8781. Micro semantic F1 improved
0.887 to 0.910, with precision 0.854 to 0.917 and recall 0.924 to 0.904.
Words improved 0.807 to 0.841 and semantic marks 0.874 to 0.966. Numeric F1
fell 0.965 to 0.939 because High is more conservative and misses some numbers.

There are two valid controls and they answer different questions:

- Against the frozen historical Low artifacts, High wins 9 forms and loses 5.
  It wins in aggregate but does not dominate every historical sample.
- Against the fresh Low-compatible primary produced inside the same High job,
  the selector has 4 wins, 10 ties and zero regressions. This paired control is
  the relevant proof that the additive route gate does not make that job worse.

The final review load is 1,854 red cells out of 21,006 mapped targets (8.83%)
and 36 orange findings. eval_08 and eval_09 dominate the red burden because
their agentic primaries collapsed and the fallback honestly exposes all peer
differences. That is the human-fatigue cost of refusing a silent guess.

## Stage 6 — independent artifact and browser gates

The independent validator checks PDF/page parity, decoded page renders, exact
worksheet coordinates, canonical/workbook equality, unique review IDs,
normalized source boxes, crop existence and route-specific provenance. Result:

- forms: 14/14
- pages: 68/68
- artifact errors: zero

The production PWA bundle builds. The 18 general product flows pass. The
all-form visual suite opens all 68 pages, waits for each image to decode,
compares exact red/orange overlay counts with the manifests, requires real
workbook rows, opens Analytics and requires a distribution chart. All 14
all-form cases pass. Full-resolution screenshots are saved under
`benchmarks/high_visuals/additive-v1/`.

## Cost, latency and stop condition

Codex subscription calls report no marginal API charge, so `$0` in the audit
means **unmetered by the CLI**, not free infrastructure. The structured stage
used 204 calls, 3.79 million reported tokens and 14,468.5 seconds of summed
provider latency: 212.8 seconds per page before the agentic primary and Fargate
overhead. High is intentionally a slower, user-selected tier.

The automatic stop condition is now concrete:

- do not add a third reader unless a frozen paired gate beats the selected
  reader by a material margin; Sol did not
- do not retry a collapsed agent indefinitely; coverage routes to fallback
- do not turn ecology plausibility into transcription truth
- when the fallback queue is dense, present the limit to a human rather than
  spend more tokens to conceal it

## Release decision

The local candidate passes an opt-in production gate. It improves aggregate
content, never worsens its paired in-job primary, preserves literal provenance,
and gives a source-linked review/Analytics workflow. It must not be described
as perfect or as better on every historical form. Production verification must
repeat a real high job, validate every artifact, visually inspect Review and
Analytics, and prove the frozen Low digest/task did not move.

