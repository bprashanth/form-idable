# form-idable

A mobile-first tool for digitising ecological survey forms. Field workers photograph paper forms; the app extracts the data into a spreadsheet and applies ecological domain knowledge to correct common OCR errors before the researcher downloads the file.

## Components

```
pwa/           Vue 3 PWA — the mobile interface used in the field
agent/         FastAPI post-processing server — ecological context handlers
good-shepherd  Serverless OCR backend (separate repo, deployed independently)
```

See [pwa/README.md](pwa/README.md) and [agent/README.md](agent/README.md) for component-level quickstart and deployment instructions.

---

## Architecture

### End-to-end flow

```
User (mobile)
  │  captures photo of paper form
  ▼
pwa/ (Vue PWA, hosted on Netlify)
  │  POST /api/upload  →  good-shepherd (AWS Lambda + Textract)
  │                        • runs AWS Textract on the image
  │                        • converts the table into an .xlsx workbook
  │                        • writes a "(Good Shepherd) Row ID" column for row-stable joins
  │                        • returns: xlsx (base64), row bboxes, summary
  │
  │  [user reviews the result screen]
  │
  │  POST /agent/infer-types  →  agent server (AWS Lambda)
  │                               • fuzzy-matches column headers against cheatsheet.json
  │                               • returns type_map: {col → {type, confidence, keyword}}
  │
  │  [user confirms the detected column types]
  │
  │  POST /agent/check-serial →  agent server
  │                               • rewrites serial-number columns 1…N
  │                               • returns corrected .xlsx
  │
  │  POST /agent/check-species → agent server
  │                               • fuzzy-matches each unique species cell value against
  │                                 the species dictionary (abbr / expanded / Toda name)
  │                               • returns proposals: [{original, corrected, score, …}]
  │
  │  [user reviews proposals, edits if needed, confirms]
  │
  │  POST /agent/apply-species → agent server
  │                               • writes accepted corrections back into the .xlsx
  │                               • returns corrected .xlsx
  │
  ▼
  user downloads corrected .xlsx
```

### Network routing

| Request path | Dev (Vite proxy) | Production (Netlify) |
|---|---|---|
| `/api/*` | → `localhost:8070` (good-shepherd) | → absolute URL baked in at build time via `VUE_APP_API_BASE_URL` |
| `/agent/*` | → `localhost:8071` (agent server) | → Lambda Function URL via `netlify.toml` redirect |

See [docs/manuals/deployment.md](docs/manuals/deployment.md) for environment variable details.

---

## The ecological context layer (agent server)

Ecological forms contain columns that Textract handles poorly out of the box:

- **Species names** — hand-written abbreviations or local (Toda) dialect names that Textract guesses phonetically and gets wrong.
- **Serial numbers** — OCR often misreads or skips cells; the true values are deterministic (1, 2, 3 …).

The agent server encodes this domain knowledge in *handlers* — one per column type. Each handler lives in `agent/server/routers/` and is backed by a service in `agent/server/services/`. The column type assigned to a header (via `cheatsheet.json`) determines which handler runs.

### Current handlers

| Type | Endpoints | What it does |
|---|---|---|
| `serial` | `/agent/check-serial` | Replaces OCR values with sequential integers; row count returned in `X-Row-Count` header |
| `species` | `/agent/check-species`, `/agent/apply-species`, `/agent/lookup-species` | Fuzzy-matches cell values against `data/species_name.csv` (abbreviation, expanded Latin name, Toda dialect name) using rapidfuzz; user reviews and accepts/edits proposals before they are written back |

### Column type discovery (cheatsheet)

`agent/server/cheatsheet.json` maps type names to header keywords. `fuzzy.infer_types()` does a substring match (both directions) between each column header and the keyword list — returning `high` confidence on an exact match, `medium` on a substring match.

The cheatsheet is editable at runtime through the PWA sidebar (`/agent/cheatsheet` GET/PUT) without redeploying the server.

### Species dictionary

`agent/server/data/species_name.csv` has three fields per entry: `Species name Abbr`, `Species name expanded`, `Toda name`. The fuzzy matcher searches all three fields so that a field worker writing "kage" (the Toda name) or "Kage" (the abbreviation) both resolve to *Litsea wightiana*. New entries can be added through the PWA sidebar or via `POST /agent/species-db/entry`.

---

## Adding a new ecological context handler

See [docs/manuals/new-handler.md](docs/manuals/new-handler.md).
