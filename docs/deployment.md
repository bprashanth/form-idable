# Deployment

Formidable has two independently releasable products:

- the PWA in this repository, deployed by Netlify;
- the Lambda and Low/High Fargate workers in Good Shepherd.

The authoritative backend runbook is
`../good-shepherd/agents/formidable/docs/deployment.md`. Do not duplicate or
invent backend release commands here.

## PWA

Netlify deploys `pwa/` automatically when this repository's `main` branch is
updated. Before pushing a frontend change:

```bash
cd pwa
npm install
npm run build
npx playwright test
```

The production build uses the public `VITE_API_BASE_URL`. No AWS container
rebuild is needed for a PWA-only change.

For a review, Analytics, page-layout or overlay change, also run the saved
all-form visual suite and inspect its screenshots. See `docs/design/evals.md`.

## Backend quick reference

Run from a clean Good Shepherd `main` checkout:

```bash
cd ../good-shepherd/agents/formidable/deploy

./deploy.sh credentials  # rotate Codex auth; rebuild nothing; test Low + High
./deploy.sh low          # shared Lambda + Low; assert High unchanged; test both
./deploy.sh high         # shared Lambda + High; assert Low unchanged; test both
./deploy.sh all          # shared Lambda + both workers; test both
```

Credentials are not baked into containers and code releases do not rotate
them. The backend is self-contained in Good Shepherd; Docker no longer reads
pipeline code from this PWA/benchmark repository.

The detailed runbook explains prerequisites, automatic rollback, exact effects
of each mode and cross-repository release order:
`../good-shepherd/agents/formidable/docs/deployment.md`.

## First-time AWS setup

Only for an unprovisioned environment:

```bash
cd ../good-shepherd/agents/formidable/deploy
./setup.sh
./setup_high.sh
```

All resource identifiers and pinned CLI versions come from `deploy/config.sh`.
Do not hardcode them in another script.

## Changes spanning backend and PWA

Keep the API contract backward compatible and release in this order:

1. pass local backend, model/artifact and saved-browser gates;
2. merge and deploy Good Shepherd first;
3. confirm real Low and High jobs pass;
4. merge Formidable `main` so Netlify deploys the PWA;
5. run the production browser sweep and inspect screenshots;
6. record both commits, job IDs and live image/task identifiers in chronology.

This order lets the previous PWA continue working while the backend changes.

## Accepted production control

The 2026-08-11 accepted High release is:

- High `formidable-high-worker:7`, digest `sha256:231f223f...`;
- frozen Low `formidable-worker:15`, digest `sha256:aacbe354...`.

The complete identifiers, failed first release and recovery are in
`chronology/015_production_selector_and_workbook_provenance_gate.md`. Always
query AWS again before a new release rather than assuming these remain current.

## Operations and maintenance

Use `docs/ops.md` for logs, failed jobs, the nightly regression, S3 artifacts
and diagnosis. Add lifecycle policies for all three ECR repositories
(`form-idable-vision`, `formidable-worker`, `formidable-high-worker`) and both
worker log groups. Do not expire S3 job data until the project has an agreed
retention policy; historical jobs are currently useful evaluation evidence.
