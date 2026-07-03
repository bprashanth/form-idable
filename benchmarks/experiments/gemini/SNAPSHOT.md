# Gemini / codex-only experiments — progress snapshot

**Goal**: Evaluate alternatives to the Textract+codex pipeline on
GridVegetation100mx100m.pdf (3 pages, 6 form-sheets). Three sub-experiments
launched after reviewing the two Gemini baselines.

All work is under:
- `temp/experiments/gemini/gridvegetation100mx100m/` — Gemini direct-PDF runs
- `temp/experiments/codex_only/gridvegetation100mx100m/` — codex without Textract

Source PDF: `/media/desinotorious/T7 Shield/partners/shankar/forms/DatasheetScans/GridVegetation100mx100m.pdf`  
Local copy: `temp/experiments/gemini/gridvegetation100mx100m/input.pdf`  
(Same file as `temp/experiments/multi/gridvegetation100mx100m/input.pdf`)

Textract v1.json (page 1 only, already paid for):
`temp/experiments/multi/gridvegetation100mx100m/v1.json`

Golden reference (page 1 = M13+L13 forms):
`temp/experiments/multi/gridvegetation100mx100m/golden.xlsx`
`temp/experiments/multi/gridvegetation100mx100m/golden.md`

Final comparison document (all 5 experiments):
`temp/experiments/gemini/gridvegetation100mx100m/COMPARE_all_experiments.md`

---

## Experiment inventory

| ID | Status | Dir | Key files |
|----|--------|-----|-----------|
| **Baseline 1**: gemini-3.5-flash + thinking | DONE | `gemini/gridvegetation100mx100m/` | `output_gemini-3.5-flash.xlsx`, `raw_gemini-3.5-flash.txt`, `meta_gemini-3.5-flash.json`, `COMPARE_gemini-3.5-flash.md` |
| **Baseline 2**: gemini-2.5-flash + thinking | DONE | `gemini/gridvegetation100mx100m/` | `output_gemini-2.5-flash.xlsx`, `raw_gemini-2.5-flash.txt`, `meta_gemini-2.5-flash.json` |
| **Exp A**: gemini-3.5-flash, no thinking, pdf-only | DONE | `gemini/gridvegetation100mx100m/` | `output_gemini-3.5-flash-nothink.xlsx`, `raw_gemini-3.5-flash-nothink.txt`, `meta_gemini-3.5-flash-nothink.json` |
| **Exp B**: codex-only, no Textract (gpt-5.5) | DONE | `codex_only/gridvegetation100mx100m/` | `output.xlsx`, `last_message.txt`, `run.log` (115,750 tokens) |
| **Exp C**: gemini-3.5-flash, no thinking, +v1.json | DONE | `gemini/gridvegetation100mx100m/` | `output_gemini-3.5-flash-nothink-v1.xlsx`, `raw_gemini-3.5-flash-nothink-v1.txt`, `meta_gemini-3.5-flash-nothink-v1.json` |

---

## Key numbers (all runs complete)

| Exp | Tokens | Cost | Time |
|-----|--------|------|------|
| Baseline 1 (3.5-flash+think) | 14,577 (8,795 think) | ₹13.23 empirical | 56.8s |
| Baseline 2 (2.5-flash+think) | — | ~₹1.96 | — |
| Exp A (3.5-flash no-think) | 6,157 (0 think) | ₹0.24 | 24.7s |
| Exp B (codex-only gpt-5.5) | 115,750 | ~$0.50–1.00 est. | ~6 min |
| Exp C (3.5-flash no-think +v1) | 33,212 (0 think) | ₹0.57 | 28.7s |

---

## Headline findings (see COMPARE_all_experiments.md for full detail)

1. **Exp A is the best cost/quality tradeoff**: ₹0.24, 6 forms, 4 Q columns,
   correct absent-species checkboxes. Two promptable gaps: no uncertainty flagging,
   some checkbox notation inconsistency.

2. **Exp C (Textract+Gemini) actively hurts multi-page quality**: v1.json covers
   only page 1 (M15 forms), so adding it for a 3-page PDF causes cross-page
   contamination — page 2-3 checkboxes go wrong (absent species show Tick).
   If v1.json is ever fed to Gemini, it must cover the exact page being read.

3. **Exp B (codex-only)**: Most thorough (correct continuous-line/blank notation,
   yellow flags, ambiguous-species detection), but expensive (115K tokens) and
   produces a flat single-sheet structure.

4. **Thinking tokens = 98% of Baseline 1's cost, marginal quality gain**: not
   worth it for production.

5. **Canopy grid**: Exp C produced the best structure (separate NW/NE/SW/SE
   sheet) despite worst checkbox quality. Exp B got values right in free-text.
   Exp A got M13 composition wrong (N→M).

---

## How to run the Gemini script (if re-running)

```bash
cd temp/experiments/gemini/gridvegetation100mx100m/

# Exp A: 3.5-flash, no thinking, pdf-only
python3 run_gemini.py --model gemini-3.5-flash --no-thinking

# Exp C: 3.5-flash, no thinking, +v1.json
python3 run_gemini.py --model gemini-3.5-flash --no-thinking \
  --v1-json ../../multi/gridvegetation100mx100m/v1.json
```

GEMINI_API_KEY is in `/home/desinotorious/src/github.com/bprashanth/good-shepherd/agents/formidable/.env`.
Raw response is cached (`raw_<slug>.txt`) — the xlsx can be rebuilt from the raw file
without calling the API again by editing run_gemini.py to skip the upload/generate and
just load `raw_<slug>.txt` directly.

## How to run the codex-only experiment (if re-running)

```bash
cd temp/experiments/codex_only/gridvegetation100mx100m/
timeout 540 docker run --rm -i \
  -v "$(pwd)":/workspace \
  -v /home/desinotorious/.codex/auth.json:/root/.codex/auth.json:ro \
  -w /workspace \
  formidable-codex-exp \
  codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
  -C /workspace -o /workspace/last_message.txt - \
  < full_prompt.md > run.log 2>&1
```

Docker image: `formidable-codex-exp` (already built; Dockerfile at
`temp/experiments/docker/Dockerfile`).

---

## What's next (not yet done)

- [ ] Prompt engineering pass on Exp A to close the two promptable gaps:
      (a) uncertainty flagging — prompt currently says `" (?)"` on uncertain reads,
          Gemini ignored it; try asking for a separate "uncertain_cells" JSON array instead
      (b) checkbox normalization — prompt currently unspecified; add explicit rule:
          "represent all checked boxes as `X`, all unchecked boxes as blank (empty string)"
- [ ] Test whether per-page v1.json (instead of full-PDF v1.json) fixes Exp C's
      cross-page contamination
- [ ] Two-stage hybrid: Gemini first-pass (Exp A) → codex targeted re-read of
      flagged/ambiguous cells only
- [ ] Extend any of the above to a second PDF (different tier) to check generalization
