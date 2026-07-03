# Shankar forms — phased POC plan

Reference: `docs/design/shankar_poc_scope.md` for form-by-form assessment and tier definitions.

---

## Overview

Four phases, each building on the last. Tiers 1 and 2 are committed scope. Tier 3 and the excluded forms (especially the Osuri bird data) are deferred — revisit after tier 2 is working.

```
Phase 1  PDF input + per-page review UX     (tier 1 forms, no new handlers)
Phase 2  New handlers + tier 2 review        (tally + Y/N handlers)
Phase 3  Tier 3 forms                        (structural problems, TBD)
Phase 4  Excluded / Osuri bird data          (free-text + checklist forms, TBD)
```

---

## Phase 1 — Tier 1 forms + PDF review UX

**Forms in scope:** `2023VegetationPlots`, `TreePlots20mx20m`, `GrowthSurvivalMonitoring`, `LeafLitterBiomass` (14 pages, 4 PDFs).

**Goal:** A user can drop a PDF into the PWA, see its pages, run the existing handlers (species + serial) on each page, review corrections through a card UI with bbox highlighting, and download a single merged Excel at the end.

### What changes

#### Agent server — new PDF endpoint

`POST /agent/pdf/pages`
- Accepts a PDF upload
- Splits into pages using PyMuPDF
- Returns JSON: `{page_count, pages: [{page: 1, image: "<base64 jpeg>", width, height}]}`
- Each image is the rendered page at 2× zoom (same resolution as the extracted test images)
- No Textract call here — just splitting. Textract happens per-page via the existing `/api/upload` flow.

#### PWA — new views and flow

The current flow is: Capture → Crop → Processing → Result.

For PDF input, the new flow is: **PDFUpload → PDFReview (per page) → Download**.

**PDFUpload view**
- File picker (accepts `.pdf`)
- On select: POST to `/agent/pdf/pages`
- Shows a grid of page thumbnails with page numbers
- Each thumbnail has a status badge: `pending / processing / done`
- "Process all" button works page by page sequentially

**Per-page processing (no new view — happens in background)**
- For each page image: POST to `/api/upload` (good-shepherd) → gets xlsx + bboxes
- Stores {xlsx bytes, bboxes, page image blob} per page in a pages store

**PDFReview view (per page)**
- Left panel: the page image (same `FormImageOverlay` component as current result view)
- Right panel: stack of "check" cards, one per detected column type
- Each check card has: column name badge, "Run check" button, status, then inline review once run

**Check cards (the core new UX)**

Each card represents one column type detected by `infer-types`. States:

```
[ Species: SPP Name/Local Name ]  [ Run check ▶ ]

   ↓ after Run check

[ Species: SPP Name/Local Name ]  ✓ 12 proposals

  ┌─────────────────────────────────────────┐
  │ #3  kage  →  Litsea wightiana  (100%)  │  [✓ Accept] [✗ Skip] [✎ Edit]
  └─────────────────────────────────────────┘
  ┌─────────────────────────────────────────┐
  │ #7  nelli →  Phyllanthus emblica (92%) │  [✓ Accept] [✗ Skip] [✎ Edit]
  └─────────────────────────────────────────┘
  ...
  [ Save corrections ]
```

- Clicking a proposal card highlights that row's bbox in the page image (reuses `FormImageOverlay` + existing `activeProposal` / `primaryEntries` pattern)
- Accept/Skip/Edit inline per card
- "Save corrections" calls `apply-species` (or the appropriate apply endpoint), updates xlsx bytes for this page
- For serial: auto-applies on "Run check" with no review needed — just shows "Renumbered 1–N ✓"

**Download view**
- After all pages are processed: "Download Excel" button
- Client-side: merges all per-page xlsx files into a single workbook (one sheet per page, named `Page 1`, `Page 2` etc.)
- Uses SheetJS (`xlsx` npm package) — already likely in pwa/node_modules if not, add it

### Reused from current code
- `FormImageOverlay.vue` — bbox highlighting, no changes
- `AgentSidebar.vue` — cheatsheet + species DB editor, no changes needed
- `useFormStore.js` — extend to hold pages array instead of single form
- `/agent/infer-types`, `/agent/check-species`, `/agent/apply-species`, `/agent/check-serial` — no changes
- `useApi.js` — no changes

