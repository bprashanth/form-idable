# Agent task: wide cross-sector form-transcription benchmark

You are taking over on a second machine that was set up by rsyncing two repos
(`form-idable` + `good-shepherd`). Before anything else, read
`../CLAUDE.md` -> "Taking over on another machine" and confirm your environment:
`codex login` works (`codex --version`), the API keys exist under
`~/.config/formidable/` (`gemini.json`, `openrouter.json`, each with an
`api_key` field), and `python3` can import `fitz`, `openpyxl`, `PIL`.

## What this is

Formidable digitises handwritten field forms into structured xlsx. We have
already benchmarked model/config choices, but on a NARROW set: a handful of
ecology datasheets (Western Ghats tree-plot surveys). Your job is to REPLICATE
that benchmark and go MUCH WIDER across sectors and form types, then report
which model/config wins where, and overall.

This is offline benchmarking. Do NOT deploy, do NOT touch prod, do NOT modify
the running worker. You are measuring, not shipping.

## Read these first (do not re-derive what they already settled)

- `benchmarks/model_bench.py` — the exact harness that produced our numbers.
  Renders pages, tiles them, sends them to a provider, parses CSV -> xlsx,
  scores with the SAME tolerant diff the nightly regression uses.
- `benchmarks/FINDINGS_treeplots.md` — our results and conclusions on the seed
  form. This is the baseline you are widening. Read it fully.
- `../../good-shepherd/agents/formidable/xlsx_diff.py` — the scorer. Recall-based:
  `num_recall` (primary), `word_recall` (lenient, handwriting is noisy),
  `cell_frac` (liveness). Thresholds are env-overridable gates.
- `benchmarks/experiments/multi/SNAPSHOT.md` — the method we used to hand-build
  a "golden" reference per form and diff a run against it. Reuse this method.
- `benchmarks/TreePlots20mx20m.pdf` + `TreePlots20mx20m_merged.xlsx` — the seed
  form and its golden. Keep it in the suite as the known-anchor.

## What we already know (carry forward, do not re-litigate)

- **Baseline: codex CLI** (our prod extractor; the GPT-5-class agentic model,
  version pinned in `good-shepherd/agents/formidable/deploy/config.sh`). It
  crops/zooms agentically. On the seed form: cell ~0.85, num ~0.71, word ~0.48,
  ~300 s/form.
- **Winner so far: `gemini-2.5-flash`, tiled, reasoning OFF.** Tiled = each page
  split top/bottom and rendered near the 1568px vision cap (roughly 2x table
  detail), the deterministic stand-in for codex's crop/zoom. Reasoning off =
  `thinkingConfig.thinkingBudget = 0`, temperature 0. Result: 0.92/0.77/0.50,
  ~$0.005/form, ~12 s. Beats codex on all three metrics.
- **Open-weight alternative: `qwen3-vl-32b`** (via OpenRouter), tiled:
  0.91/0.67/0.49 at ~$0.0019/form. Matches codex, avoids Google.
- **Key lesson:** for cheap models, feeding detail deterministically (tiling)
  beats an agentic crop loop. Default to tiled; keep oneshot as the cost floor.
- **Known blind spot:** the scorer measures RECALL, not precision. Cheap models
  over-produce cells (qwen3-vl-8b hit cell_frac 1.11). Fixing this is part of
  your task (see step 5).

## The task

### 1. Source paper forms across sectors (go wide)

Gather real scanned paper forms well beyond ecology. Target several sectors,
several forms each. Prioritise HANDWRITTEN (the hard case); include mixed
print+handwriting. Vary layout deliberately: portrait and landscape, dense
numeric grids, tally/tick marks, checkboxes, multi-form-per-page, marginal
notes. Suggested sectors (not exhaustive):

- health / clinical intake, patient charts, vaccination cards
- agriculture / crop and livestock records
- logistics / warehouse counts, delivery manifests
- finance / ledgers, expense sheets, receipts
- education / attendance, grade sheets
- government / census, permit applications, land records
- lab notebooks, field surveys, insurance claim forms

