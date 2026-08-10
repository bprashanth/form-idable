# Cheaper-model experiment — can a low-cost model match codex CLI?

**Form:** `benchmarks/TreePlots20mx20m.pdf` (3-page handwritten tree-plot survey).
**Scoring:** the *same* tolerant diff the nightly regression uses (`xlsx_diff.py`)
against `TreePlots20mx20m_merged.xlsx`. Recall of golden tokens — numbers are the
reliable signal; words run low (handwriting variance); cell_frac is liveness.
**Baseline:** codex CLI 0.144.4 (current prod), which crops/zooms agentically:
cell ≈ 0.85, num ≈ 0.71, word ≈ 0.48, ~300 s/form.
**Total spend:** $0.02 (budget was $5). One form, one run per config.

## Results

| model | mode | cell | num | word | $/form | sec |
|---|---|---|---|---|---|---|
| **codex 0.144.4** (baseline) | agentic | 0.85 | 0.71 | 0.48 | ~subscr | ~300 |
| **gemini-2.5-flash** | **tiled** | **0.92** | **0.77** | **0.50** | 0.0051 | 12 |
| qwen3-vl-8b | tiled | 1.11⚠ | 0.89 | 0.46 | 0.0023 | 24 |
| qwen3-vl-32b | tiled | 0.91 | 0.67 | 0.49 | 0.0019 | 39 |
| qwen3-vl-8b | oneshot | 0.85 | 0.70 | 0.41 | 0.0024 | 31 |
| qwen3-vl-32b | oneshot | 0.84 | 0.67 | 0.46 | 0.0012 | 30 |
| gemini-2.5-flash | oneshot | 0.80 | 0.63 | 0.46 | 0.0041 | 12 |
| mistral-small-3.2-24b | oneshot | 0.69 | 0.61 | 0.35 | 0.0010 | 14 |
| amazon/nova-lite-v1 | oneshot | 0.18❌ | 0.68 | 0.42 | 0.0007 | 16 |
| openai/gpt-5-nano | oneshot | 0.03❌ | 0.01 | 0.04 | 0.0016 | 28 |

- **oneshot** = 3 full-page overviews (1568px) in one call.
- **tiled** = each page split into top/bottom halves rendered at the 1568px cap
  (~2× table detail) — the deterministic stand-in for codex's crop/zoom.
- Gemini run with reasoning OFF (`thinkingBudget=0`), temp 0.

## Conclusions

1. **Cheap models already match codex, and tiling makes them beat it.** The
   codex edge is numeric detail (num_recall), which it earns by cropping/zooming.
   Handing a cheap model the same detail via simple tiling closes and reverses
   that gap — no agentic loop needed.
2. **Winner: `gemini-2.5-flash`, tiled, no reasoning.** Beats codex on all three
   metrics (0.92/0.77/0.50), **$0.005/form, 12 s** vs codex's ~5 min. Stable
   first-party API. This is the recommendation.
3. **Open-weight alternative: `qwen3-vl-32b` (OpenRouter), tiled** — 0.91/0.67/0.49
   at **$0.0019/form**, matches codex, avoids Google.
4. **qwen3-vl-8b tiled** has the highest num_recall (0.89) but cell_frac 1.11 —
   it over-produces cells. See caveat.

## Caveats (don't over-read)

- **One form, one run each.** codex itself varied 0.82–0.87 / 0.71–0.72 across
  runs, so differences under ~0.05 are noise. Gemini-tiled's num win (0.77 vs
  0.71) is beyond that; the qwen oneshot vs codex gaps are within it.
- **Recall only, not precision.** `xlsx_diff` rewards finding golden tokens; it
  does *not* penalise invented cells. qwen3-vl-8b's cell_frac 1.11 means it
  emitted more cells than the golden — partly the tiling overlap (middle band
  transcribed twice; overlap doesn't inflate num_recall because multiset match
  caps at golden count, but it does inflate cell_frac), partly possible
  over-transcription. Gemini-tiled (cell 0.92, not over-producing) is the safer
  "best" pick. A precision metric is the obvious next eval.
- **gpt-5-nano** forces reasoning and returned almost no CSV under this prompt
  (0.03) — not a fair OCR test without prompt tuning; excluded. **nova-lite**
  emitted a near-empty/summary output (0.18) — malformed for our parser.
- Cost for codex is "~subscription" (ChatGPT auth). By tokens (~78k/form on a
  frontier model) its true per-form cost is far above $0.005 — the ~1000× gap
  holds either way.

## Reproduce

`scratchpad/experiment/run_experiment.py` (keys from `~/.config/formidable/`):
```
python3 run_experiment.py render                       # full-page overviews
python3 run_experiment.py tiles                        # top/bottom half tiles
python3 run_experiment.py oneshot|tiled <provider> <model>
```
Outputs (transcription .txt, built .xlsx, metrics .json) land in `outputs/`.
