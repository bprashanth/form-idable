# Agent vision pipeline — phasing & setup

Companion to `docs/design/shankar_poc_phasing.md`. That doc covers the
existing **deterministic** pipeline (Textract + species/serial/tally/yn
handlers, "tier 1/2/3" forms). This doc covers the **agent vision**
track that runs alongside it: a Claude Agent SDK container that looks at
the page image directly and produces a corrected, "v2" copy of the
extraction.

This is a new component, distinct from the existing
`form-idable/agent/server` ("form-idable-agent" — the deterministic
species/serial/tally/yn logic server, already deployed as a standalone
Lambda Function URL POC per `agent/server/deploy/`). To avoid confusion
this doc calls the new component the **vision agent**. It will live in
`good-shepherd/agents/formidable/` (base image in
`good-shepherd/agents/`), reusing the `form-idable-api` API Gateway and
its `cognito-jwt` authorizer (AUTH_ID `8vxlrc`) — see the new "Agent
servers" section in
`heartwood/docs/how-to/onboard-new-component.md`.

---

## Recap of the agreed design (from prior discussion)

- **v1/v2 tabs**: Textract produces the existing extraction (v1, with
  bboxes + confidence). The vision agent produces a second tab (v2) for
  the same page, by looking at the rendered page image directly.
- **Review UX**: cards (proposals to accept/skip/edit) come from v2;
  bbox highlighting comes from v1. If a v2 cell has no corresponding v1
  bbox (e.g. a row Textract dropped entirely, like Page 1's ground
  cover grid in `TreePlots20mx20m.pdf`), highlight the nearest
  surrounding v1 bbox (earliest-after / latest-before interpolation).
- **Hosting**: Claude Agent SDK running in the user's own container
  (not the hosted `code_execution` tool), so it has the same
  bash/Python tool access as the manual exploration that produced
  `temp/TreePlots20mx20m_agent.xlsx`.
- **Async pipeline**: PDF → S3 → Step Functions (TextractPass →
  AgentPass → Merge → Done) → DynamoDB job record → PWA dashboard for
  review.
- **Auth**: same `form-idable-api` API Gateway + Cognito JWT authorizer
  as good-shepherd. The vision agent gets its own per-component IAM
  execution role (S3 read for the uploaded PDF, S3 write for the
  result xlsx — same shape as `good-shepherd/server/deploy/lambda-policy.json`).

---

## Package curation for the agent sandbox

**Question**: is "the venv packages used during exploration" the right
set to bake into the container?

**Answer: no — that venv is not scoped to this task at all.** I checked
`agent/server/.venv` and it's a general-purpose system Python
environment with 250+ packages: `ansible`, `awscli`, `GDAL`, `rasterio`,
`frappe-bench`, `python-telegram-bot`, `matplotlib`, `pandas`,
`scipy`... none of that is related to PDF/image/xlsx work. It's just
whatever has accumulated on this dev machine. Baking it in would:

- massively bloat the image (GDAL/rasterio/frappe alone dwarf
  everything else) and slow cold starts
- hand the LLM-driven sandbox tools (`ansible`, `awscli`) that have
  nothing to do with the task — bad from a least-privilege standpoint
  for a sandbox an LLM has shell access to

**What was actually used** to produce `TreePlots20mx20m_agent.xlsx`:

| Package | Purpose |
|---|---|
| `pymupdf` (fitz) | rasterize PDF pages to PNG at arbitrary zoom |
| `Pillow` | crop/zoom/compose page-region images for closer inspection |
| `openpyxl` | read the v1 xlsx structure, write the v2 tab (incl. fills/fonts for uncertainty highlighting) |
| `numpy` | pixel-level operations PIL doesn't expose directly (thresholding, contrast stretch, rotation correction) — not used in the `TreePlots20mx20m` exploration but cheap to include and likely needed for messier scans (e.g. Osuri, see below) |

That's the curated **agent sandbox toolkit** — four pure-Python
packages, no system/apt dependencies (PyMuPDF bundles its own MuPDF).

This is a **different list from the server's own deps**
(`fastapi`/`uvicorn`/`boto3`/the Agent SDK package itself), which the
sandbox tools don't need — those are for the wrapper process, not for
the agent's bash/Python tool calls.

**Why not let the agent `pip install` at runtime?** Lambda's filesystem
is read-only outside `/tmp`; `/tmp` is wiped between invocations and
`pip install --target=/tmp` needs network egress most Lambda deployments
don't have configured, plus it adds latency per invocation. So: bake the
curated toolkit in at build time. If the agent hits something genuinely
missing for a new form type, that should surface as a finding/log entry
("needed X, didn't have it") during Phase 2 testing — and the curated
list gets revisited deliberately, not patched at runtime.

---

## Agent role — "ecology form detector"

### This is not a one-shot prompt

