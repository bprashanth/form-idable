# 016 — QR/OMR Form Builder prototype

Date: 2026-08-11

## Goal

Turn any completed form already visible on the dashboard into a clean
collection-sheet preview with the geometry aids demonstrated by paperroast.
For the meeting, the UX intentionally ends at preview/print; it does not yet
register a reusable template with the extractor.

## What was built

- Dashboard `Clone` action and a Form Builder gallery of completed jobs.
- A client-side printable page generated from the selected job's delivered
  workbook and, when available, High's canonical review contexts.
- A real QR image containing a deterministic form ID.
- Filled marks beside every row boundary on both margins, including a taller
  first sequence anchor.
- Filled ticks under every column boundary.
- Empty writable cells. Source handwriting is never copied; only a recognized
  serial column may preprint row numbers.
- A visible prototype explanation of why QR identity and printed fiducials
  help geometry under page curl and camera perspective.

High review contexts are preferred for printed column/header labels. The
fallback workbook heuristic rewards unique textual header rows and penalizes
numeric data rows. This fixed an early eval_13 prototype that accidentally used
the first handwritten data row as its header.

## Gate

All 14 saved form types were opened through the builder:

- 14/14 preview cases passed;
- every QR is a generated PNG data image;
- row marks equal writable rows plus the header/sequence boundaries;
- column ticks equal columns plus one;
- each form has at least ten writable rows and two columns;
- no source values appear in the writable body;
- when canonical contexts exist, every printed table label comes from those
  contexts rather than a data value.

Screenshots are under `benchmarks/high_visuals/builder-v1/`. eval_01, eval_02,
eval_09 and eval_13 were visually inspected after the all-form gate.

## Production gate

The implementation was pushed to `main` and Netlify served asset
`/assets/index-CzzQcnL8.js`. A separate authenticated Playwright gate then
opened every saved production High job through the live Netlify, Cognito, API
Gateway and S3 paths:

- 14/14 live builder cases passed in 43.1 seconds;
- the same QR, empty-body, canonical-label and OMR-count invariants passed;
- screenshots for all 14 are under
  `benchmarks/high_visuals/prod-builder-v1/`;
- all 14 screenshots were visually opened, not merely asserted.

The visual sweep found no missing or overlapping geometry. It also exposed the
remaining semantic boundary instead of concealing it: complex/multi-section
sources can retain generic labels (`Column 8`, `Unlabeled column`), repeated
numeric headings, or source metadata such as `Printed file path`. No guessed
replacement was introduced. These are confirmation-editor inputs, not safe
automatic corrections.

## Honest boundary

This is a UI prototype, not yet paperroast's complete template system. Printing
works, but the QR ID is not persisted in a versioned descriptor, the form is
not registered for QR lookup, multi-page/page-break editing is not exposed,
and the High/Low extraction tasks do not yet route QR forms through a
deterministic fiducial extractor. The next production stage is a confirmation
editor for labels, types, closed-choice legends, row count and page breaks,
followed by descriptor/PDF persistence and a QR-aware extraction route.
