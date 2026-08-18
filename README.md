# form-idable

Formidable digitises handwritten ecological survey forms. A field worker uploads a scanned PDF through the web app. An AI worker extracts the data into a structured Excel workbook with bounding-box annotations, and a reviewer can inspect the output side-by-side with the original form before downloading.

The backend runs entirely on AWS (ap-south-1). The PWA is hosted on Netlify.

---

## >>> HOW TO DEPLOY <<<

The PWA deploys through Netlify when this repository's `main` branch changes.
The self-contained backend lives in `../good-shepherd/agents/formidable/`.
Choose an explicit backend release mode:

```
cd ../good-shepherd/agents/formidable/deploy
./deploy.sh credentials  # Codex auth only; rebuild nothing; verify Low + High
./deploy.sh low          # Lambda + Low; assert High unchanged; verify both
./deploy.sh high         # Lambda + High; assert Low unchanged; verify both
./deploy.sh all          # Lambda + both workers; verify both
```

Credentials and code are intentionally separate release surfaces. Both workers
read the same Secrets Manager auth at task startup; rotating it does not rebuild
an image. The production High pipeline is owned by Good Shepherd, so backend
deploys do not require this PWA/benchmark checkout.

Notes:

- You need a good network connection. The two image pushes are large and have
  stalled mid-push on flaky connections before.
- A successful code or credential gate runs one real Low and one real High job;
  rollback paths run them again.
- This deploys the BACKEND only. The frontend (this repo's `pwa/`) deploys
  separately via Netlify on a push to `main`.

Authoritative backend commands:
`../good-shepherd/agents/formidable/docs/deployment.md`. Product-level release
order: `docs/deployment.md`. Operations: `docs/ops.md`.

---

## Replicating this on another machine

Never use a blanket `git add .`: model outputs and cross-project scratch files
may be present. Credentials, venvs and generated benchmark runs are gitignored;
stage reviewed source/docs by explicit path. The only tracked env file,
`pwa/.env.production`, contains the public API Gateway URL.

### Option A: fresh clone (you re-provision the secrets)

1. Clone Good Shepherd to deploy the backend. Clone Formidable too when working
   on the PWA or running the full model/visual benchmark suite.
2. `codex login` locally so `~/.codex/auth.json` exists (deploy reads it and
   pushes it to Secrets Manager; it is never in git).
3. Configure AWS credentials locally (`aws sts get-caller-identity` must work).
4. Recreate `good-shepherd/agents/formidable/deploy/test-credentials.env` with
   `TEST_USERNAME` / `TEST_PASSWORD` (a Cognito test user) so `verify_prod.sh`
   can mint a JWT. This file is gitignored on purpose.
5. Recreate the backend `.env` if you run the worker/handler locally.
6. Rebuild deps: `pwa/` -> `npm install`; backend -> `python3 -m venv .venv &&
   . .venv/bin/activate && pip install -r requirements.txt`.

### Option B: rsync from a machine that already works (recommended)

Instead of re-cloning and re-provisioning, copy your working state directly.
From this machine:

```
./transfer-context.sh USER@HOST [REMOTE_PATH]
```

This rsyncs BOTH repos to the remote (default `REMOTE_PATH` is
`~/src/github.com/bprashanth`, same layout as here). It carries the gitignored
`.env` / `test-credentials.env` / `outputs.env` so the remote can deploy and
verify immediately, but it does NOT copy codex credentials (the remote runs its
own `codex login`) and skips `node_modules`/venvs/caches (rebuild those on the
remote). Full agent handover notes are in `CLAUDE.md` under "Taking over on
another machine".

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
docs/chronology.md         How experiments, failures and releases are recorded
docs/onboarding.md        Adding a user (Cognito + SES), Netlify deploy
docs/scaling.md           Concurrency limits, free tier, cost per form
docs/design/evals.md      Model, harness, UX and end-to-end benchmark workflow
```

Historical design notes and experiments are in `docs/archive/`.
