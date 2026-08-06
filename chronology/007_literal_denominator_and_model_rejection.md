# Experiment 007 — separate printed layout from literal reading

Date: 2026-08-06

## Metric failure found by a sparse form

A GPT-5.4 Mini Cursor pilot on a stream-habitat page missed all four handwritten
values but received 0.9535 exact workbook F1. The other 41 nonblank workbook
cells were printed labels reproduced deterministically from the blank template.
The metric correctly said the workbook layout/content was nearly complete, but
it was invalid as a model-reading score.

This is a denominator error analogous to the earlier single-character bug:
easy deterministic structure hid the values the model was actually asked to
read.

## Source-aware literal scorer

`template_value_eval.py` scores `ground_truth.json` sources directly:

- printed cells are excluded from model value precision/recall/F1;
- every `written` cell is a required nonblank literal;
- every generated blank or strike-through remains in the denominator for false
  fills and blank specificity;
- wrong values, omissions, and false fills are separate;
- accuracy is broken down by semantic value kind and mark type;
- a per-column modal oracle reads no pixels and is reported as a control;
- confidence thresholds report review burden, queue precision, and error
  recall.

`integrity_eval.py` remains the layout/workbook scorer. Both are required; one
must not be used as a proxy for the other.

## Corrected v5 results

Saved raw responses were rescored with no provider calls.

| reader/view | forms | literal micro F1 | correct written | wrong | omitted | false fills |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.6 whole page | 5 | 0.9644 | 352 | 9 | 8 | 0 |
| Gemini 3.5 whole page | 5 | 0.9671 | 353 | 8 | 8 | 0 |
| Gemini 3.6 row bands | 4 | 0.9799 | 292 | 5 | 0 | 2 |
| Claude Sonnet 5 soil | 2 | 0.8776 | 43 | 4 | 2 | 2 |

For soil specifically:

- clean literal F1 0.8980 (22/25 correct, two wrong, one omitted, no false
  fills; all-writable accuracy 0.9725);
- hard literal F1 0.8571 (21/24 correct, two wrong, one omitted, two false
  fills; all-writable accuracy 0.9541).

The confidence ≤0.80 review queue still captures all eight soil errors. The
queue contains 4/109 clean cells and 19/109 hard cells, so combined burden is
10.6% and combined queue precision is 34.8%. This calibration remains specific
to one reader/form family.

Disagreement conclusions are unchanged because those analyses already compare
every writable target, including blanks, directly against literal truth:

- page versus bands: 13/708 disagreements, capturing 87.5% of whole-page
  errors;
- Gemini 3.6 versus 3.5: 18/877 disagreements, capturing 70.59% of 3.6 errors.

## Cursor GPT-5.4 Mini pilot rejected

The user explicitly authorised Cursor for model diversity/grinding. A single
Cursor agent using `gpt-5.4-mini-low` read two small held-out pages from fixed
PNG/target contracts. It returned exact schemas and all requested IDs, but that
only established output discipline:

| form | writable targets | written values | literal F1 | errors |
| --- | ---: | ---: | ---: | --- |
| NVS metadata | 39 | 16 | 0.1053 | 2 wrong, 13 omitted |
| stream habitat | 11 | 4 | 0.0000 | all 4 omitted |

The subscription CLI exposed no attributable request tokens/cost. No cost claim
is made. The model is rejected before larger-form testing: schema compliance is
not coverage, and printed-cell workbook F1 would have hidden that failure.

## Decision

1. Headline known-template value metrics are now source-aware literal F1 plus
   explicit false fills; workbook F1 is labelled layout integrity.
2. Retain Gemini 3.6 as the provisional primary because it was stronger on the
   held-out foliar family; use 3.5 or bands only as optional review readers.
3. Do not use GPT-5.4 Mini for transcription.
4. Do not infer model quality from exact ID counts, valid JSON, or printed
   header reproduction.
