# Form QA & Eval Analysis — Design

Post-extraction quality layer. After the Fargate worker produces an xlsx,
these features help a human reviewer decide whether the transcription is
trustworthy before downloading it.

**Status:** the additive subscription High layer passed its local production
gate on 14 PDFs / 68 pages with zero artifact errors. Micro semantic F1 improves
0.887 to 0.910 and precision 0.854 to 0.917 while recall falls 0.924 to 0.904.
The exact routes, five historical-score regressions, paired no-regression
control and review burden are in `benchmarks/HIGH_ADDITIVE_V1.md`.

Current High uses a canonical page/cell IR, a coverage-gated Low-compatible
primary, Luna structure plus Terra/Luna literal readings, generic numeric/domain
checks, taxonomy context, and deterministic histogram/categorical manifests.
Raw accuracy metrics remain, plus semantic metrics that treat only visually
equivalent checked marks (`✓`, `✔`, `☑`, `X`) as the same code. Ecology audit
sheets are excluded from extraction accuracy and validated separately.

## Implemented release architecture

1. Run the frozen Low-compatible agent in the isolated High container.
2. Map every page with bounded Luna structured output.
3. Read each declared cell independently with Terra and Luna.
4. If primary nonblank mapping coverage is at least 80%, deliver it unchanged
   and mark only peer-consensus differences red.
5. Otherwise use Terra; switch to Luna only for at least 10% more nonblank
   evidence, and mark every peer difference red.
6. Run ecology after transcription. Suggestions are orange and never edits.
7. Build Analytics from delivered values, then independently check exact
   canonical/workbook/review coordinates.

The 14-form gate used 204 structured calls, 3.79M reported subscription tokens
and 14,468.5 seconds of summed provider latency (212.8 seconds/page), plus the
agentic primary and Fargate overhead. The CLI reports no marginal API price;
this must be described as subscription-unmetered, not free. A Sol tie-breaker
was rejected because it scored below Terra on its targeted fixture.

## Historical speculative design (not the current implementation)

---

## 1  LLM anomaly report

Send the stored xlsx (already in S3) as CSV text to a cheap LLM. Ask it to
identify anomalies using its own domain knowledge — no human needs to
specify what kind of form it is.

### Prompt approach

One pass. The LLM infers form type from available context signals:

```
You are a scientific data reviewer. A scanned field form was processed by
OCR into the spreadsheet below.

Filename: {filename}
Form notes from extraction:
  {crop_notes joined from crops_manifest.json, e.g.
   "page 1 header, date, treatment, observers"
   "page 1 table A, blocks 1-5"}
Column headers: {row 7 of xlsx, the first non-metadata row}

Data (CSV):
{full xlsxRows as CSV, all pages}

Tasks:
1. In one sentence, identify what this data records.
2. List up to 8 anomalies: values that are biologically implausible,
   internally inconsistent, or statistically unusual. For each, give
   row/col, the value, and why it's suspicious.
3. Note any systematic patterns suggesting transcription error
   (e.g. a whole block is zero, one species appears only once,
   a treatment label is inconsistent with the others).
```

### Model choice

- **Gemini 2.5 Flash** (recommended): ~$0.15/1M input, ~$0.60/1M output.
  A 150-row × 15-col xlsx ≈ 8–12K tokens → ≈$0.001 per analysis run.
- **Gemini 2.0 Flash**: half the price, slightly less capable reasoning.
- **Google AI Studio free tier**: 15 req/min, 1M tokens/day — sufficient
  for development and light production use.
- **Avoid**: OpenRouter free models (inconsistent quality/availability).

### Backend

New route on the Lambda HTTP handler:

```
POST /vision/jobs/{job_id}/analyze
Authorization: Bearer {cognito_token}
Body: { "query": null }          // null = standard anomaly report
      { "query": "plot ..." }    // string = distribution query (see §2)
```

