# Operations

Day-2 operations for the Formidable backend: the nightly regression suite,
debugging failed jobs, deploying, and rolling back. First-time setup and the
normal deploy flow are in [deployment.md](deployment.md); this doc covers what
you do *after* it's live and something needs checking, fixing, or reverting.

The backend code lives in the sibling repo `../good-shepherd/agents/formidable/`.
All paths below are relative to that directory unless noted.

---

## Nightly regression suite

A cron runs codex against a frozen "golden" form every night and emails a
pass/fail diff report. Its job is to catch **regressions** — codex crashing,
emptying out, or dropping whole tables after a model/CLI/prompt change — not to
certify transcription accuracy (a human spot-checks the attached xlsx for that).

### How it works

```
EventBridge Scheduler (formidable-nightly-regression, 20:00 UTC ≈ 01:30 IST)
  → ecs:runTask on the formidable-worker task def, with MODE=regression override
    → worker.py run_regression():
        1. download source.pdf + golden.xlsx from S3 (the frozen fixture)
        2. run codex exec on the PDF (same path as a real job)
        3. tolerant diff of the produced output.xlsx vs golden  (xlsx_diff.py)
        4. email a PASS/FAIL report with output.xlsx + page renders attached
        5. archive all artifacts to s3://formidable-storage/formidable/regression/runs/<ts>/
```

The schedule uses EventBridge Scheduler's **universal `ecs:runTask` target** (not
the templated ECS target) because only the universal target can pass the
`MODE=regression` container override. It references the task-def **family**
(`formidable-worker`), so it always runs the latest revision — no need to
re-point it after a `push.sh`.

### The tolerant diff (`xlsx_diff.py`)

The golden is a human-corrected transcription; any codex run is a *second*
reading of the same handwriting, and the two don't even share a sheet layout
(golden uses per-page sheets; codex emits one `v2` sheet). So the diff is
**structure-agnostic**: flatten every cell across all sheets → split into atomic
tokens → bucket into numbers vs words → measure recall against the golden as a
multiset.

- **Numbers are the reliable signal** (`num_recall`, primary gate) — a "17" is a
  "17" regardless of penmanship.
- **Words run perpetually low** (`word_recall`, lenient gate) — handwritten
  species/site names get read three different ways; this is expected, not a bug.
- **`cell_frac`** (candidate cell count / golden cell count) is a liveness gate —
  catches "codex broke → tiny/empty output".
- The "missing numbers/words" lists in the report are `Counter(golden) -
  Counter(candidate)` — a **spot-check triage aid**, not a defect list. A word
  shows as "missing" mostly because the run read the same scrawl as a different
  string.

Thresholds (all env-overridable, defaults calibrated so a healthy run — observed
0.82 / 0.72 / 0.48 — passes with margin but a broken run fails):

| Env var                      | Default | Gate                        |
| ---------------------------- | ------- | --------------------------- |
| `REGRESSION_MIN_CELL_FRAC`   | 0.50    | liveness                    |
| `REGRESSION_MIN_NUM_RECALL`  | 0.55    | primary content gate        |
| `REGRESSION_MIN_WORD_RECALL` | 0.30    | lenient content gate        |

### Operating it

```bash
cd ../good-shepherd/agents/formidable/regression

./toggle.sh status      # ENABLED / DISABLED
./toggle.sh off         # kill switch — pauses the nightly (schedule stays in place)
./toggle.sh on          # resume
./run_once.sh           # fire a run right now + tail logs (costs ~$0.02 Fargate + 1 codex form)
./schedule.sh           # (re)create the schedule — idempotent; run after changing cron/recipient
./upload_golden.sh      # (re)upload the fixture — run after updating the golden standard
```

- **Recipient:** `REGRESSION_EMAIL` (default `prashanth@tech4goodcommunity.com`).
  Must be an SES-verified identity — SES is in **sandbox** (see onboarding.md).
- **Cron:** `SCHEDULE_EXPR` (default `cron(0 20 * * ? *)` UTC). Pass a different
  expression and re-run `schedule.sh` to change it.
- **Fixture:** `benchmarks/TreePlots20mx20m.pdf` + `TreePlots20mx20m_merged.xlsx`
  in *this* repo → uploaded to `s3://formidable-storage/formidable/regression/`
  as `source.pdf` + `golden.xlsx`. To change the standard, replace those and
  re-run `upload_golden.sh`.

### Updating the golden standard

The golden should be a transcription you trust. To change it: edit/replace the
xlsx (and PDF if the form changes) in `benchmarks/`, run `upload_golden.sh`, then
`run_once.sh` to confirm a healthy run still passes against the new golden. If
thresholds need retuning, set the `REGRESSION_MIN_*` env vars on the schedule
(via `schedule.sh` after adding them to the container override) — or adjust the
defaults in `xlsx_diff.py`.

### Did the nightly actually run?

```bash
# Artifacts from every run (newest last):
aws s3 ls s3://formidable-storage/formidable/regression/runs/ --region ap-south-1

# EventBridge invocation errors (if a night produced no run at all):
aws cloudwatch get-metric-statistics --namespace AWS/Scheduler \
  --metric-name TargetErrorCount --dimensions Name=ScheduleName,Value=formidable-nightly-regression \
  --start-time <T-1d> --end-time <now> --period 86400 --statistics Sum --region ap-south-1
```

