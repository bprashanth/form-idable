# form-idable

Formidable digitises handwritten ecological survey forms. A field worker uploads a scanned PDF through the web app. An AI worker extracts the data into a structured Excel workbook with bounding-box annotations, and a reviewer can inspect the output side-by-side with the original form before downloading.

The backend runs entirely on AWS (ap-south-1). The PWA is hosted on Netlify.

---

## >>> HOW TO DEPLOY THE BACKEND <<<

The backend source does NOT live in this repo. It lives in the sibling repo at
`../good-shepherd/agents/formidable/`. To deploy it:

```
cd ../good-shepherd/agents/formidable/deploy
./deploy.sh
```

That single command does everything:

1. Reads your local codex auth (`~/.codex/auth.json`) and pushes it to AWS
   Secrets Manager. Run `codex login` first if your token is stale.
2. Builds both container images (HTTP handler + Fargate worker), pinned to the
   codex version in `deploy/config.sh`.
3. Retags the current images as `:rollback` so a bad deploy can be undone.
4. Pushes the images, updates the Lambda, and registers a new Fargate task
   definition.
5. Runs ONE real codex job against prod and diffs the result against the golden
   fixture. If it fails, it rolls back the image (and, as a last resort, the
   secret) and complains loudly.

Notes:

- You need a good network connection. The two image pushes are large and have
  stalled mid-push on flaky connections before.
- Each run costs roughly one codex job (~$0.02 Fargate + one form). A rollback
  path runs codex two or three times.
- This deploys the BACKEND only. The frontend (this repo's `pwa/`) deploys
  separately via Netlify on a push to `main`.

Full deploy and ops detail: `docs/deployment.md` and `docs/ops.md`.

---

## Replicating this on another machine

The code is safe to `git add . && git push` (credentials are gitignored: `.env`,
venvs, `deploy/test-credentials.env`, `deploy/outputs.env`, `CLAUDE.md`,
`AGENTS.md`; the only tracked env file, `pwa/.env.production`, holds just the
public API Gateway URL). But a fresh clone alone does NOT reproduce the deploy
flow, because a few things are deliberately kept out of git.

### Option A: fresh clone (you re-provision the secrets)

1. Clone BOTH repos as siblings under the same parent:
   `.../bprashanth/form-idable` and `.../bprashanth/good-shepherd`.
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
docs/onboarding.md        Adding a user (Cognito + SES), Netlify deploy
docs/scaling.md           Concurrency limits, free tier, cost per form
docs/design/evals.md      Planned QA analysis layer (anomaly detection, distribution plots)
```

Historical design notes and experiments are in `docs/archive/`.
