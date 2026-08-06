# Experiment 003 — exact, adversarial synthetic ecology corpus

Date: 2026-08-06

## Goal

Create structurally diverse fake ecology forms with exact cell truth, realistic
blanks and degradation, and semantically plausible values. The corpus must
detect layout loss, invented cells, modal filling, and benchmark-generator
mistakes instead of flattering the extractor.

## Corpus construction

- Source layouts: 35 downloaded real blank-form PDFs, yielding 40 usable
  template pages across marine, bird, vegetation, nursery, soil, stream, and
  other ecology/field-survey forms.
- Deterministic dev/test split is by template filename, not filled instance.
- Two fills per template page: different handwriting seed/density, with one
  clean and one hard degradation where writable cells exist.
- Values use real SD-19 handwritten glyphs plus handwriting fonts for prose.
- New exact artifacts per form:
  - `layout_golden.xlsx`, retaining page/lattice row/lattice column;
  - `ground_truth.json`, with every ruled cell, point and normalized boxes,
    printed/written/blank state, literal intended value, mark type, semantic
    kind, and printed semantic context;
  - legacy token-bag `golden.xlsx` retained only for historical comparisons.
- Fixed the builder's use of Python's randomized process hash. Seeds now come
  from SHA-256 and reproduce across processes/machines.

## Hostile visual-audit failures and fixes

The first regenerated corpus was rejected before model scoring:

1. Bird species-code columns contained person names, one understorey species
   column contained single letters, and stream fields received arbitrary dates.
   Cause: random width-based types and same-lattice-column labels ignored merged
   parents and adjacent field prompts.
2. Empty regions within merged table headers were treated as writable cells.
3. Page-global vertical coordinates split wide Comments cells into phantom
   narrow cells when the vertical rule did not cross that physical row.
4. NRCS PDF drawing streams included rules below the visible MediaBox, producing
   normalized boxes greater than 1.

Generic fixes, with no template-specific values or ranges:

- same-column and nearest overlapping vector headers outrank broader context;
- labels beside a field and merged headers supply fallback context;
- alpha/species codes, taxa, dates, times, counts, measurements, percentages,
  temperature, pH, coordinates, names, notes, and Y/N marks have separate
  generators;
- grid-form writing is restricted to data-like rows, preserving empty headers;
- elementary lattice intervals merge when no vertical rule crosses the row;
- cells outside the PDF MediaBox are rejected;
- semantic context is stored beside every cell so assignments remain auditable.

## Accepted corpus

Directory: `benchmarks/wide/struct_eval_v4_exact_semantic/`

- **80 forms** from **40 template pages**.
- **18,270 ruled cells**; **7,502 written cells**.
- **14 semantic kinds**, including 431 species values, 1,039 Y/N values,
  643 percentages, 448 decimals, 221 dates, and 291 ecology notes.
- Full contract audit: **0** duplicate/value/workbook/bbox/type violations.
- Six pages have no writable cells after the stricter lattice rules. They are
  explicitly listed in `audit.json` and excluded from accuracy averages; they
  may still serve as blank-overproduction controls.

The audit is reproducible with `benchmarks/wide/audit_synthetic.py`.

## Limitations

- These are realistic hand-print and degradation tests, not a substitute for
  real field cursive or independent human transcription.
- Hard variants store intended pre-degradation truth. A sampled human-readable
  ceiling is required before interpreting model errors on severe degradation.
- Generic semantic inference is materially better after visual audit but does
  not claim a complete ecology ontology. Exact structure/value truth and
  ecological realism are separate quality dimensions.
- Generated test data is never used to assert a correction range for a real
  form. Ecology correction remains a separate, provenance-preserving stage.

## Decision

Use v4 for exact structural/model ablations. Keep earlier v2/v3 directories as
rejected evidence during this research session; do not mix them into reported
scores. Exclude zero-writing pages from accuracy means and always report the
modal oracle, false fills, omissions, and exact-position metrics.
