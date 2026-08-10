# Phenology form (eval_09 / TreePhenologyTwoTrails.pdf) — diagnosis and experiments

Investigating the reported complaint that columns filled in on the paper come
out ignored, on production job `1266657c-1aa4-4a3d-bc1c-25d0b329d178`.

Everything below is **n = 1 form** unless stated. Total API spend: **$0.56**.

---

## 1. The headline: production is worse than reading nothing

The scan is byte-identical to our benchmark copy (sha256
`a653b94c…78d2c`), so this is not an input difference.

Production emitted 212 rows and every phenophase column is a **constant**:

| column | production emitted | golden |
|---|---|---|
| LEAVES-Flush | **blank, all 212 rows** | varies 0–4 |
| LEAVES-Mature | `4` × 212 | mostly 4, but varies |
| LEAVES-Fallen | `Y` × 212 | varies Y/N |
| FLOWERS-Buds/Open/Fallen | `0`/`0`/`N` × 207, `X` × 5 | varies |
| FRUITS-Unripe/Ripe/Fallen | `0`/`0`/`N` × 212 | varies |

The printed columns (Tree No, Species, H, GBH) are near-perfect. The nine
hand-filled columns — the actual data, ~40% of the form — were not read.

The model **said so** in its final message, which is in `run.log`:

> "All handwritten phenology cells were yellow-filled because many marks were
> difficult to distinguish confidently."

The cells really are yellow-filled (`FFFF00`). But it filled them with a guess
rather than leaving them empty, so the artifact looks complete.

**The null baseline.** `cellacc.py --null` fills each column with that column's
most common value in the golden — i.e. reads nothing at all:

| | pheno-column accuracy |
|---|---|
| null baseline (reads nothing) | **0.783** |
| **production** | **0.725** |

Production is **below the do-nothing floor**. Per-column it is almost exactly
the null: Mature 0.943 vs 0.943, Fallen 0.605 vs 0.605, Unripe 0.738 vs 0.738,
Ripe 0.905 vs 0.905. It is the null model, minus the Flush column it left blank,
plus five `X` marks.

The null is that high because the true distribution is mode-dominated. Which is
exactly why the multiset metric could not see any of this.

## 2. Why nobody caught it: the metric rewards fabrication

`wide_diff` scores token **multisets**. Production's fabricated output scores
**ALL-F1 0.899** against the golden — 4th of 15 on our leaderboard, above
qwen3.7-flash and gemini-2.5-flash.

`cellacc.py` keys each row by its printed Tree No (globally unique across all
six pages, so it survives the single-sheet flattening) and compares field by
field. Re-ranking the same 15 outputs:

| candidate | multiset F1 | **pheno acc** | coverage | false-fill | max constancy |
|---|---|---|---|---|---|
| gemini-3.6-flash perpage | 0.937 | **0.854** | 1.00 | 36 | 0.97 |
| codex CLI (benchmark run) | 0.947 | **0.853** | 1.00 | 51 | 0.96 |
| gemini-3.5-flash perpage | 0.943 | **0.849** | 1.00 | 36 | 0.96 |
| — null baseline — | — | **0.783** | — | — | 1.00 |
| **PRODUCTION (codex, live)** | 0.899 | **0.725** | 1.00 | 65 | **1.00** |
| qwen3.7-flash agentic | 0.878 | 0.601 | 1.00 | 164 | 0.76 |
| qwen2.5-vl-72b perpage | **0.917** | 0.484 | **0.64** | 71 | 0.89 |
| gemini-2.5-flash perpage | 0.876 | 0.413 | 0.97 | 181 | 0.94 |
| gemma-3-12b agentic | 0.654 | 0.187 | 0.66 | 201 | 0.96 |

**Only three configurations beat the null.** Everything else would be improved
by deleting the model and stamping the modal value.

The two metrics are nearly uncorrelated in the middle of the table:
qwen2.5-vl-72b ranks 4th on multiset F1 while reading 0.484 and covering only
64% of rows. Note also that the earlier finding "qwen2.5-vl-72b has the best
single-character accuracy (code-F1 0.905)" is an artifact of the same blindness
— it skipped a third of the rows, and multiset precision does not punish that.

