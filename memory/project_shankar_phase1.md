---
name: project-shankar-phase1
description: Current build state for Shankar forms POC — Phase 1 PWA implemented, partially tested, more testing pending
metadata:
  type: project
---

Phase 1 of the Shankar ecological forms POC is implemented (code complete) and partially tested end-to-end.

**Why:** Shankar has 14 PDFs of ecological survey datasheets. Goal is to ingest them via the existing form-idable pipeline with ~80% accuracy. Phase 1 covers the 4 simplest ("tier 1") PDFs.

**What is done:**
- Agent server: `POST /agent/pdf/pages` endpoint (`agent/server/routers/pdf.py`) — accepts a PDF, returns page count + per-page JPEG images as base64. PyMuPDF in requirements.txt.
- Design docs: `docs/design/shankar_poc_scope.md`, `docs/design/shankar_poc_phasing.md`.
- PWA (all uncommitted as of 2026-06-15):
  - `xlsx` (SheetJS) installed in `pwa/`
  - `pwa/src/composables/usePdfStore.js` — pages array (imageBlob, xlsxBytes, rowBboxes, typeMap, summary, status), `loadFromUpload`, `processPage`/`processAll` (POST `/api/upload` then `/agent/infer-types`), `downloadMerged` (SheetJS, one sheet per page named "Page N")
  - `pwa/src/views/PDFUploadView.vue` (route `/pdf`) — file picker → `/agent/pdf/pages` → thumbnail grid with status badges → "Process all" / "Start review"
  - `pwa/src/views/PDFReviewView.vue` (route `/pdf/review/:pageIndex`) — left `FormImageOverlay`, right stack of `CheckCard`s, prev/next page nav, "Download merged Excel"
  - `pwa/src/components/CheckCard.vue` — species (proposals/edit/apply, ported from `ResultView.vue`) and serial (auto-apply) handlers; unsupported types (tally, yn — phase 2) show a placeholder
  - `pwa/src/router.js` — `/pdf` and `/pdf/review/:pageIndex` routes added with auth + pages-loaded guards
  - `pwa/src/views/CaptureView.vue` — "Scan PDF" button added

**What was tested (2026-06-15, browser E2E via headless Chrome):**
- Ran the full flow against real backends with `TreePlots20mx20m.pdf` (3 pages, found in `/media/desinotorious/T7 Shield/partners/shankar/forms/DatasheetScans/`).
- Confirmed working with zero console errors: PDF split → thumbnail grid (pending badges) → "Process all" (real Textract via `/api/upload` + `/agent/infer-types`) → all pages "done" → review view (image + CheckCard stack) → species check → proposals list → clicking a proposal highlights the correct row bbox (red overlay on `FormImageOverlay`) → "Save corrections" → "Download merged Excel" (disabled until all pages done, then produces a valid xlsx with sheets "Page 1"/"Page 2"/"Page 3").

**Testing pending — resume here:**
- The serial CheckCard's auto-apply path (`/agent/check-serial` → "Renumbered 1–N ✓") was NOT exercised — `TreePlots20mx20m.pdf` had no page with a recognized serial/"S.No" column. Need a PDF with a serial column (e.g. `2023VegetationPlots.pdf` or `GrowthSurvivalMonitoring.pdf`) to test this.
- `LeafLitterBiomass.pdf` (and possibly other tier-1 PDFs) use a notation where a **dot means "0"** and a **continuous line drawn through a column means "no entry"**. Untested how Textract/the type inference handles this — it could get OCR'd as stray characters, or the line could get misread as a value. **Do not confuse this with the "tally" type** (Phase 2, separate handler). If Textract mishandles dots/lines, we may need a small custom post-processing handler for "line-through = blank" — not coded yet, design after seeing real Textract output.

**How to resume ("let's resume"):**
1. Start (or confirm running) agent server on 8071: `cd agent/server && source .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8071 --reload`
2. Start (or confirm running) good-shepherd server on 8070: `cd ~/src/github.com/bprashanth/good-shepherd/server && source ../.venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8070 --reload`
3. Health check: `curl localhost:8071/agent/health` and `curl localhost:8070/api/health`
4. Start PWA dev server: `cd pwa && npm run dev` (proxies `/api`→8070, `/agent`→8071)
5. Browser test with `LeafLitterBiomass.pdf` from `/media/desinotorious/T7 Shield/partners/shankar/forms/DatasheetScans/` — focus on: (a) how dots/lines in cells come through Textract/typeMap, (b) if a serial column appears, exercise the serial CheckCard's "Run check" → "Renumbered 1–N ✓" path.
6. If dots/lines cause issues, design a small handler for "line-through = blank entry" (distinct from tally type) before moving to Phase 2.

**How to apply:** When user says "let's resume" or "continue testing", run the steps above with `LeafLitterBiomass.pdf` as the test file — don't re-test the already-confirmed flow on `TreePlots20mx20m.pdf`, focus on the serial-card path and the dots/lines notation gap.