Each run's `run.log` (uploaded to `runs/<ts>/run.log`) records the codex result
and the email send outcome — the send is non-blocking, so this log is the
server-side confirmation the email went out.

### Cost

EventBridge Scheduler is effectively free (nightly ≈ 30 invocations/mo vs a 14M
free tier). The only cost is the Fargate task it launches (~$0.02/run, ~$0.60/mo)
plus one codex form (drawn from the ChatGPT subscription via `~/.codex/auth.json`,
so likely ~$0 marginal). See scaling.md for the broader cost model.

---

## Debugging a failed job or extraction

Whether it's a real user job or a regression run, the artifacts and logs live in
the same places.

```bash
# Job status + error (real jobs):
aws dynamodb get-item --table-name formidable-jobs \
  --key '{"user_id":{"S":"<user>"},"job_id":{"S":"<id>"}}' --region ap-south-1

# Per-run log (the detailed codex trace — file-based, uploaded to S3):
aws s3 cp s3://formidable-storage/formidable/jobs/<job_id>/run.log - --region ap-south-1
#   (regression runs: .../regression/runs/<ts>/run.log)

# Fargate stdout (sparse — worker logs to the file above, not stdout):
aws logs tail /ecs/formidable-worker --since 1h --region ap-south-1
```

Common failure modes:

- **codex auth stale/expired** — `run.log` shows "could not fetch codex auth" or
  a codex auth error. `~/.codex/auth.json` holds rotating OAuth tokens; re-run
  `deploy/push_secrets.sh` (or a full `push.sh`) to refresh the Secrets Manager
  copy from your current local login.
- **Job stuck in `queued`** — ECS couldn't launch the task (task limit, subnet).
  No automatic retry today (see scaling.md).
- **Synchronous 30s timeout** — API Gateway HTTP APIs cap integrations at ~30s.
  The upload path is async (returns a job_id immediately) precisely to avoid
  this; if you see a 503 at ~30s you're on a synchronous path that shouldn't be.

---

## Deploying

The full deploy is **self-verifying and self-reverting**:

```bash
./deploy.sh
#  build.sh --test           local container health check (free)
#  push.sh                   retag current images :latest→:rollback, then build+push
#                            new :latest (codex pinned), refresh secret, update Lambda,
#                            register a new worker task-def revision
#  verify_prod.sh            mint JWT → real /vision/extract → presigned upload →
#                            /start → poll → download xlsx → tolerant-diff vs golden
#     PASS → done
#     FAIL → rollback.sh → verify_prod.sh
#              PASS → prod restored to previous image, exit 1 (this deploy failed)
#              FAIL → rollback.sh --with-secret → verify_prod.sh → exit 1 or 2
```

Each `verify_prod.sh` runs one real codex job (~$0.02 + one form), so a rollback
path can run codex 2–3 times. Deploys are infrequent; this is the price of a safe
gate. `config.sh` holds every resource name/ID and is sourced by all scripts. See
deployment.md for first-time `setup.sh`.

`verify_prod.sh` needs Cognito test creds: `deploy/test-credentials.env`
(`TEST_USERNAME`/`TEST_PASSWORD`), falling back to the server repo's copy at
`good-shepherd/server/deploy/test-credentials.env`.

### Rolling back

`deploy.sh` rolls back automatically on a failed verify. To do it by hand:

```bash
./rollback.sh                # restore :rollback→:latest, redeploy Lambda + worker task-def
./rollback.sh --with-secret  # ALSO revert the codex secret to its prior version
./verify_prod.sh             # confirm prod is healthy again
```

How it works:

- **Images:** `push.sh` retags the current `:latest`→`:rollback` in both ECR
  repos *before* overwriting `:latest` (via `_retag.sh`), so the prior image is
  always preserved (not left untagged to be GC'd). `rollback.sh` restores it.
- **Lambda:** redeployed from the restored `:latest` (Lambda caches the digest, so
  it must be re-pointed).
- **Worker:** task defs reference the `:latest` tag, so moving the tag back is
  enough; `rollback.sh` also re-registers a revision so the family head is clear.
- **Secret:** `--with-secret` swaps the Secrets Manager `AWSPREVIOUS` label back to
  `AWSCURRENT`. **Ordering:** image/task-def first; revert the secret only if an
  image rollback alone doesn't fix prod — the previous OAuth token is *older* and
  may be closer to expiry, so reverting it can make an auth problem worse.

---

## Secrets & codex

- **codex auth:** `deploy/push_secrets.sh` copies `~/.codex/auth.json` →
  Secrets Manager `formidable/codex-auth`. The worker writes it back to
  `$HOME/.codex/auth.json` at startup. It's a manual snapshot of rotating OAuth
  tokens — `push.sh` refreshes it every deploy, but it's only as fresh as your
  local login at push time.
- **codex version:** **pinned** via `CODEX_VERSION` in `config.sh` (default
  `0.142.5`), passed as a `--build-arg` into both Dockerfiles — the image's codex
  matches your validated local `codex --version`. To upgrade: bump `CODEX_VERSION`
  and run a full `./deploy.sh` so `verify_prod.sh` confirms the new version works
  before it sticks (and auto-reverts if it doesn't).
- **SES:** sandbox mode (recipients must be verified). `ses:SendEmail` +
  `ses:SendRawEmail` (raw = MIME/attachments) are on the worker task role in
  `deploy/fargate-task-policy.json`.