**Golden QA.** Because everything rests on the golden, I re-read 69 phenophase
cells myself off a high-zoom crop and compared: **69/69 agreement**. The golden
is sound on the columns in question.

## 3. Why production does this — it is the prompt

`good-shepherd/agents/formidable/prompts/codex_prompt.md`:

1. **The quality bar is inverted.** "Every table, heading, metadata field, and
   grid visible on the page must show up in `v2` — that's the non-negotiable
   part. **Beyond that**, use your turn budget to verify and correct cell
   values." Structural completeness is mandatory; value accuracy is
   discretionary. The model optimised exactly what it was asked for: a
   complete-looking 212-row table with invented values.
2. **Uncertainty has no blank option.** "For any cell where you're not confident
   even after cropping, apply yellow fill." It never says what value to write,
   so writing a plausible one is the path of least resistance. Blank is
   sanctioned only for the unrelated "line struck through cell" rule.
3. **No zoom budget is enforced.** It took **one crop per page** (bboxes like
   `[.10,.11,.93,.89]` — the whole page), 52,368 tokens, 3 minutes, and stopped.
   It visited all six pages, so this is not the page-level coverage failure we
   documented before — it is the same failure one level down: it never zoomed
   into the narrow columns where the data is.
4. **The form's own legend is unused.** The page prints its codebook
   (`0: 0% of canopy … 4: 76–100%`, plus Y/N rules). Codex transcribes it into
   rows 258–264 of the output and never applies it as a constraint.

The benchmark harness has the same bias from the other direction: `PAGE_PROMPT`
in `wide_bench.py` ends **"Better an uncertain value than an omission."** So
both the production prompt and the evaluation prompt actively instruct the model
to fabricate, and the metric rewards it. Two mutually reinforcing errors.

## 4. What I tried

### 4.1 Anti-fabrication prompt (`prompts/page_v1_noguess.txt`)
Inverts the bar (reading the handwriting is the task), forbids inventing,
forbids copying the row above or the column mode, and adds a self-check: *if
every row of a column has the same value, you have not read that column.*

### 4.2 Legend prompt (`prompts/page_v2_codebook.txt`)
V1 plus: read the form's printed legend and use it to constrain each column's
legal values; sub-columns under one group heading may hold different types;
listed the genuinely confusable glyph pairs (4/H/Y, 0/O, N/M).

| model | baseline | V1 no-guess | V2 legend |
|---|---|---|---|
| gemini-2.5-flash | 0.413 (ff 181) | **0.552** (ff 165) | **0.588** (ff 90) |
| gemini-3.5-flash | 0.849 (ff 36) | **0.859** (ff 31) | **0.770** (ff 85) |

**Prompt scaffolding helps the weak model and hurts the strong one.**
2.5-flash gains **+0.175** and halves its false-fills. 3.5-flash gains +0.010
from V1 and **loses 0.079** from V2 — the "constrain to legal values"
instruction makes it snap ambiguous glyphs onto the legal set instead of
abstaining (false-fills 31 → 85).

This mirrors the harness finding in reverse: match the intervention to the
model's capability, don't share one across tiers. Even so, 2.5-flash at 0.588
is still far below the 0.783 null — no prompt makes it usable on this form.

### 4.3 High-zoom narrow-column bands (`band_bench.py`) — FAILED
Hypothesis: the nine columns are single characters ~30px wide, and the 1568px
vision cap leaves too few pixels per glyph. So: cut the table into horizontal
bands, drop the wide text columns (Species, Notes), composite the key column
beside the code block, staple the header on top. This gives **2.2× more pixels
per glyph** and the crops are visibly far more legible.

It does not work.

| | pheno acc | coverage |
|---|---|---|
| baseline perpage | **0.849** | 1.00 |
| band, rule-stepped | 0.495 | 0.65 |
| band, fixed-step + pinned schema | 0.492 | 0.62 |
| baseline, **page 1 only** | **0.944** | 37/37 |
| band, **page 1 only** | 0.861 | 37/37 |

