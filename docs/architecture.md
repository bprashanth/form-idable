# Architecture

Formidable digitises handwritten ecological survey forms. A field worker uploads a scanned PDF through the web app. A Fargate worker processes the PDF with the codex CLI, producing a structured Excel workbook and a set of crop images that the reviewer can inspect side-by-side. The system is serverless and runs entirely on AWS in ap-south-1.

---

## Components

```
Component          | What it does                                  | Runs on
------------------ | --------------------------------------------- | -----------------------
PWA                | Upload, review, and download interface        | Netlify (static)
API Gateway        | HTTPS entry point, JWT auth                   | AWS HTTP API (hachry61xe)
Lambda handler     | Receives uploads, queries jobs, returns URLs  | AWS Lambda (form-idable-vision)
Fargate worker     | Runs codex on the PDF, writes outputs to S3   | AWS Fargate (formidable-worker)
S3                 | Stores PDFs, page images, crop images, xlsx   | formidable-storage bucket
DynamoDB           | Job metadata and status                       | formidable-jobs table
Cognito            | User accounts and JWT tokens                  | ap-south-1_28HVATwK2
SES                | Job completion notification emails            | AWS SES ap-south-1
```

The Lambda handler and the Fargate worker are built from separate Docker images in the same source tree (good-shepherd/agents/formidable). The Lambda uses the Lambda Web Adapter to wrap a FastAPI application. The Fargate worker uses the awslambdaric runtime so it can be invoked directly without a web server.

---

## Repositories and infra ownership

The system spans two repos, split along a frontend/data vs backend line:

- **`form-idable` (this repo)** — the PWA (`pwa/`), documentation (`docs/`),
  benchmarks and datasets (`benchmarks/`), and the golden regression fixture.
  The old `agent/` FastAPI server here is the retired Textract-era code, not in
  use.
- **`good-shepherd/agents/formidable/`** — the entire live backend: the Lambda
  handler (`main.py`), the Fargate worker (`worker.py`), Dockerfiles, deploy
  scripts, prompts, and the nightly regression suite. The Python is
  self-contained (no imports from `good-shepherd/server/`).

The **AWS infra** belongs to neither repo — it's deployed in `ap-south-1` by the
good-shepherd deploy scripts. Ownership matters when reasoning about changes:

- The **`form-idable-api` API Gateway** and the **`cognito-jwt` authorizer** are
  created by **`good-shepherd/server/deploy/setup.sh`**. The formidable agent
  *reuses* them (hangs its `/vision/*` routes off the shared gateway) and never
  creates them — so all backends sit behind one gateway in good-shepherd.
- The **`form-idable-agents` ECS cluster** (VPC/subnet/SG) is shared config in
  `good-shepherd/agents/deploy/config.sh`; `agents/formidable/deploy/config.sh`
  sources it. `agents/` is structured as a multi-agent host — formidable is the
  first agent.

Practical consequence: working on the formidable **backend** requires the
good-shepherd repo checked out alongside this one. Operational runbook: `ops.md`.

---

## Data flow

A user authenticates against Cognito through the PWA and receives a short-lived JWT. Every API call to the gateway includes that token in the Authorization header. The Cognito JWT authorizer on the gateway validates the token before routing the request to the Lambda.

When a user uploads a PDF, the Lambda writes the file to S3 under `formidable/jobs/{job_id}/input.pdf`, creates a DynamoDB record with status `queued`, and calls `ecs.run_task()` to launch a Fargate task with the job ID and S3 key passed as environment variables. The Lambda returns the job ID immediately without waiting for the worker.

The Fargate worker downloads the PDF, renders each page as a PNG, and runs `codex exec` with a prompt that instructs it to crop regions of interest, assign Excel row ranges to each crop, and produce `output.xlsx`. The worker writes the following to S3:

```
formidable/jobs/{job_id}/
  input.pdf
  page_1.png, page_2.png, ...
  crop_001.png, crop_002.png, ...
  crops_manifest.json
  output.xlsx
  progress.json
```

After writing all outputs the worker updates the DynamoDB record to status `done` and sends a notification email via SES if a recipient address was provided at upload time.

