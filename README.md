# form-idable

Formidable digitises handwritten ecological survey forms. A field worker uploads a scanned PDF through the web app. An AI worker extracts the data into a structured Excel workbook with bounding-box annotations, and a reviewer can inspect the output side-by-side with the original form before downloading.

The backend runs entirely on AWS (ap-south-1). The PWA is hosted on Netlify.

---

## Repo layout

```
pwa/              Vue 3 PWA -- the upload, review, and download interface
docs/             Documentation (see index below)
docs/archive/     Superseded documents from earlier pipeline iterations
agent/            Original FastAPI species/serial handler server (Textract era, not in use)
```

The backend source (Lambda handler, Fargate worker, deploy scripts) lives in a sibling repo at `../good-shepherd/agents/formidable/`.

---

## System overview

```
User (browser)
  |
  v
Netlify (PWA, pwa/)
  |  JWT from Cognito
  v
API Gateway (form-idable-api, ap-south-1)
  |
  v
Lambda (form-idable-vision)
  |  stores PDF -> S3
  |  creates job record -> DynamoDB
  |  launches task -> ECS Fargate
  |
  v
Fargate worker (formidable-worker)
  |  runs codex CLI on the PDF
  |  writes page images, crop images, manifest, xlsx -> S3
  |  sends completion email -> SES
  |
  v
S3 (formidable-storage)
  |  presigned URLs returned to PWA
  v
User reviews output in the browser
```

---

## Documentation

```
docs/architecture.md      System components, data flow, API routes, local dev setup
docs/deployment.md        How to build and push, first-time setup, periodic cleanup
docs/onboarding.md        Adding a user (Cognito + SES), Netlify deploy
docs/scaling.md           Concurrency limits, free tier, cost per form
docs/design/evals.md      Planned QA analysis layer (anomaly detection, distribution plots)
```

Historical design notes and experiments are in `docs/archive/`.
