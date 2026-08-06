# Experiment 009 — attention-first review, not automatic correction

Date: 2026-08-06

## Evidence that determines the UI

The extraction experiments produced two signals with very different meanings:

- literal-reader disagreement covered roughly 63% of eval_09 transcription
  errors while selecting 393/3,209 values (12.25%), about five-fold enrichment;
- on the two soil forms, primary confidence at or below 0.80 selected 23/218
  writable targets (10.6%) and contained all eight errors, with 34.8% queue
  precision;
- five robust GBH distribution outliers on eval_09 were all correctly
  transcribed, so ecology outlier status had 0/5 precision as an extraction
  error detector;
- ecology review produced useful plausibility/taxonomy findings, but these are
  hypotheses about the observation, not evidence that the handwriting reader
  is wrong.

Therefore one combined “AI correction” queue would be epistemically false. A
peer reader can identify literal ambiguity; ecology can identify a surprising
measurement or taxon. Neither may silently replace the primary literal value.

## PWA prototype

The PWA now optionally consumes `formidable-review-v1` from
`/api/jobs/{job_id}/review-manifest`. A missing or malformed optional artifact
leaves the existing crop/xlsx review path functional.

When present, the UI offers three explicit views:

1. **All cells** — the page-shaped xlsx, with attention cells tinted;
2. **Transcription** — exact red bbox overlays and a queue showing the primary
   literal, reason, and peer alternative; clicking opens the existing editable
   zoom modal at that bbox;
3. **Ecology** — separate anomaly cards with observed value, median/MAD where
   applicable, and the statement that no value was changed.

The workbook loader now retains every sheet and selects the sheet matching the
paper page. The old implementation always displayed sheet one. Correction keys
also include the page number, avoiding collisions between the same Excel
coordinate on different sheets.

## Validation

- production frontend build succeeds;
- 15/15 Playwright tests pass;
- the browser suite is now hermetic for manifest/xlsx/page/crop artifacts and
  has an explicit dev-only Cognito bypass that cannot activate in production;
- a generated three-sheet workbook proves page navigation changes the table;
- visual inspection at 1,280×720 confirmed the attention bbox, queue, literal
  value, peer alternative, and non-auto-apply notice are aligned and legible.

## Limitations and cut line

This is a local frontend prototype, not a deployment. The current backend does
not serve the optional endpoint, and no AWS change was made. Production wiring
requires the worker to upload `review_manifest.json` and the API to return its
presigned content. That should happen only after the extraction branch and
route gate clear their remaining external-validity checks.

The soil confidence result is only two forms from one family. Confidence must
be calibrated by model and form family before its threshold is treated as a
general service-level guarantee. Disagreement is the stronger cross-model
signal today.