The PWA polls `GET /vision/jobs/{job_id}` until status is `done`, then fetches presigned S3 URLs for the manifest, xlsx, page images, and crop images. All assets are loaded directly from S3 using those presigned URLs -- no binary data passes through the Lambda on the read path.

---

## crops_manifest.json format

The manifest is the contract between the Fargate worker and the review UI. The worker writes it; the UI reads it to know which crop images exist, where they are on the page, and which Excel rows they correspond to.

```json
{
  "pages": [
    {
      "page": 1,
      "render": "page_1.png",
      "crops": [
        {
          "file": "crop_001.png",
          "bbox": [0.13, 0.12, 0.88, 0.23],
          "rows": "1:5",
          "note": "page 1 header, date, treatment, observers"
        },
        {
          "file": "crop_002.png",
          "bbox": [0.08, 0.21, 0.47, 0.84],
          "rows": "10:39",
          "note": "page 1 table A, blocks 1-5"
        }
      ]
    }
  ]
}
```

`bbox` values are fractions of the rendered page image dimensions, in the order x0, y0, x1, y1. `rows` is a range of Excel row numbers (1-indexed) corresponding to the cells extracted from that crop. The UI uses `rows` to scroll and highlight the Excel panel when a user hovers or clicks a crop overlay.

---

## API routes

All routes go through API Gateway and require a Cognito JWT except the health check.

```
Method | Path                          | Auth | What it does
------ | ----------------------------- | ---- | -----------------------------------
GET    | /vision/health                | none | Returns {"status":"ok"}
POST   | /vision/extract               | JWT  | Upload PDF, create job, return job_id
GET    | /vision/jobs                  | JWT  | List all jobs for the authenticated user
GET    | /vision/jobs/{job_id}         | JWT  | Return job status + presigned S3 URLs
```

The POST /vision/extract body is JSON: `{"filename": "...", "name": "...", "notification_email": "..."}`. The PDF is uploaded separately to S3 via a presigned PUT URL that the Lambda returns alongside the job_id. The notification_email field is optional and is stored in DynamoDB; it receives the completion email if provided.

---

## Authentication and Cognito config

The Cognito user pool ID and client ID are not baked into the PWA build. At startup the PWA fetches them from a public S3 object:

```
https://fomomon.s3.ap-south-1.amazonaws.com/auth_config.json
```

This means Cognito pool configuration can change without a PWA redeploy. The file contains `{"userPoolId": "...", "clientId": "..."}`.

---

## Environment variables

The Lambda handler reads these from its function configuration:

```
JOBS_BUCKET          S3 bucket name (formidable-storage)
S3_PREFIX            Key prefix within the bucket (formidable)
DYNAMO_TABLE         DynamoDB table name (formidable-jobs)
ECS_CLUSTER          Fargate cluster ARN
FARGATE_TASK         Task definition name (formidable-worker)
ECS_SG_NAME          Security group name for Fargate tasks
```

The Fargate worker reads these, some injected at task launch time:

```
CODEX_SECRET_NAME       Secrets Manager secret holding codex auth.json
JOBS_BUCKET             Same as above
AWS_REGION              ap-south-1
NOTIFICATION_FROM_EMAIL SES sender address
PWA_URL                 Base URL for links in notification emails
JOB_ID                  Injected per-task at launch
INPUT_KEY               S3 key of the uploaded PDF, injected per-task
FILENAME                Original filename, injected per-task
USER_ID                 Cognito user ID, injected per-task
NOTIFICATION_EMAIL      Recipient email, injected per-task if provided
```

The PWA reads one build-time variable:

```
VITE_API_BASE_URL    Full base URL of the API Gateway stage
```

---

## Local development

To run the PWA against the production API, set `API_TARGET` in `pwa/.env.local` to the API Gateway URL and run `npm run dev` from the `pwa/` directory. The Vite dev server proxies all `/vision/*` requests to that target.

To run against a local mock instead, start `mock_api.py` from the good-shepherd repo on port 8072 and point `API_TARGET` at `http://localhost:8072`. The mock returns static fixture data and does not talk to AWS.

The backend (Lambda + Fargate) cannot be run locally in a meaningful way because it depends on ECS, Secrets Manager, and a live Cognito pool. Use the mock for frontend development and the real deployed stack for backend testing.
