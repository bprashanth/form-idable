# benchmarks/wide — form transcription: what we tried, what worked, what didn't

Successor to `benchmarks/FINDINGS_treeplots.md`. That study asked "can a cheap
model match codex on ONE ecology form". This one asks the harder questions:
how well does a **local, private** model do on **many** form types, what
architecture should wrap it, and what is actually making it hard.

**Read `FINDINGS_wide.md` for round 1, `FINDINGS_evals_tree.md` for the partner
eval, and `CHECKPOINT.md` for the full chronological log including failures.**

## Current frontier-model phase (2026-08-06)

The older local-model work below remains historical evidence, but the active
system is now an API/CLI-only, integrity-first prototype. No local model or GPU
job is used in this phase. Read `../../chronology/000_scope_and_audit.md`
through `008_frozen_false_routes.md` in order.

Current components:

| file | current role |
| --- | --- |
| `integrity_eval.py` | exact page/row/column, blank invention, omission, duplication, and modal-control metrics |
| `structured_pipeline.py` | unknown-form canonical structure plus independent literal readers |
| `template_pipeline.py` | recognised blank template, exact merged lattice, whole-page or band reader |
| `template_match.py` + `template_labels.py` | abstaining pixel shortlist plus independent printed-label confirmation |
| `frozen_routing_eval.py` | one-shot false-route test on frozen real partner pages; never a threshold tuner |
| `ecology_review.py` | separate physical/outlier/GBIF flags; never silently edits transcription |
| `review_manifest.py` | stable transcription-attention and ecology-anomaly contract |
| `pipeline_v2.py` | local-only orchestrator; contains no AWS/deploy operation |

The accepted span-aware synthetic corpus is
`struct_eval_v5_exact_spans/`: 84 forms, 42 template pages, 20,238 ruled
cells, 8,178 written cells, and zero value/bbox/span/workbook audit failures.
`struct_eval_v4_exact_semantic/` remains as the experiment record but its Excel
renderer omitted merged-header spans; do not use it for new layout claims.

Route-only check using already cached generic structure (no provider call):

```bash
python3 pipeline_v2.py eval_forms/eval_09 \
  --templates downloads/templates \
  --registry template_registry_v2.json \
  --tag canonical_v1_full --reuse-structure --route-only
```

Full local quality pipeline (provider calls, but still no AWS writes):

```bash
python3 pipeline_v2.py /path/to/form_dir \
  --templates downloads/templates \
  --registry template_registry_v2.json \
  --tag formidable_v2
```

The output directory contains `route.json`, `output.xlsx`,
`review_manifest.json`, `ecology_review.json`, and `run.json`. A document uses
the exact-template branch only when every page clears both identity gates;
otherwise the entire document safely falls back to the generic canonical path.

The fixed pixel shortlist alone falsely nominated 11/78 frozen unknown real
pages (14.1%), including visually unrelated layouts. It is therefore never an
identity decision. The one available actual printed-label check and 11/11
workbook-token proxies rejected those candidates, but exact routing remains
experimental until it has real duplicate-capture positives and more actual
structure-gate negatives. See `../../chronology/008_frozen_false_routes.md`.

---

## TL;DR

- **A local Qwen3-VL-2B can *read* these forms about as well as gemini-2.5-flash**
  (recall 0.86 vs 0.83). Its problem was never perception.
- **It could not stop generating.** It read pages correctly and then invented
  rows — 17 forms scored exactly 0 while having recall above 0.5.
- The cause was **my training data**: 100% densely-filled forms taught it that
  pages are full of rows. Fixing that was worth **+0.224 ALL-F1** on unseen
  layouts. Over-correcting toward sparse then cost **-0.145** on dense forms.
- **The output is not review-ready even when the tokens are right.** It emits a
  flat CSV that does not match the form's layout — header fields linearised,
  column headers dropped, inconsistent column counts per row. Token-multiset
  scoring is blind to this, which is why the metric looked better than the
  product was. **This, not accuracy, is the current blocker.**