### What is explicitly NOT in phase 1
- Auto-crop per form type (user crops are skipped — assume pre-cropped JPEGs for POC test; real use still goes through PWA crop)
- Species dict enrichment (do after first real run reveals gaps)
- Cheatsheet keyword additions for new column names
- Per-page progress saving / resume
- Color coding in the output Excel

---

## Phase 2 — Tier 2 forms + new handlers

**Forms in scope:** `RegenerationPlot5mx5m`, `SurvivalGrowthMonitoring`, `LEMoNPlotQuarterlyDendrobandSample`, `TreePhenologyTwoTrails` (18 pages, 4 PDFs).

**Goal:** Add two new handlers to the agent server. The phase 1 review UX works for them without changes — each handler produces proposals in the same shape, or auto-applies (like serial).

### New handlers (agent server)

**Tally handler (`type: tally`)**
- Endpoint: `POST /agent/check-tally`
- Input: xlsx + type_map
- Counts tally-mark characters (`I`, `l`, `1`, `|`) per cell and replaces with integer
- Auto-applies (no review needed — like serial)
- See `docs/manuals/new-handler.md` for full implementation walkthrough (tally is the worked example)
- Cheatsheet keywords to add: `tally`, `seedling`, `sapling`, `coppice`

**Y/N normaliser (`type: yn`)**
- Endpoint: `POST /agent/check-yn`
- Input: xlsx + type_map
- Maps cell values: `{y, Y, yes, 1, ✓} → Y`, `{n, N, no, 0, H, ×, x, -} → N`, blank → blank
- Auto-applies (no review needed)
- Cheatsheet keywords to add: `flush`, `mature`, `fallen`, `buds`, `open`, `unripe`, `ripe`, `multistem`

### Phase 1 UX handles these automatically
The check card for `tally` and `yn` types will show "Run check → Auto-applied ✓" with the row count, same as serial. No new UI work needed.

### Species dict enrichment
After the first tier 2 run, add missing species to `data/species_name.csv` based on what the fuzzy matcher fails to find. This is data work, not code work.

---

## Phase 3 — Tier 3 forms (deferred)

**Forms:** `LEMoNPlotAnnualCensusSample`, `SaplingSurvivalMonitoring`, `GridVegetation100mx100m`.

**Blockers to resolve before starting:**
- `GridVegetation100mx100m`: two complete form-sheets per page — needs auto-split of the page image into two crops before upload
- `SaplingSurvivalMonitoring`: multi-date column structure — each date is a separate column group; current Excel model is flat. May need a reshape step in the agent server.
- `LEMoNPlotAnnualCensusSample`: 12-column dense portrait table with merged headers — Textract accuracy on very dense small-print handwriting is the unknown. Run a test upload first to see what comes out before committing to handlers.

**Decision point:** after phase 2 is done, review tier 3 blockers and decide scope. If the dense form accuracy is poor, tier 3 may simply be flagged as "researcher post-processes in Excel."

---

## Phase 4 — Excluded forms (Osuri bird data + others)

**Main target:** `2003_AnandOsuri_BirdChecklists.pdf` (24 pages, heterogeneous).

This PDF contains at least two distinct form types:
1. **Free-text bird lists** (pages 1, 9 visible so far) — a numbered list of species seen at a location, no grid
2. **Visit-tracking grid** (page 2, `Kalyana Pandhal Fragment`) — species rows × visit columns, cells are `S`/`H`/blank

The free-text pages cannot be processed by Textract table extraction — they'd need a different prompt (LLM-based reading of a list). The grid pages are tractable once the format is understood.

**Plan:** parse the visit-tracking pages as a grid (species × visit matrix); drop the free-text pages or convert them to a simple two-column "species observed / date" list via an LLM call. Design TBD after phases 1–2 establish the pattern.

---

## Success criteria

| Phase | Criterion |
|---|---|
| 1 | User uploads a tier 1 PDF, reviews species corrections, downloads Excel. ≥80% of species names correct after review. |
| 2 | Same flow works for tier 2 PDFs. Tally counts and Y/N values correct on first pass. |
| 3 | Dense forms produce a usable (if imperfect) Excel that the researcher prefers to manual transcription. |
| 4 | Osuri visit-tracking pages produce a species × visit matrix Excel. |
