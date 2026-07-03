# Shankar forms — POC scope & preprocessing

Survey of 14 PDFs in `DatasheetScans/`. Goal: identify which can be ingested at ~80% quality with the current pipeline plus targeted new handlers, define what preprocessing is needed, and scope the experiment.

---

## What the PDFs are

All 14 PDFs are **scanned images** — no embedded text, no selectable content. Every page is a photo of a handwritten paper datasheet wrapped in a PDF container. The scanner/phone was not always consistent: some pages within the same PDF alternate between portrait and landscape depending on who took the photo.

Total: **68 pages** across 14 PDFs, spanning ~8 distinct form types.

---

## Preprocessing required before ingestion

### 1. PDF → per-page JPEG (mandatory)

The current good-shepherd endpoint accepts a **single image** per upload call. Multi-page PDFs must be split into individual page images. Done via PyMuPDF at 2× zoom (renders ~1400×2000 px from a 700×1000 pt scan — good enough for Textract).

Script: already run, outputs in `DatasheetScans_modified/pages/`. Manifest at `DatasheetScans_modified/manifest.json`.

```bash
# To regenerate:
cd form-idable/agent/server
source .venv/bin/activate
python3 <the extraction script>   # see docs/testing.md for the pattern
```

### 2. No rotation needed

All in-scope pages are already correctly oriented inside the PDF. Portrait pages render portrait, landscape pages render landscape. Textract handles both orientations without help.

### 3. Crop (per-page, user-driven or manual for POC)

The metadata block at the top of each form (date, site ID, GPS, observer names) will cause the same multi-table problem we saw in the WA0000 test image. **Each page should be cropped to the data grid only before upload.** For the POC batch-run we can crop each extracted JPEG manually once and save the crop coordinates; for production use the PWA crop UI handles this per-scan.

---

## Form-by-form assessment

### Tier 1 — include (high confidence, works with current pipeline)

| PDF | Pages | Structure | Columns of interest | Notes |
|---|---|---|---|---|
| `2023VegetationPlots.pdf` | 4 | Portrait/landscape alternating | No, Species, GBH(cm), Height(m), Remarks | Identical form to WA0000 test. Ground cover section above grid is metadata noise — crop it out. |
| `TreePlots20mx20m.pdf` | 3 | Portrait | Same as above | Same form, different dates/sites. |
| `GrowthSurvivalMonitoring.pdf` | 3 | Landscape | S.no, T_no, Species, Basal_Dia_1, Basal_Dia_2, Shoot_L, Crown_Dia, Survival, Remarks | Clean grid. Survival column is a single letter code (A/D/B/etc) — Textract will read it as-is, researcher interprets. |
| `LeafLitterBiomass.pdf` | 4 | Portrait | Trap ID, Fresh/Dry, Leaf, Twig, Flower, Fruit, Seed, Other | Numeric data, clean. Trap ID format is C1–C25. Handwritten totals/annotations at bottom — will be misread but researcher can ignore. |

**14 pages, 4 PDFs. These should produce usable output with zero new handlers.**

---

### Tier 2 — include with targeted new handlers

| PDF | Pages | Structure | Challenge | Handler needed |
|---|---|---|---|---|
| `RegenerationPlot5mx5m.pdf` | 3 | Portrait | Seedling/sapling counts recorded as tally marks (`III`, `IIII 1`) | **Tally handler**: count tally-mark characters and replace with an integer |
| `SurvivalGrowthMonitoring.pdf` | 3 | Portrait (dense) | ~60 rows per page, very small handwriting, d/dr column | Species handler will help. Dense rows are fine for Textract once cropped. |
| `LEMoNPlotQuarterlyDendrobandSample.pdf` | 3 | Portrait (dense) | Many abbreviated columns (uso, gno, tno, pno, sps, la, b, lng, dbm_old, dbm_new, da) | Abbreviated column names won't match cheatsheet keywords — researcher should review infer-types output and confirm manually. |
| `TreePhenologyTwoTrails.pdf` | 6 | Landscape (very wide) | 12+ columns, many single-character Y/N/0 cells for leaves/flowers/fruits. "Multistem" column is numeric but irregular | **Y/N normaliser**: standardise y, Y, N, n, 0, H, × to Y/N. Otherwise Textract reads these OK. |

**18 pages, 4 PDFs. Need 2 new handlers (tally + Y/N normaliser).**