- Three "clever" ideas failed and are recorded so they are not retried:
  template fingerprinting, printed-layer subtraction, degenerate-tail trimming.

## Where the local model stands (24 real partner forms, ALL-F1)

| model | ALL-F1 | $/100 forms | sec/form | notes |
|---|---|---|---|---|
| qwen3-vl-32b (OpenRouter) | 0.849 | **$0.39** | 99 | *contaminated — helped build goldens* |
| codex CLI | 0.846 | subscription | **649** | *contaminated*; the current prod extractor |
| gemini-2.5-flash | 0.780 | $5.80 | 102 | clean |
| **local 2B v2** | 0.519 | **$0** | 174 | dense-trained |
| qwen3-vl-8b (OpenRouter) | 0.518 | $0.84 | 169 | clean |
| **local 2B v3** | 0.473 | **$0** | 153 | sparse-trained; better on photos, worse on dense scans |

On the 76-form structure-diverse eval (real templates, none seen in training)
v3 reaches **0.575** vs v2's 0.351 — the sparse-fill fix.

## What we tried, ranked by measured effect

| lever | effect | kind | verdict |
|---|---|---|---|
| training fill-density matching deployment | **+0.224** | data | biggest win; over-shooting cost -0.145 |
| structured row-band cropping (known template) | **+0.089** | architecture | works; recall 0.70 -> 0.86 |
| output cap sized to the page | +0.14 (simulated) | architecture | not yet deployed |
| repetition penalty at inference | large on affected forms | inference | shipped as default |
| real SD-19 ink instead of handwriting fonts | (round 1) | data | shipped |
| tiling vs one-shot rendering | +0.11 recall on high-DPI | inference | shipped; pick by source DPI |
| degenerate-tail trimming | **-0.017** | inference | **FAILED** — see below |
| printed-layer subtraction | **-0.114** | architecture | **FAILED** |
| template fingerprinting (auto-route) | precision 0.00 held out | architecture | **FAILED** |

### Why the three failures failed
- **Tail trimming**: both signals are confounded with real content. Ecology
  tables are legitimately repetitive (`N N N N N`), and a serial-number column
  *is* an arithmetic progression, so the detector cut good tables in half.
- **Printed-layer subtraction**: handwriting overlaps printed rules, so erasing
  print erases parts of digits; the model also uses printed context.
- **Fingerprinting**: hand-built geometry scored precision 0.00 on held-out
  templates; DINOv2 was 3x better but still 0.75/0.30. **Ask the user which
  form it is** instead of guessing.

## What makes it hard — measured, not assumed

| factor | effect on ALL-F1 |
|---|---|
| photo degradation (clean vs heavy) | 0.564 -> 0.586 — **none** |
| form structure / table size | large tables score *best* (0.660) — not the problem |
| fill density | 0.546-0.596 — minor |
| single-letter code columns | 0.648 -> 0.545 (**-0.10**) |
| **synthetic vs real handwriting** | 0.575 -> 0.473 (**-0.10, largest**) |

By content type on real forms: numbers 0.531, codes 0.567, **words 0.475**.

So the difficulty is, in order: **real cursive/pencil ink** (our synthetic ink
is hand-PRINT), **sector vocabulary** (a VLM reads handwriting through language
priors — "Boothahami" is unreadable unless the word is in-distribution, and
this compounds with cursive), and **single-character code ambiguity** (N/M/W,
L/C/E, 4/H/Y) which needs the column's value domain to resolve.
**Photo quality and form structure are NOT the bottleneck** — which was
surprising and redirected effort away from camera realism.

## Evaluation — and two bugs in it that we caused

Three eval sets, all with the training/eval split enforced by a shared hash:

1. `eval_forms/` — **24 real partner forms** (14 scans + 10 field photos),
   goldens by 3-5 converter median consensus, one hand-adjudicated (eval_02).