Sources to consider: public form-understanding datasets (FUNSD, SROIE, CORD,
RVL-CDIP, DocLayNet), government open-data scanned-form archives, and any real
scans available on this machine. Record provenance for each form (where it came
from, licence if relevant) in that form's folder.

### 2. Build a golden per form

For each form, hand-build a golden xlsx exactly as in
`experiments/multi/SNAPSHOT.md`: render an overview, read it yourself, write out
what SHOULD be transcribed (cropping in for detail where needed). The golden is
the scoring reference. Keep the ecology notation rules consistent: a dot = 0, a
continuous line through a cell = blank/no entry, tally marks sum to an integer,
ticks/X = present.

### 3. Generalise the harness

`model_bench.py` is ecology-specific in two places you must parametrise:

- `TRANSCRIBE_PROMPT` is written for "Western Ghats 20x20m tree-plot surveys."
  Rewrite it sector-AGNOSTIC (transcribe every table, header, tally, note on
  every page; keep the notation rules above; output CSV with `### PAGE N`
  separators). Do not bake in any one domain.
- `PDF` and `GOLDEN` are hardcoded to TreePlots. Make the form path + golden
  path arguments so you can loop over the whole suite.
- Paths `FORMID`/`GSHEP` assume the default layout `~/src/github.com/bprashanth/`.
  If this machine used a different `REMOTE_PATH`, fix those two constants.

Keep everything else (tiling, cost pulls, xlsx parsing, scoring) as-is — it is
the proven code.

### 4. Run the settled model set on every form

Run these configs per form and record recall/precision/cost/latency:

- **codex CLI** — the agentic baseline (run it the way prod does; reuse the
  worker's codex invocation as reference).
- **gemini-2.5-flash, tiled, reasoning off** — our current winner.
- **qwen3-vl-32b (OpenRouter), tiled** — the open-weight alternative.
- **LOCAL MODELS — TO BE SPECIFIED.** The user will give you model IDs and how
  to reach them (likely an OpenAI-compatible endpoint from llama.cpp / Ollama /
  vLLM). Add them as another provider in `model_bench.py` alongside `gemini`
  and `openrouter`, reusing the same image-in-prompt shape. Leave this slot
  clearly marked until the user fills it; do not guess model names.

Use `tiled` as the default mode; also run `oneshot` to capture the cheap floor.

### 5. Add a precision metric (close the known gap)

Extend `xlsx_diff.py` (or add a sibling scorer next to it in `benchmarks/`) to
report PRECISION and F1 alongside recall, so over-production is penalised. Keep
the existing recall numbers so results stay comparable to
`FINDINGS_treeplots.md`. Report recall, precision, F1 per form and per model.

### 6. Track cost and latency honestly

Per form, per model: `$/form` and `seconds`. OpenRouter cost is pulled live from
its `/generation` endpoint (already wired). Gemini cost uses the price table in
`model_bench.py` — update it if the model list changes. codex is subscription
auth, so report its token count and an estimated frontier-model $ equivalent,
as `FINDINGS_treeplots.md` does. Keep a running total spend. Confirm the budget
ceiling with the user before large runs — the prior narrow run cost ~$0.02
against a $5 cap.

### 7. Deliverables

Put everything under `benchmarks/wide/`:

- one subfolder per form: `input.pdf` (or image), `golden.xlsx`, `provenance.md`,
  and per-model output `.txt` / `.xlsx` / `.json`.
- `results.csv` (+ `results.json`): rows of
  `sector, form, model, mode, recall, precision, f1, cost_usd, latency_s`.
- `FINDINGS_wide.md`: mirror the structure of `FINDINGS_treeplots.md` — results
  table, conclusions, per-sector recommendation, overall recommendation, and an
  honest caveats section (runs-per-form, recall-vs-precision, any malformed
  outputs excluded and why).

## Guardrails

- Offline only. No deploy, no prod writes, no changes to the running worker.
- Keep keys out of any committed file. They live in `~/.config/formidable/` and
  `~/.codex/`.
- One form + one run per config is enough to start; note that differences under
  ~0.05 recall are within codex's own run-to-run noise.
- When you hit the "LOCAL MODELS — TO BE SPECIFIED" slot with no spec yet, stop
  and ask the user rather than substituting a model.