Important framing for how this prompt gets written: when this was done
manually (producing `TreePlots20mx20m_agent.xlsx`), the process wasn't
"zoom in once, read, done" — it was iterative. Render the full page,
look at it, decide it's too small to read, crop+zoom a specific region,
read that, notice something ambiguous, crop again at a different
position/scale, cross-check against an adjacent region, etc. That back
and forth is exactly what a Claude Agent SDK / Claude Code headless
invocation already supports natively: a single invocation is an
agentic loop — the model calls a tool (bash/Python), sees the result,
and decides the *next* tool call, repeatedly, until it's satisfied or
hits its turn/time budget. Nothing extra needs to be built to get this
— it's the default behavior of the SDK.

The risk is writing a prompt that *undoes* this by being too
procedural — "step 1: render at 2x, step 2: crop to bbox X, step 3:
read it" reads like a fixed pipeline and may bias the model toward a
single pass. The prompt below is written as a **goal + techniques
available**, not a numbered procedure, specifically so the model keeps
exploring (different zoom levels, rotations, contrast adjustments,
cross-referencing other pages/regions) until it's actually confident,
the same way the manual exploration did.

### Handling forms with no fixed layout (e.g. Osuri bird data)

The tier 1/2 forms have a known v1 layout to match. But the prompt
shouldn't *require* a v1 match — for the excluded/heterogeneous forms
(`2003_AnandOsuri_BirdChecklists.pdf`: free-text species lists on some
pages, a visit×species grid on others, inconsistent page sizes/
orientation), there may be no usable v1 at all, or v1 may be
structurally wrong for the page. The agent should be allowed to
**propose its own sheet structure** in that case — it won't be perfect,
but "the agent figures out *some* reasonable tabular structure for an
unseen form" is the capability we want, rather than the agent giving up
because its instructions only describe matching an existing template.
This is explicitly **not required to work well yet** (Osuri is Phase
3/4, out of scope for Phase 2) — but the prompt shouldn't actively
prevent the agent from attempting it.

### Draft prompt

> You are transcribing a scanned handwritten ecological field datasheet
> (Western Ghats forest plot surveys — tree plots, ground cover, leaf
> litter biomass, regeneration counts, bird checklists, etc.) into a
> spreadsheet.
>
> You will be given the PDF page and (usually) an existing xlsx (`v1`,
> produced by AWS Textract) with a sheet for this page. Your goal is to
> produce a `v2` sheet that is a corrected, complete transcription of
> what's actually on the page.
>
> **You have a sandbox with PyMuPDF, Pillow, numpy and openpyxl, and a
> shell.** Use them however you need to — render the page at different
> zoom levels, crop to regions, rotate, adjust contrast, compare crops
> side by side, re-render at higher resolution if a crop is still
> illegible. Don't settle for a single full-page render if you can't
> read something — keep trying different views of the same region until
> you're confident, the same way a person would hold a page closer to
> the light or tilt it.
>
> **If `v1` has a layout that matches this page** (same header fields,
> same table columns/row count): reproduce that layout in `v2` so the
> review UI can align `v2` cards with `v1` bboxes. Fill in cells `v1`
> left blank or got wrong, including entire tables Textract dropped
> (e.g. a ground-cover grid that didn't get OCR'd as a table at all).
>
> **If `v1` doesn't match this page** (wrong structure, or no usable
> `v1` at all): propose your own sheet structure that best represents
> what's on the page — a table, a list, whatever fits. Mark the sheet
> (e.g. a cell note or a `_meta` flag) as `needs_layout_review` so the
> reviewer knows there's no `v1` to cross-check against.
>
> **Respect notation conventions**, and don't confuse them:
> - a **dot/period** in a cell means the recorded value is literally `0`
> - a **continuous line drawn through a cell** means "no entry" — leave
>   the cell blank, don't transcribe it as a value
> - **tally marks** (`I`, `l`, `1`, `|` repeated) are a count — sum them
>   to an integer (separate from the dot/line rules above)
>
> **Flag uncertainty.** For any cell where you're not confident in the
> reading even after trying multiple views, apply a yellow fill
> (matching the existing confidence legend convention) so a human
> reviewer's eye goes there first. It's fine to be uncertain — it's not
> fine to guess silently.
>
> **Output**: write the `v2` sheet into the xlsx using openpyxl,
> preserving the `v1` sheet unchanged.

This will get refined once Phase 2 testing runs it against forms beyond
`TreePlots20mx20m.pdf` (e.g. the dot/line convention in
`LeafLitterBiomass.pdf`, flagged in `memory/project_shankar_phase1.md`
as untested on the Textract side too).

---

## Bootstrapping — API keys