2. `struct_eval/` — **76 forms from 38 real blank templates** downloaded from
   the web (NVS NZ, AGRRA, EPA, Himachal Pradesh Forest Dept, Kew, NRCS…),
   filled synthetically so goldens are exact. Structure/handwriting/conditions
   vary independently. 10 templates held out from training forever.
3. Round-1 17-form cross-sector suite (see `FINDINGS_wide.md`).

**Bug 1 — the scorer ignored 59-70% of the hardest forms.** It inherited
`len(token) >= 2` from the tree-plot code, discarding single characters as OCR
noise. In this domain single letters *are* the data. Fixed by adding `code_*`
and `all_*` buckets; immediately revealed gemini beats codex on codes
(0.839 vs 0.803) while losing on numbers.

**Bug 2 — three scripts hard-coded metric lists** and silently dropped the new
buckets, once producing a fabricated "v3 scores 0.000". All now propagate
whatever the scorer emits.

Both were the same failure: a hard-coded assumption quietly discarding data.

## Layout: the real blocker

The model can be token-accurate and still useless. Current output for a form
with columns `S.No | SPP Name | Habit | DBH | Phenology`:

```
Date,19/02/2025                                    <- header fields linearised
Area Name,BKM
S.No,SPP Name/Local Name,Phenological condition,1  <- 2 columns DROPPED
1,Coburn,T,23,Fruity                               <- 5 cells
2,Coag,T,9+2+3+4+2+5                               <- 4 cells, no longer aligned
```

A reviewer cannot diff that against the paper. **The next phase should target a
form-shaped xlsx**: given a known blank template, emit a sheet with the same
grid and place each value in its own cell. `structured_extract.py --mode band`
already extracts per row-band with known columns, which is most of the way
there; what is missing is writing into a grid rather than concatenating lines.

## Files

| file | what it does |
|---|---|
| `wide_bench.py` | harness: providers (gemini/openrouter/local/textract), modes oneshot/tiled/perpage |
| `wide_diff.py` | scorer: recall + precision + F1, with `code_*` and `all_*` buckets |
| `consensus.py` | builds goldens from N converters by per-token median; refuses to clobber hand-adjudicated ones |
| `gen/formgen2.py` | synthetic forms: real SD-19 ink, sparse fill, pencil, vernacular names, page furniture |
| `gen/photo_aug.py` | phone-camera pipeline: perspective, page bow, finger, shadow, background |
| `gen/fill_template.py` | fills a REAL blank template read from PDF vectors — exact goldens, no CV thresholds |
| `gen/build_struct_eval.py` / `build_train_corpus_v3.py` | eval / training corpora with the shared dev-test split |
| `gen/train_lora_v2.py` | LoRA trainer; `--gpu-frac` is the only thing that actually bounds GPU memory here |
| `structured_extract.py` | tier-3: align to template, crop row-bands, per-band extraction |
| `template_id.py` | fingerprinting (FAILED — kept as the record) |
| `detrail.py` | tail trimming (FAILED — kept as the record) |
| `serve_ui.py` | local web UI: upload a form, get a table + xlsx, nothing leaves the box |
| `gpu_run.sh` | **the only sanctioned way to start a GPU container here** |

## Reproducing

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install augraphy opencv-python-headless transformers torch torchvision
python3 gen/build_glyphbank.py downloads/sd19/by_class assets/glyphs 60
.venv/bin/python3 gen/build_struct_eval.py downloads/templates struct_eval --per 2
./gpu_run.sh ...                      # never plain `docker run --gpus all`
python3 rescore.py eval_forms struct_eval && python3 analyze_evals.py
```

## Host safety (read before any GPU job)

This GB10 shares 121 GB between CPU and GPU. An uncapped container **hard-freezes
the box** — it happened twice on 2026-07-31. `docker --memory` does NOT bound
GPU memory (measured: container RSS 6.9 GB while the system lost 54 GB); only
`torch.cuda.set_per_process_memory_fraction()` does. Always launch via
`gpu_run.sh`, never auto-chain GPU jobs, and after any abrupt session death run
`last -x reboot` before relaunching anything.
