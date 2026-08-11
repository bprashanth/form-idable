# 015 — Production selector failure and workbook-provenance gate

Date: 2026-08-11

## 1. The smoke test passed, but the all-form test blocked the release

The first High production image completed its real smoke job and rendered the
new Review and Analytics surfaces. That was necessary but insufficient. A
serial production run over all 14 PDFs / 68 pages found:

- frozen Low micro semantic F1: 0.887
- first production High micro semantic F1: 0.867
- first production High macro semantic F1: 0.8587 versus Low 0.8512

The macro average hid two large regressions: eval_07 fell from 0.970 to 0.760
and eval_09 from 0.947 to 0.819. Production therefore remained blocked even
though one average and the smoke fixture looked good.

## 2. Why the first selector was wrong

The first selector treated at least 80% coordinate bridge coverage as evidence
that the agentic primary was healthy. A workbook can align perfectly to the
page schema while still omitting or misreading many literal values. eval_07
and eval_09 both reached 100% geometry coverage, so geometry alone provided
false reassurance.

The corrected truth-free gate keeps the primary only when all of these hold:

1. peer-supported geometry coverage is at least 80%;
2. primary nonblank literal evidence is at least 75% of the strongest peer;
3. peer-consensus conflicts are no more than 20% of declared targets; and
4. there is no material peer recovery: at least 15% more evidence than the
   primary and at least 10% more than the other peer.

Numeric zero is nonblank. This matters for ecology forms and is covered by the
same generic evidence rule; no fixture labels, expected ranges or golden values
enter routing.

On the failed production evidence, eval_07 exceeded the conflict limit (30.51%)
and selected Terra. eval_09 showed material Luna recovery (17.28% over primary,
48.97% over Terra) and selected Luna. Replaying this deterministic decision on
the exact saved model evidence avoids confounding the fix with a fresh model
sample.

## 3. The artifact validator found a second hidden defect

The selected fallback workbooks used `page1` through `pageN`, but some blank
canonical targets retained the rejected primary workbook's `v2` sheet name.
The extracted values scored correctly, while red spreadsheet highlighting
could silently miss those targets.

The canonical writer now assigns an explicit worksheet name to every target.
A production validator cross-checks, for every form:

- PDF, crop-manifest, canonical and Analytics page counts;
- literal workbook versus delivered workbook content;
- every review worksheet/row/column against the actual workbook value;
- unique review IDs and red target IDs;
- red source geometry against its canonical cell;
- normalized red/orange boxes and valid page numbers;
- review, Analytics and ecology summary counts.

The PWA also keys focus colours by worksheet name rather than assuming paper
page N means workbook sheet N. It materializes reviewable blank coordinates
outside Excel's saved used range, so an omitted blank cell can still be shown
red in the table. A browser regression test covers this exact case.

## 4. Controlled production result

Five disposable benchmark jobs were repaired from saved evidence: eval_07 and
eval_09 changed selected literal reader; eval_01, eval_04 and eval_08 received
worksheet-provenance metadata only. No transcription model was rerun and no
golden values were used in either operation.

The API was then used to download and rescore the production objects:

- High micro semantic F1: **0.913** versus Low **0.887**
- High precision: **0.922** versus Low **0.854**
- High recall: **0.905** versus Low **0.924**
- High macro semantic F1: **0.8809** versus Low **0.8512**
- 14/14 forms, 68/68 pages, zero cross-artifact errors
- 2,797 red targets out of 20,690 (13.52%) and 32 orange findings

High wins 7 forms and loses 7 against historical Low. The remaining losses are
not hidden: eval_03 -0.002, eval_04 -0.025, eval_06 -0.090, eval_07 -0.024,
eval_08 -0.001, eval_09 -0.004 and eval_12 -0.006 are the observed individual
deltas (the win/loss count uses exact scores; rounded near-ties may appear
equal). Aggregate improvement is the release claim, not universal dominance.

The local saved-evidence control remained unchanged at micro F1 0.910 versus
Low 0.887, 14/14 forms, 68/68 pages and zero artifact errors. Its focused queue
is smaller (8.83%) because fresh model evidence varies; this difference is
another reason not to report one model run as a deterministic truth.

## 5. Release and invariants

The corrected High image passed a fresh authenticated production job:

- verification job `5b128b19-67a4-4667-807d-daa835019499`
- route `agentic_primary`, 3 pages, 15 red disagreements, 17 ecology flags
- High ECR digest
  `sha256:0e13474a250fb33015c6c7e1a71213daf67b3d409eee9ee626d793237db3de2e`
- High task `formidable-high-worker:6`

The frozen Low control did not move:

- Low ECR digest
  `sha256:aacbe354d16bb79dda0ac30239e8d59a12b1353ab8ad75a245a5840fc21cc9bc`
- Low task `formidable-worker:15`

The backend release is accepted only together with the frontend all-page
browser sweep. The selector improvement alone is not sufficient if a reviewer
cannot see the exact source and workbook targets it selected.
