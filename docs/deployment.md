# Deployment

This document covers building and deploying the system, and periodic maintenance tasks. The backend source lives in the sibling repo `good-shepherd/agents/formidable/`. The PWA lives in `pwa/` in this repo.

---

## Prerequisites

You need the AWS CLI configured with credentials that can push to ECR, update Lambda, and register ECS task definitions. Docker must be running. Node 18+ is required to build the PWA locally if needed.

```
aws sts get-caller-identity   # confirm you are logged in as the right account
docker info                   # confirm Docker is running
```

---

## PWA (Netlify)

Netlify deploys automatically on every push to the `main` branch of this repo. No manual steps are needed for routine changes. The build command (`npm run build` from `pwa/`) and publish directory (`pwa/dist`) are set in `netlify.toml` at the repo root.

For a first-time Netlify setup, connect the repo through the Netlify dashboard and add one environment variable:

```
VITE_API_BASE_URL = https://hachry61xe.execute-api.ap-south-1.amazonaws.com/prod
```

All other configuration is checked in.

---

## Backend (Lambda + Fargate)

All backend deploy steps run from the `good-shepherd/agents/formidable/deploy/` directory.

**First-time only:** run `setup.sh` to create the S3 bucket, ECR repos, IAM roles, DynamoDB table, and API Gateway routes. This is idempotent and safe to run again if something was missed.

```
cd good-shepherd/agents/formidable/deploy
./setup.sh
```

**Every release:** run `push.sh`. It builds both Docker images, pushes them to ECR, registers a new Fargate task definition revision pointing to the just-pushed worker image, and updates the Lambda function code.

```
cd good-shepherd/agents/formidable/deploy
./push.sh
```

The script sources `config.sh` for all resource names and IDs. If you need to change anything (memory, timeout, email sender, PWA URL), edit `config.sh` and re-run `push.sh`.

To push only the codex credentials to Secrets Manager without a full redeploy:

```
cd good-shepherd/agents/formidable/deploy
./push_secrets.sh
```

### Additive High release (does not rebuild low)

Use the high-only scripts when changing per-job effort routing, dual readers,
ecology, or Analytics. `push_high.sh` builds/pushes the API handler and the new
high image, and registers only `formidable-high-worker`. It never builds,
pushes, or registers `formidable-worker`.

```
cd good-shepherd/agents/formidable/deploy
./setup_high.sh       # idempotent: high ECR/role/secret/log/routes only
./push_high.sh
```

The deployment host is ARM64 but the existing Lambda is x86_64. The script
preflights amd64 emulation, cross-builds the handler for `linux/amd64`, builds
the high worker for `linux/arm64`, and registers that runtime platform
explicitly. If the preflight fails, install binfmt as instructed by the script
and rerun. Roll back only the additive surfaces with:

```
./rollback_high.sh
```

The provider config is read from
`~/.config/formidable/openrouter.json` (override with
`FORMIDABLE_OPENROUTER_CONFIG`) and stored in Secrets Manager. Never use the
ordinary `push.sh` for a high-only release because it intentionally rebuilds
the low worker too.

---

## Verifying a deploy

After `push.sh` completes, confirm the Lambda is live:

```
curl https://hachry61xe.execute-api.ap-south-1.amazonaws.com/prod/vision/health
```

Expected response: `{"status":"ok"}`.

To tail Lambda logs in real time:

```
aws logs tail /aws/lambda/form-idable-vision --since 5m --follow --region ap-south-1
```

To tail Fargate worker logs for a specific task:

```
aws logs tail /ecs/formidable-worker --since 30m --follow --region ap-south-1
```

---

## Adding a new user

See `docs/onboarding.md`. In short: create a Cognito account, then verify their email in SES if the SES account is still in sandbox mode.

---

## Periodic maintenance

### ECR image cleanup

`push.sh` always pushes to the `:latest` tag. Old image layers accumulate and incur storage costs (~re 2 per GB per month). Set an ECR lifecycle policy to keep only the last 5 images:

```
aws ecr put-lifecycle-policy \
  --repository-name form-idable-vision \
  --lifecycle-policy-text '{"rules":[{"rulePriority":1,"selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":5},"action":{"type":"expire"}}]}' \
  --region ap-south-1

aws ecr put-lifecycle-policy \
  --repository-name formidable-worker \
  --lifecycle-policy-text '{"rules":[{"rulePriority":1,"selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":5},"action":{"type":"expire"}}]}' \
  --region ap-south-1
```

Run this once after the first deploy. It persists and applies automatically going forward.

### CloudWatch log retention

Lambda and Fargate write logs indefinitely by default. Set a retention period to avoid unbounded storage costs:

```
aws logs put-retention-policy \
  --log-group-name /aws/lambda/form-idable-vision \
  --retention-in-days 30 \
  --region ap-south-1

aws logs put-retention-policy \
  --log-group-name /ecs/formidable-worker \
  --retention-in-days 30 \
  --region ap-south-1
```

### S3 job data

Each processed form leaves files in `formidable/jobs/{job_id}/` (PDF, page images, crop images, manifest, xlsx). These accumulate indefinitely. Add a lifecycle rule to delete job data after 180 days if long-term storage is not needed:

```
aws s3api put-bucket-lifecycle-configuration \
  --bucket formidable-storage \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "expire-old-jobs",
      "Filter": {"Prefix": "formidable/jobs/"},
      "Status": "Enabled",
      "Expiration": {"Days": 180}
    }]
  }'
```

Adjust the day count to match your retention requirements. If reviewers need to re-open old jobs, keep it longer or omit the rule entirely.

### DynamoDB

The `formidable-jobs` table grows with every uploaded form. On-demand pricing means there is no cost for unused capacity, but storage costs ~re 21 per GB per month above the free tier. For now the table is small enough that no cleanup is needed. If you want to archive old records, add a TTL attribute to the table and set it on each item at write time.
