# Phase 5 Checkpoint — Docker, Lambda, Cognito Auth

**Branch:** `assistant`
**Status:** Infra deployed and verified. Health endpoint working. Frontend auth not yet tested.

## What was done

Created 17 new files, edited 6 existing files. See the full file list at the
bottom.

- **Docker**: `server/Dockerfile` (Python 3.12-slim + Lambda Web Adapter),
  `server/.dockerignore`, `docker-compose.yml`
- **Deploy scripts**: `deploy/{config,setup,build,push,deploy,add-user}.sh`,
  `deploy/{trust-policy,lambda-policy}.json`
- **Frontend auth**: `useCognitoAuth.js` composable (fetches config from S3),
  `useApi.js` (Bearer token + 401 retry), `LoginView.vue`, router auth guard,
  logout button in AppHeader
- **Docs**: `docs/server_design.md`, `docs/cross_app_auth.md`

## What remains

Steps 1–5 are done. Pick up from Step 6 (create test user) onward.

## Gotchas discovered during deploy

1. **Lambda invoke permission**: `setup.sh` creates the API Gateway before the
   Lambda exists, so it can't grant the invoke permission. Fix: `push.sh` now
   grants the permission after creating/updating the Lambda.

2. **Stage path prefix**: API Gateway `prod` stage prepends `/prod` to the path,
   so Lambda receives `/prod/api/health` instead of `/api/health`. Fix: `push.sh`
   sets `AWS_LWA_REMOVE_BASE_PATH=/prod` env var on the Lambda so the Web
   Adapter strips the prefix before forwarding to uvicorn.

---

## Step 1 — Local server (bare uvicorn)

Confirm the server still works without Docker first.

```bash
cd server
uvicorn main:app --host 0.0.0.0 --port 8070 --reload
```

In another terminal:

```bash
# Health check
curl -s http://localhost:8070/api/health
# Expected: {"status":"ok"}

# JSON endpoint (no Textract call, uses saved layout)
curl -s -X POST http://localhost:8070/api/upload/json \
  -H "Content-Type: application/json" \
  -d @server/test/000_layout.json \
  -o /tmp/test_bare.xlsx -w "HTTP %{http_code}\n"
# Expected: HTTP 200, valid xlsx in /tmp/test_bare.xlsx

# Full pipeline (requires ~/.aws credentials with Textract access)
curl -s -X POST http://localhost:8070/api/upload \
  -F "image=@server/test/handwritten.jpg" \
  -o /tmp/test_live.xlsx -w "HTTP %{http_code}\n"
# Expected: HTTP 200
```

Stop uvicorn before proceeding.

## Step 2 — Docker Compose (local container)

```bash
# Build and start
docker compose up --build -d

# Wait a few seconds for startup, then test
sleep 3
curl -s http://localhost:8070/api/health
# Expected: {"status":"ok"}

# JSON endpoint through container
curl -s -X POST http://localhost:8070/api/upload/json \
  -H "Content-Type: application/json" \
  -d @server/test/000_layout.json \
  -o /tmp/test_docker.xlsx -w "HTTP %{http_code}\n"
# Expected: HTTP 200

# Full pipeline through container (uses mounted ~/.aws credentials)
curl -s -X POST http://localhost:8070/api/upload \
  -F "image=@server/test/handwritten.jpg" \
  -o /tmp/test_docker_live.xlsx -w "HTTP %{http_code}\n"
# Expected: HTTP 200

# Clean up
docker compose down
```

**Troubleshooting:**
- If Textract calls fail, verify `~/.aws/credentials` exists and has a profile
  with `textract:AnalyzeDocument` permission in `ap-south-1`.
- If the container won't start, check `docker compose logs server`.

## Step 3 — Deploy infra (one-time)

Requires AWS CLI configured with admin-level access.

```bash
cd deploy

# Verify AWS identity
aws sts get-caller-identity

# Create ECR repo, IAM role, API Gateway, JWT authorizer, routes
./setup.sh
```

This is idempotent — safe to re-run. On success it prints the API Gateway URL
and writes `deploy/outputs.env`.

**Verify outputs.env was created:**

```bash
cat deploy/outputs.env
# Should contain: APIGW_ID, APIGW_URL, LAMBDA_ARN, ROLE_ARN, AUTH_ID
```

## Step 4 — Build, push, deploy Lambda

```bash
cd deploy

# Build image, run smoke test, push to ECR, create/update Lambda
./deploy.sh
```

This runs `build.sh --test` (starts container on port 8071, curls health, stops)
then `push.sh` (ECR login, tag, push, create or update Lambda, set
`AWS_LWA_REMOVE_BASE_PATH=/prod` env var, grant API Gateway invoke permission).

## Step 5 — Verify deployed API

```bash
source deploy/outputs.env

# Health (no auth required)
curl -s "${APIGW_URL}/api/health"
# Expected: {"status":"ok"}

# Upload without token (should be rejected)
curl -s -X POST "${APIGW_URL}/api/upload" -w "HTTP %{http_code}\n"
# Expected: HTTP 401

# Upload JSON without token
curl -s -X POST "${APIGW_URL}/api/upload/json" \
  -H "Content-Type: application/json" \
  -d @server/test/000_layout.json -w "HTTP %{http_code}\n"
# Expected: HTTP 401
```

## Step 6 — Create a test user

```bash
cd deploy
./add-user.sh testuser@example.com 'SomePassword123!'
```

## Step 7 — Get a token and test authenticated requests

