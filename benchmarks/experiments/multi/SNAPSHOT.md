# Multi-PDF Codex+Textract experiment — progress snapshot

**Goal**: Validate the "exp2" recipe (Codex CLI in Docker, `~/.codex/auth.json`
mounted, Textract `v1.json` provided, crops/zoom allowed via
`render_page.py`, crop-friendly `system_prompt_crops.md`, no turn cap) across
5 PDFs that look structurally different from `TreePlots20mx20m.pdf` (already
tested — exp2 succeeded there: 6 crops, ~72K tokens, full 8-col ground-cover
grid reconstructed, 26-row trees table mostly correct).

For each PDF we (a) build a hand-made "golden" reference by looking at the
rendered page ourselves, (b) run the codex flow, (c) diff codex's output
against the golden. This tells us where Textract/prompt/tool scoping breaks
down — i.e. what to scope vs descope for the production agent.

All work happens under
`/home/desinotorious/src/github.com/bprashanth/form-idable/temp/experiments/multi/`
(NOT `/tmp` — survives container restarts). Source PDFs live at
`/media/desinotorious/T7 Shield/partners/shankar/forms/DatasheetScans/`.

Reusable docker image: `formidable-codex-exp` (already built in the previous
phase — Dockerfile at `../docker/Dockerfile`, has codex CLI 0.139.0 +
pymupdf/openpyxl/numpy/Pillow). Reuse the same image; rebuild only if missing
(`docker images | grep formidable-codex-exp`).

Reusable prompt template: `../shared/system_prompt_crops.md` (the crop-
friendly prompt that won exp2). Per-PDF, fill `{input_file}`=`input.pdf`,
`{page}`=as chosen below, `{render_tool}`=`/workspace/render_page.py`, then
append the same task-instruction suffix used for exp2 (see
`../exp2/full_prompt.md` for the exact wording).

## Selected PDFs (5, across tiers, structurally different from TreePlots)

| # | PDF | Tier | Page | Why picked | Status |
|---|-----|------|------|-----------|--------|
| 1 | GrowthSurvivalMonitoring.pdf | 1 | 1 | Landscape, different columns (S.no/T_no/Species/Basal_Dia_1/2/Shoot_L/Crown_Dia/Survival/Remarks) | DONE — strong match, see COMPARE.md |
| 2 | LeafLitterBiomass.pdf | 1 | 1 | Portrait, all-numeric grid (Trap ID, Fresh/Dry/Leaf/Twig/Flower/Fruit/Seed/Other) | DONE — strong match incl. missing column + off-table section, see COMPARE.md |
| 3 | RegenerationPlot5mx5m.pdf | 2 | 1 | Tally marks (III, IIII 1) — tests the "descope pencil scribbles" decision against actual tally counts (which we explicitly do NOT want to descope) | DONE — strong match, see COMPARE.md |
| 4 | TreePhenologyTwoTrails.pdf | 2 | 1 | Very wide landscape, 12+ columns, single-char Y/N/0 cells | DONE — essentially identical, see COMPARE.md |
| 5 | GridVegetation100mx100m.pdf | 3 | 1 | Two complete form-sheets on one page — structural stress test | DONE — strong structural match, all quadrant grids recovered, see COMPARE.md |

## Per-PDF pipeline (repeat for each row above)

Workdir: `./temp/experiments/multi/<stem>/` (stem = pdf filename without
`.pdf`, lowercased), containing:

- `input.pdf` — copy of source page's PDF
- `render_page.py` — copy of the shared crop/zoom tool
- `v1_overview.png` — rendered overview (zoom 2), FREE (pymupdf)
- `v1.json` — Textract `simplify()` output (TABLES+FORMS+LAYOUT), COSTS ~$0.05-0.10/page — cache, never re-call
- `golden.md` / `golden.xlsx` — hand-built reference (Claude looks at v1_overview.png + v1.json + crops as needed, writes out what SHOULD be in v2)
- `system_prompt_filled.md`, `full_prompt.md` — templated prompt for codex
- `output.xlsx`, `v2_meta.json`, `last_message.txt`, crop_*.png — codex run artifacts
- `run.log` — full codex stdout/stderr
- `COMPARE.md` — diff notes: codex output vs golden, what broke and why

Steps:
1. [ ] copy input PDF page → `input.pdf`, copy `render_page.py`
2. [ ] render `v1_overview.png` (free)
3. [ ] Textract call → `v1.json` (costs money, do once)
4. [ ] Claude builds `golden.md`/`golden.xlsx` by inspecting v1_overview.png/v1.json (+ targeted crops if needed)
5. [ ] fill `system_prompt_crops.md` → `full_prompt.md`, run codex in docker (mount auth.json, `--dangerously-bypass-approvals-and-sandbox --skip-git-repo-check`)
6. [ ] compare codex `output.xlsx` vs `golden.xlsx`, write `COMPARE.md`

## Overall status

- [x] PDF 1: GrowthSurvivalMonitoring — DONE, strong match
- [x] PDF 2: LeafLitterBiomass — DONE, strong match
- [x] PDF 3: RegenerationPlot5mx5m — DONE, strong match
- [x] PDF 4: TreePhenologyTwoTrails — DONE, essentially identical
- [x] PDF 5: GridVegetation100mx100m — DONE, strong match, all 4 quadrant grids recovered
- [x] Final summary written — see FINAL_SUMMARY.md

## Resume instructions

If interrupted: check this file's checkboxes, find the last incomplete PDF's
workdir, check which of its files exist (v1.json existing = Textract already
paid for, don't recall `analyze()`; golden.xlsx existing = golden already
built, don't redo). Continue from the first unchecked step.