---

### Tier 3 — stretch goals (higher risk, tackle after tier 1+2 are working)

| PDF | Pages | Challenge |
|---|---|---|
| `LEMoNPlotAnnualCensusSample.pdf` | 6 | Very dense portrait table (~90 rows, ~12 columns). Two-row merged headers. Abbreviated column names. Functionally the most data-rich form but also hardest for Textract. |
| `SaplingSurvivalMonitoring.pdf` | 2 | Landscape, multi-date columns (same species tracked across many visits with checkmarks). Column structure is time-series, not a simple list. |
| `GridVegetation100mx100m.pdf` | 3 | **Two complete form-sheets printed per page** (GPS grid north mini-map + two separate data blocks). Would need the page split into two crops before upload. |

**8 pages, 3 PDFs. Significant structural issues; drop from initial POC unless there's time.**

---

### Excluded — drop from POC

| PDF | Reason |
|---|---|
| `2003_AnandOsuri_BirdChecklists.pdf` (24 pages) | Mixed page sizes, inconsistent orientation, first half is free-text numbered lists (no grid at all), second half is a visit-tracking grid. No consistent structure to target. |
| `SeedSeedlingExperiment.pdf` (2 pages) | Two side-by-side sections (A and B) with coded multi-row sub-tables (L/D/C/R/S codes). Fundamentally different layout — would need its own complete pipeline path. |
| `SaplingGrowthMonitoring.pdf` (2 pages) | Wide time-series table (height and diameter for many dates, side by side). No single "species column" — the columns encode time, not category. Wrong model for current pipeline. |

---

## New handlers required for tier 1+2

### Tally handler (`type: tally`)

Needed for: `RegenerationPlot5mx5m.pdf` — seedling/sapling columns contain tally marks.

What Textract produces: `III`, `IIII`, `IIII 1`, `ll`, `1111` (mixed because OCR guesses I/l/1/|).  
What the handler should output: the integer count of those characters.

Cheatsheet keyword ideas: `tally`, `seedling`, `sapling`, `coppice`.

See `docs/manuals/new-handler.md` for the full implementation walkthrough — tally is the worked example there.

### Y/N normaliser (`type: yn`)

Needed for: `TreePhenologyTwoTrails.pdf` — leaves/flowers/fruits columns are single-character Y/N observations.

What Textract produces: mix of `y`, `Y`, `N`, `n`, `0`, `H`, `×`, blank.  
What the handler should output: canonical `Y` or `N` (or leave blank if truly empty).

Cheatsheet keyword ideas: `flush`, `mature`, `fallen`, `buds`, `open`, `unripe`, `ripe`.

This is a simple normalisation — no fuzzy matching needed, just a lookup table.

### Species dictionary enrichment

The existing species handler will be used for all tier 1+2 forms. The current `data/species_name.csv` was built around the WA0000 form. These new forms introduce new species (e.g. *Glochidon malabaricum*, *Bambusa* sp., *Artocarpus heterophyllus*) and potentially different local names. The dict will need enrichment after the first test run reveals what's missing.

---

## POC experiment scope

**In scope: 32 pages (Tier 1 + Tier 2), from 8 PDFs.**

All pages have been extracted to `DatasheetScans_modified/pages/`. Recommended test order:

1. Tier 1 pages — run as-is, verify >80% column accuracy without new handlers
2. Add tally handler → re-run RegenerationPlot
3. Add Y/N normaliser → re-run TreePhenology
4. Enrich species dict from what tier 1 produces → re-run species checks across all

**Target: 80% of rows in tier 1+2 forms have the key scientific data columns (species, measurements) extracted correctly without researcher correction.**

Tier 3 and excluded forms are explicitly out of scope for the initial run.

---

## Pipeline changes needed

| Change | Effort | Notes |
|---|---|---|
| PDF → JPEG extraction script | Done | `DatasheetScans_modified/pages/` + manifest |
| Tally handler endpoint | Small | See `docs/manuals/new-handler.md` |
| Y/N normaliser endpoint | Small | Simple lookup, no ML |
| Crop coordinates per form | Manual, one-time | Define crop box for each of the 8 form types; bake into test script |
| Species dict enrichment | Iterative | After first Textract run reveals missed species |
| Cheatsheet additions | Small | Add `tally`/`seedling`/`flush`/`mature` etc. keywords |