Handler:
1. Fetch `crops_manifest.json` and xlsx from S3 (both already stored)
2. Convert xlsxRows to CSV string
3. Build prompt with filename + crop notes + headers + CSV
4. Call Gemini via `google-generativeai` Python SDK (API key in env/secret)
5. Return `{ "type": "anomaly_report", "findings": "...", "form_type": "..." }`

### Frontend

"QA Report" button in the review page header (next to "Submit Review").
On click: POST to `/analyze`, show a collapsible panel below the toolbar
with the bullet-point findings. Highlight referenced rows in the Excel
panel (if the model returns structured row/col refs — request JSON output
format for easier parsing).

---

## 2  Distribution plots (natural language queries)

Same endpoint, non-null `query`. User types: "show me treatment vs species count"
or "plot DBH by site". Backend sends query + CSV to Gemini and asks for a
**Vega-Lite spec** (JSON). Frontend renders it natively using `vega-embed`
(no image encoding needed, no matplotlib dependency).

```
// extended prompt when query is set:
The user asks: "{query}"
Produce a valid Vega-Lite v5 JSON spec that answers this question using
the data above. Inline the data in the spec (values array). Return only
valid JSON, no markdown fences.
```

### Frontend

Small chat input below the Excel panel ("Ask about this data…"). Submits
query, renders the returned Vega-Lite spec via `vega-embed`. Package:
`vega`, `vega-lite`, `vega-embed` (~450KB gzipped total).

---

## 3  Second-model diff (future)

Run Gemini Flash alongside codex in the Fargate worker. Both emit a
normalised flat JSON array: `[{row, col_name, value}, ...]`. Diff at cell
key level. Store disagreeing cells in DynamoDB alongside the job record.
Review page shows a fourth highlight colour ("models disagree") alongside
yellow (low confidence), amber (human correction).

Key constraint: both models must use an identical strict JSON schema in
their system prompt to make the diff viable. Format mismatch is the main
failure mode.

**Not yet scoped** — depends on §1 first.

---

## Build order

1. Backend route + Gemini SDK integration (one Python file change on the Lambda)
2. Frontend "QA Report" button + collapsible panel
3. Vega-embed package + query input
4. Second-model diff (future sprint)

---

## Environment variables needed

```
GEMINI_API_KEY   Lambda env or Secrets Manager   Gemini API key
GEMINI_MODEL     Lambda env                      e.g. gemini-2.5-flash
```

The Lambda already has access to S3 (to read xlsx + manifest) via its task role.

---

## Testing dev changes

The review page has an end-to-end Playwright suite in `pwa/tests/`. It covers upload, job polling, and the review UI including crop overlays. To run it against a real job:

```
cd pwa
npx playwright test
```

By default the tests run against the production API (set via `API_TARGET` in `pwa/.env.local`). To run against the local mock instead, set `API_TARGET=http://localhost:8072` and start the mock server first.

When the `/vision/jobs/{job_id}/analyze` endpoint is built, add a test in `pwa/tests/review-flow.spec.js` that clicks the "QA Report" button and asserts that the result panel appears with at least one finding. The test should use a known seed job (e.g. `bd6a19ac-b14d-4a67-8cfa-50df8bd78121`) so the fixture data is stable and the Gemini call can be stubbed with `page.route()` to avoid live API costs in CI.

For agents iterating on the prompt or the anomaly logic without touching the UI, the backend can be tested directly:

```
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <client_id> \
  --auth-parameters USERNAME=<user>,PASSWORD=<pass> \
  --region ap-south-1 \
  --query 'AuthenticationResult.IdToken' --output text)

curl -s -X POST \
  https://hachry61xe.execute-api.ap-south-1.amazonaws.com/prod/vision/jobs/bd6a19ac-b14d-4a67-8cfa-50df8bd78121/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": null}' | jq .
```

Use the credentials in `good-shepherd/server/deploy/test-credentials.env` for the Cognito call. Pass `{"query": "plot treatment vs species count"}` in the body to test the distribution plot path instead.
