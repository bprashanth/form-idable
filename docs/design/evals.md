# Form QA & Eval Analysis — Design

Post-extraction quality layer. After the Fargate worker produces an xlsx,
these features help a human reviewer decide whether the transcription is
trustworthy before downloading it.

**Status:** planned — not yet built.

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

| Variable | Where | Notes |
|---|---|---|
| `GEMINI_API_KEY` | Lambda env / Secrets Manager | Gemini API key |
| `GEMINI_MODEL` | Lambda env | e.g. `gemini-2.5-flash` |

The Lambda already has access to S3 (to read xlsx + manifest) via its task role.