**What to get**: an `ANTHROPIC_API_KEY` from the
[Anthropic Console](https://console.anthropic.com) → Settings → API
Keys. This is a Console (pay-as-you-go) key, **not** a `claude login`
/ Claude.ai subscription session — the latter is for interactive
personal use and isn't appropriate for a backend service.

Recommended: create a separate **Workspace** in the Console for this
component (e.g. "form-idable-agent") and generate the key inside it.
Workspaces support their own spend limits — mirrors the Lambda
budget-alert pattern already used for the POC servers (`BUDGET_LIMIT_USD`
in `deploy/config.sh`), giving an independent cost ceiling for the
vision agent specifically.

**How to store it**:

- **Local dev**: `.env` file in `good-shepherd/agents/formidable/`
  (already covered by the repo's `.env` gitignore pattern — same as
  `deploy/test-credentials.env`). Load via `python-dotenv` or
  docker-compose `env_file:`.
- **Deployed (Lambda)**: set as a Lambda environment variable
  (`ANTHROPIC_API_KEY=...`), encrypted at rest by AWS KMS by default —
  same mechanism as any other Lambda config. Set it via
  `aws lambda update-function-configuration --environment Variables={...}`
  in the deploy script, reading the value from the local `.env`
  (never baked into an image layer/`COPY`'d file).

---

## Failure handling & retry

The async pipeline (S3 → Step Functions → DynamoDB job record, from the
recap above) needs a `status` field on the job record:
`pending | processing | done | failed`, plus an `error` field when
`failed`.

- **Step Functions catch blocks** around each pass (TextractPass,
  AgentPass, Merge) write `status=failed` and a human-readable `error`
  string to the job's DynamoDB item — including which stage failed
  (`"agent pass failed on page 3: <message>"`), so the message is
  specific enough to act on.
- **PWA**: the job dashboard polls/reads job status. A `failed` job
  shows the error message and a **"Retry"** button instead of (or next
  to) the normal "Review" action.
- **Retry** = re-invoke the pipeline for that job. The input PDF is
  already in S3 from the original upload, so retry doesn't need a
  re-upload — it's a POST to a `rerun` endpoint that flips the job back
  to `pending`/`processing` and starts a new Step Functions execution
  against the same S3 input. Pages that already completed successfully
  (e.g. agent pass for pages 1–2 of 3) could in principle be skipped on
  retry, but for Phase 2/initial rollout, simplest is to just rerun the
  whole job — optimize later if retries are common and expensive.
- No special handling for *why* it failed (timeout vs transient AWS
  error vs bad input) — same retry button either way. If a job fails
  repeatedly for the same input, that's a signal for a human to look at
  it (the error message + page should make this diagnosable), not
  something the pipeline needs to detect itself.

This is part of the async-pipeline design, not Phase 1/2 — Phase 2 is
local/manual invocation (see below), so there's no job record yet. This
section documents the model so it's not re-derived when the pipeline
gets built.

## Input size limits (Lambda 15-minute timeout)

The agent pass runs inside a single Lambda invocation, capped at 15
minutes. Rather than building chunking/splitting logic into this API
now, **constrain it at the frontend**: cap PDF uploads at a nominal size
(e.g. 5MB) and ask the user to split larger PDFs into multiple
smaller-page-count files before upload if they exceed it. This is a
client-side check (file size before POST), no backend change — the
agent API continues to work exactly as described (one PDF in, v1+v2
xlsx out) and just never sees inputs large enough to risk the timeout.
If 15 minutes turns out to be tight even for 5MB/few-page PDFs once
Phase 2 testing has real timings, revisit the limit number, not the
architecture.

---

## Phasing

### Phase 1 — Vision agent server + methodology

1. Build the vision agent container: base image in
   `good-shepherd/agents/` (Agent SDK + curated toolkit from above),
   component overlay in `good-shepherd/agents/formidable/` (system
   prompt above, FastAPI wrapper exposing it as an endpoint, requirements
   overlay).
2. Document the methodology for setting up agent servers like this one:
   add a new **"Agent servers"** section to
   `heartwood/docs/how-to/onboard-new-component.md`, parallel in style
   to the existing "API servers" section (added without modifying that
   section) — covers the base-image/component-overlay split, package
   curation principle, auth/key storage, and gateway reuse.
3. Smoke test: vision agent given a single page image + v1 xlsx,
   produces a v2 sheet. No PWA integration yet.

### Phase 2 — End-to-end testing (tier 1/2 forms)

- Run the full v1+v2 flow against `TreePlots20mx20m.pdf` (already used
  as the baseline — compare v2 output against the manually-produced
  `temp/TreePlots20mx20m_agent.xlsx`) and a handful of other tier 1/2
  PDFs from `docs/design/shankar_poc_scope.md`.
- Tier 1/2 only for now — tier 3 (`LEMoNPlotAnnualCensusSample`,
  `SaplingSurvivalMonitoring`, `GridVegetation100mx100m`) and the
  excluded forms stay out of scope; revisit once tier 1/2 quality is
  known.
- Use this pass to validate the "ecology form detector" prompt above
  against real notation edge cases (dots/lines in
  `LeafLitterBiomass.pdf`, etc.) and to find any packages the curated
  toolkit is missing.
- **This is where the current design ends** — no orchestration
  (Step Functions/DynamoDB) build-out is in scope for Phase 2; it's
  manual/local invocation against test PDFs to validate output quality.

### Final stage — UI (deferred)

Review-UI work (v1/v2 card+bbox merge, "Save corrections" for v2
proposals, etc.) is **not started** until Phase 2 shows the raw
agent-vision output is high-quality enough across tier 1/2 forms to be
worth building a review flow around. Gated on Phase 2 results.