```bash
source deploy/outputs.env
source deploy/config.sh

# Get ID token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id "$COGNITO_POOL_ID" \
  --client-id "$COGNITO_CLIENT_ID" \
  --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --auth-parameters 'USERNAME=testuser@example.com,PASSWORD=SomePassword123!' \
  --region "$AWS_REGION" \
  --query 'AuthenticationResult.IdToken' --output text)

echo "Token length: ${#TOKEN}"
# Should be ~1000+ chars, not "None"

# Authenticated JSON upload
curl -s -X POST "${APIGW_URL}/api/upload/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d @server/test/000_layout.json \
  -o /tmp/lambda_test.xlsx -w "HTTP %{http_code}\n"
# Expected: HTTP 200, valid xlsx

# Authenticated image upload (full Textract pipeline)
curl -s -X POST "${APIGW_URL}/api/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "image=@server/test/handwritten.jpg" \
  -o /tmp/lambda_live.xlsx -w "HTTP %{http_code}\n"
# Expected: HTTP 200
```

**Troubleshooting:**
- `admin-initiate-auth` requires the Cognito pool to have
  `ALLOW_ADMIN_USER_PASSWORD_AUTH` enabled on the client.
- If the token comes back as `None`, check that the user exists:
  `aws cognito-idp admin-get-user --user-pool-id $COGNITO_POOL_ID --username testuser@example.com`
- If Lambda returns 500, check CloudWatch logs:
  `aws logs tail /aws/lambda/form-idable-server --since 5m --region ap-south-1`

## Step 8 — Update PWA production env

After deploy, grab the API Gateway URL:

```bash
source deploy/outputs.env
echo "$APIGW_URL"
```

Edit `pwa/.env.production` and replace `REPLACE_ME` with the actual API ID:

```
VITE_API_BASE_URL=https://<actual-api-id>.execute-api.ap-south-1.amazonaws.com/prod
```

## Step 9 — Test PWA locally

```bash
# Start the backend (bare or docker)
cd server && uvicorn main:app --host 0.0.0.0 --port 8070 --reload &

# Start the PWA dev server (Vite proxies /api to localhost:8070)
cd pwa && npm run dev
```

Open the browser URL (usually `http://localhost:5173`). You should see the
**login page**. Log in with the test user credentials. After login you should
land on the capture view. The full flow:

1. **Login** — enter email + password → redirects to capture
2. **Capture** — take/upload photo
3. **Crop** — adjust crop area
4. **Processing** — uploads to `/api/upload` with Bearer token
5. **Result** — download xlsx

**Verify logout:** click "Logout" in header → should redirect to login. Manually
navigating to `/` while logged out should redirect to `/login`.

## Step 10 — Build and deploy PWA to production

```bash
cd pwa
npm run build
# dist/ folder is ready for Netlify/Vercel/S3
```

For Netlify: `netlify deploy --prod --dir=dist`

**End-to-end production test:**
1. Open deployed PWA URL
2. See login page (not capture — auth guard works)
3. Log in with test user
4. Capture a form photo
5. Crop → Processing (calls API Gateway with JWT)
6. Result page shows xlsx download

---

## File inventory

### New files (17)

| File | Purpose |
|---|---|
| `server/Dockerfile` | Python 3.12-slim + Lambda Web Adapter |
| `server/.dockerignore` | Exclude pycache, xlsx, test |
| `docker-compose.yml` | Local container with `~/.aws` mount |
| `deploy/config.sh` | Shared constants (region, ECR, Lambda, Cognito) |
| `deploy/setup.sh` | Idempotent infra: ECR, IAM, API Gateway, JWT authorizer |
| `deploy/build.sh` | Docker build + `--test` smoke test |
| `deploy/push.sh` | ECR push + Lambda create/update |
| `deploy/deploy.sh` | Orchestrator: build → test → push |
| `deploy/add-user.sh` | Create Cognito user with permanent password |
| `deploy/trust-policy.json` | Lambda assume-role trust policy |
| `deploy/lambda-policy.json` | Textract + CloudWatch Logs permissions |
| `pwa/src/composables/useCognitoAuth.js` | Cognito auth composable (fetches S3 config) |
| `pwa/src/composables/useApi.js` | `apiFetch()` with Bearer token + 401 retry |
| `pwa/src/views/LoginView.vue` | Email + password login form |
| `pwa/.env.production` | `VITE_API_BASE_URL` (needs real API ID) |
| `docs/server_design.md` | Server architecture doc |
| `docs/cross_app_auth.md` | Cross-app Cognito architecture doc |

### Edited files (6)

| File | Change |
|---|---|
| `pwa/src/router.js` | Added `/login` route + auth guard |
| `pwa/src/views/ProcessingView.vue` | `fetch` → `apiFetch` |
| `pwa/src/components/AppHeader.vue` | Added logout button |
| `pwa/src/main.js` | `useCognitoAuth().init()` before mount |
| `pwa/package.json` | Added `amazon-cognito-identity-js` dep |
| `.gitignore` | Added `deploy/outputs.env` |

---

## Key config values

| Item | Value |
|---|---|
| Cognito Pool ID | `ap-south-1_28HVATwK2` |
| Cognito Client ID | `1j0f2k3top2af4m8da7nbmeu63` |
| Auth config URL | `https://fomomon.s3.ap-south-1.amazonaws.com/auth_config.json` |
| AWS Region | `ap-south-1` |
| ECR repo | `form-idable-server` |
| Lambda function | `form-idable-server` |
| IAM role | `form-idable-lambda-role` |
| API Gateway name | `form-idable-api` |
| API Gateway ID | `hachry61xe` |
| API Gateway URL | `https://hachry61xe.execute-api.ap-south-1.amazonaws.com/prod` |
| Server port | `8070` |