The reading is genuinely good where the geometry is right — the first twelve
rows of page 1 come back **exactly** correct, all nine columns. But even on
page 1 with complete row coverage, bands lose to the plain baseline. And the
plumbing fails at scale:

- **Row coverage 62%.** `hlines()` misses faint rules on a skewed scan, so
  bands skipped rows. Switching to uniform fixed-height stepping did not fix it.
- **Output arity drifts.** Survey 1 mostly returned the intended 10 fields;
  survey 2 mostly returned 14. Pinning the schema in the prompt did not fix it.
- **Row renumbering.** The model emitted trees 6, 10 and 26, which do not exist
  — the IDs on this form are deliberately non-consecutive. It "repaired" the
  gaps even when told not to.
- **Blind column detection does not work.** Vertical-rule projection found 0–5
  of ~16 rules at any threshold: the scan is skewed enough that a rule drifts
  across x faster than the projection can resolve, and handwriting crosses the
  rules. I had to supply the x-ranges by hand (`--keep-frac`), which is exactly
  the thing a blind pipeline cannot do.

This is the same wall as template fingerprinting and printed-layer subtraction:
**you cannot recover this form's geometry from its pixels.** With the geometry
given, the ceiling looks high. Without it, don't.

### 4.4 Per-cell consensus — WORKS, and gives a usable confidence signal

Majority vote per cell across existing outputs, no new API calls:

| | pheno acc |
|---|---|
| gemini-3.6 alone | 0.854 |
| codex alone | 0.852 |
| gemini-3.5 alone | 0.848 |
| clean vote (3.5 + 3.5-v1 + 72b) | 0.855 |
| **vote: 3.5 + 3.6 + codex** | **0.884** |
| vote: all five | 0.875 |

**+0.030 over the best single model.** Caveat: two of those three helped build
the goldens, so the true gain is smaller; the clean vote only managed +0.007,
but its members are weakly diverse (two are variants of the same model).

The more useful result is disagreement as a confidence signal:

| | share of cells | accuracy |
|---|---|---|
| all three agree | 83% | **0.930** |
| they disagree | 17% | **0.658** |

**Flagging the 17% of cells where three models disagree surfaces 50% of all
remaining errors** — a ~3× concentration of reviewer attention. Since a human
reviews this output anyway, that is worth more than the +0.03.

## 5. What I'd do, in order

1. **Fix the production prompt.** Invert the quality bar, and make blank the
   sanctioned output for unreadable cells — yellow fill should mean *empty and
   flagged*, not *guessed and flagged*. Add the constancy self-check. This is a
   text edit to `codex_prompt.md` in the backend repo; it is the whole
   difference between 0.725 and "at least honest".
2. **Fix the evaluation prompt too** — `PAGE_PROMPT`'s "Better an uncertain
   value than an omission" biases every benchmark we have run.
3. **Adopt `cellacc.py` as the primary metric**, with the null baseline printed
   next to every result. Any config below the null is not reading.
4. **Ship consensus + disagreement flagging** if per-form cost allows: ~$0.09
   for two Geminis, +0.03 accuracy, and a reviewer queue that is 3× denser in
   real errors.
5. **Force zoom in the agentic loop.** Production stopped at one whole-page crop
   per page. A minimum crop count, or deterministic sub-page crops it must
   process, addresses the level below page coverage.
6. Do **not** pursue blind band/column cropping without known geometry.

## 6. Caveats

- **n = 1 form.** Every number here is one form. The prompt effects were
  measured on two models and are large enough (+0.175 / −0.079) that direction
  is probably real; the +0.030 consensus gain is not.
- Two of the five outputs used in the consensus test helped build the golden.
- The band x-ranges were hand-supplied; that experiment is not a blind result.
- I overwrote the gemini-2.5-flash baseline artifact mid-session by running a
  variant to the same output path, then renaming. It has been regenerated and
  baselines are now copied to `outputs/_baseline/` first. The 0.413 figure
  quoted for it is from the original run.
