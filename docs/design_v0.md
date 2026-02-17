 Phase 5: Dockerize, Deploy to AWS Lambda, Cognito Auth                    

 Context

 The FastAPI server (server/) runs locally with uvicorn and uses ~/.aws credentials for Textract. We need to containerize it, deploy to Lambda, put API Gateway in front with Cognito JWT
 auth, and wire the PWA to authenticate and call the deployed backend.

 The existing Cognito pool (ap-south-1_28HVATwK2, client 1j0f2k3top2af4m8da7nbmeu63) is reused — shared with photomon. Auth config is fetched at runtime from
 https://fomomon.s3.ap-south-1.amazonaws.com/auth_config.json.

 Users are admin-created via the fomomon admin UI (localhost:8090), which calls admin_create_user + admin_set_user_password(Permanent=True) — so there is no temp password /
 NEW_PASSWORD_REQUIRED challenge. Users log in directly with the credentials the admin set.

 Decisions

 - Lambda Web Adapter (not Mangum) — same Docker image runs uvicorn locally and on Lambda, zero code changes to FastAPI
 - API Gateway HTTP API with native JWT authorizer — 30s timeout acceptable, add provisioned concurrency later if needed
 - Reuse existing Cognito pool + client — no new pool/client creation
 - Custom Vue login form using amazon-cognito-identity-js — simple email+password, no password-reset flow needed. Composable is reusable across Vue 3 apps (photomon web, form-idable, etc.)
 since it fetches config from S3
 - Both local dev paths — bare uvicorn for fast iteration, docker compose for integration testing before push
 - Auth config from S3 — fetched at runtime, not baked into env vars
 - deploy/add-user.sh mirrors the admin backend pattern: admin_create_user + admin_set_user_password(Permanent=True) + MessageAction=SUPPRESS

 Changes

 1. Dockerfile — server/Dockerfile (new)

 FROM public.ecr.aws/docker/library/python:3.12-slim
 COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
 ENV PORT=8070 AWS_LWA_PORT=8070 AWS_LWA_READINESS_CHECK_PATH=/api/health
 WORKDIR /var/task
 COPY requirements.txt ./
 RUN pip install --no-cache-dir -r requirements.txt
 COPY . .
 CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8070"]

 Adapter binary is inert without Lambda Runtime API → same image works with docker run.

 2. Docker ignore — server/.dockerignore (new)

 Exclude __pycache__/, *.pyc, *.xlsx, test/, .git.

 3. Docker compose — docker-compose.yml (new, project root)

 services:
   server:
     build:
       context: ./server
     ports:
       - "8070:8070"
     volumes:
       - ~/.aws:/root/.aws:ro
     environment:
       - AWS_REGION=ap-south-1
       - AWS_DEFAULT_REGION=ap-south-1

 4. Deploy scripts — deploy/ (new directory)

 deploy/config.sh — shared constants

 - AWS_REGION, AWS_ACCOUNT_ID, ECR repo name, Lambda function name, IAM role name, API Gateway name
 - Cognito pool ID + client ID hardcoded (from auth_config.json: ap-south-1_28HVATwK2 / 1j0f2k3top2af4m8da7nbmeu63)

 deploy/setup.sh — one-time idempotent infra setup

 Checks-before-create pattern throughout:

 1. ECR repository — form-idable-server
 2. IAM role — trust policy (Lambda) + inline policy: textract:AnalyzeDocument, CloudWatch logs
 3. API Gateway HTTP API — CORS config exposing X-Form-Summary header
 4. JWT authorizer — issuer: Cognito pool URL, audience: client ID
 5. Routes: GET /api/health (no auth), all POST /api/* (JWT required)
 6. Lambda integration — AWS_PROXY, payload format 2.0
 7. Stage — prod with auto-deploy
 8. Lambda invoke permission for API Gateway
 9. Writes resource IDs to deploy/outputs.env

 deploy/build.sh — build + optional smoke test

 - docker build -t form-idable-server:latest ./server/
 - With --test: run container, curl /api/health, stop

 deploy/push.sh — ECR login, tag, push, create/update Lambda

 - If Lambda exists → update-function-code, else create-function (512MB, 60s timeout)
 - aws lambda wait function-active-v2

 deploy/deploy.sh — orchestrator

 Runs build.sh --test then push.sh, prints API Gateway URL.

 deploy/add-user.sh <email> <password>

 Mirrors fomomon admin pattern:
 aws cognito-idp admin-create-user --username "$EMAIL" --temporary-password "$PASS" --message-action SUPPRESS ...
 aws cognito-idp admin-set-user-password --username "$EMAIL" --password "$PASS" --permanent ...
 No temp password email, no forced reset. User logs in directly.

 deploy/trust-policy.json + deploy/lambda-policy.json

 5. Auth composable — pwa/src/composables/useCognitoAuth.js (new)

 Reusable across any Vue 3 app. Uses amazon-cognito-identity-js.

 // Fetches config from S3 at init (same URL as Dart app)
 // https://fomomon.s3.ap-south-1.amazonaws.com/auth_config.json

 init()              // fetch S3 config → create CognitoUserPool
 login(user, pass)   // USER_PASSWORD_AUTH → session → store idToken ref
 refreshSession()    // getSession() auto-refreshes via localStorage refresh token
 logout()            // signOut() + clear refs

 // Exports
 idToken             // ref — JWT for API Gateway Authorization header
 isAuthenticated     // computed
 authError           // ref

 No NEW_PASSWORD_REQUIRED handling — admin sets permanent passwords.

 6. API fetch wrapper — pwa/src/composables/useApi.js (new)

 export async function apiFetch(path, options = {}) {
   const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
   // Attach Bearer token from useCognitoAuth
   // On 401: refreshSession() then retry once
 }

 In dev (VITE_API_BASE_URL empty) → vite proxy → localhost:8070. In prod → API Gateway URL.

 7. Login view — pwa/src/views/LoginView.vue (new)

 Simple dark-themed form matching existing views:
 - Username + password fields
 - Submit → login() → on success redirect to capture
 - Error text for wrong credentials
 - No password reset, no signup — admin manages users

 8. Router update — pwa/src/router.js (edit)

 - Add /login route (unguarded)
 - Auth guard in beforeEach: if not authenticated → try refreshSession() → if fails → redirect to /login

 9. ProcessingView update — pwa/src/views/ProcessingView.vue (edit)

 Replace fetch('/api/upload', ...) with apiFetch('/api/upload', ...).

 10. AppHeader update — pwa/src/components/AppHeader.vue (edit)

 Add logout button → logout() → redirect to /login.

 11. Frontend env — pwa/.env.production (new)

 VITE_API_BASE_URL=https://<api-id>.execute-api.ap-south-1.amazonaws.com/prod

 Cognito config comes from S3 at runtime, not env vars.

 12. Gitignore — .gitignore (edit)

 Add deploy/outputs.env.

 File Summary

 ┌───────────────────────────────────────┬───────────────────────────────────────┐
 │                 File                  │                Action                 │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ server/Dockerfile                     │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ server/.dockerignore                  │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ docker-compose.yml                    │ Create (project root)                 │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ deploy/config.sh                      │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ deploy/setup.sh                       │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ deploy/build.sh                       │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ deploy/push.sh                        │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ deploy/deploy.sh                      │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ deploy/add-user.sh                    │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ deploy/trust-policy.json              │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ deploy/lambda-policy.json             │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ pwa/src/composables/useCognitoAuth.js │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ pwa/src/composables/useApi.js         │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ pwa/src/views/LoginView.vue           │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ pwa/.env.production                   │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ pwa/src/router.js                     │ Edit — add /login route + auth guard  │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ pwa/src/views/ProcessingView.vue      │ Edit — use apiFetch                   │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ pwa/src/components/AppHeader.vue      │ Edit — add logout                     │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ pwa/package.json                      │ Edit — add amazon-cognito-identity-js │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ .gitignore                            │ Edit                                  │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ docs/server_design.md                 │ Create                                │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ docs/cross_app_auth.md                │ Create                                │
 └───────────────────────────────────────┴───────────────────────────────────────┘

 13. Documentation — docs/server_design.md (new)

 Documents the server architecture: Dockerfile, Lambda Web Adapter, deploy scripts, IAM, API Gateway + JWT authorizer, how local dev and prod use the same image, env vars.

 14. Documentation — docs/cross_app_auth.md (new)

 Architecture doc covering all apps in the ecosystem, with block diagram:

 ┌─────────────────────────────────────────────────────────────────┐
 │                        ADMIN (user management)                  │
 │  fomomon admin UI (localhost:8090)                              │
 │  admin_create_user + admin_set_user_password(Permanent=True)    │
 │  → Cognito User Pool (ap-south-1_28HVATwK2)                    │
 └────────────────────────────┬────────────────────────────────────┘
                              │ users added here
                              ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │              COGNITO USER POOL (shared, single)                 │
 │  Pool: ap-south-1_28HVATwK2                                    │
 │  Client: 1j0f2k3top2af4m8da7nbmeu63                            │
 │  Identity Pool: ap-south-1:33c1f27d-fe67-4109-a08d-06aaa893d649│
 │  Config: s3://fomomon/auth_config.json                          │
 │                                                                 │
 │  All apps fetch auth_config.json from S3 at startup             │
 │  All apps use the same pool/client for login                    │
 │  USER_PASSWORD_AUTH flow (admin sets permanent passwords)        │
 └──────┬──────────────┬──────────────┬────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
 ┌──────────┐  ┌──────────────┐  ┌────────────────┐
 │ fomomon  │  │ fomo web     │  │ scribe (PWA)   │
 │ Flutter  │  │ Vue 3 app    │  │ Vue 3 PWA      │
 │ mobile   │  │ dashboard    │  │ form capture   │
 │          │  │              │  │                │
 │ Dart SDK │  │ JS SDK       │  │ JS SDK         │
 │ cognito  │  │ cognito      │  │ cognito        │
 │ identity │  │ identity     │  │ identity       │
 └────┬─────┘  └──────┬───────┘  └───────┬────────┘
      │               │                  │
      │  JWT token    │  JWT token       │ JWT token
      ▼               ▼                  ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │              S3 BUCKET (fomomon, IAM-protected)                 │
 │  Photos, configs, sites.json, users.json, auth_config.json      │
 │  Access via: presigned URLs (Flutter) or Lambda endpoint (web)  │
 └─────────────────────────────────────────────────────────────────┘
      ▲                                  ▲
      │  presigned URLs                  │  Bearer JWT
      │  (Identity Pool                  │
      │   temp credentials)              │
 ┌────┴─────────────────┐  ┌────────────┴──────────────────────────┐
 │ fomomon Flutter app  │  │  SERVERLESS BACKEND (Lambda)          │
 │ uses CognitoIdentity │  │  FastAPI behind API Gateway           │
 │ → temp AWS creds     │  │  JWT authorizer validates Cognito     │
 │ → presigned S3 URLs  │  │  tokens at gateway level              │
 │                      │  │                                       │
 │                      │  │  Endpoints:                           │
 │                      │  │  POST /api/upload (Textract → xlsx)   │
 │                      │  │  POST /api/presign (future: S3 URLs)  │
 │                      │  │  GET  /api/health (no auth)           │
 └──────────────────────┘  └───────────────────────────────────────┘

 Content sections:
 1. Ecosystem overview — all apps, what each does, how they connect
 2. Cognito pool — shared pool, config in S3, admin creates users via fomomon admin
 3. Login flow per app — Flutter (Dart SDK), Vue 3 (amazon-cognito-identity-js), same pool
 4. Adding Cognito auth to a new Vue 3 app — step-by-step: install SDK, copy useCognitoAuth.js, add LoginView, add router guard, add useApi.js
 5. Calling the Lambda backend — set VITE_API_BASE_URL, use Bearer token
 6. S3 access patterns — Flutter uses Identity Pool temp creds → presigned URLs; web apps call Lambda /api/presign endpoint with JWT
 7. Example: fomo web app — currently uses Google OAuth whitelist, migration path to add Cognito

 Implementation Order

 Phase A: Documentation (first)
 1. Write docs/server_design.md
 2. Write docs/cross_app_auth.md

 Phase B: Docker + Deploy scripts
 3. server/Dockerfile + .dockerignore + docker-compose.yml → verify docker compose up + health check
 4. deploy/config.sh + deploy/build.sh → build image + local smoke test
 5. deploy/setup.sh (ECR + IAM only) → create repo + role
 6. deploy/push.sh → push image, create Lambda
 7. deploy/setup.sh (API Gateway + JWT authorizer) → wire routes
 8. Verify: curl <apigw>/api/health (200), curl <apigw>/api/upload without token (401)
 9. deploy/add-user.sh → create test user
 10. Verify: get token via CLI, curl protected endpoint with Bearer token (200)

 Phase C: Frontend auth
 11. pwa: npm install amazon-cognito-identity-js, create useCognitoAuth.js + useApi.js
 12. pwa: create LoginView.vue, update router.js with auth guard
 13. pwa: update ProcessingView.vue + AppHeader.vue
 14. pwa: create .env.production, build + deploy to Netlify
 15. End-to-end: login → capture → crop → process → result → download/drive save

 Verification

 # 1. Local Docker
 docker compose up --build -d
 curl http://localhost:8070/api/health                    # → {"status":"ok"}
 curl -X POST http://localhost:8070/api/upload/json \
   -H "Content-Type: application/json" \
   -d @server/test/000_layout.json -o /tmp/test.xlsx -w "%{http_code}"  # → 200
 docker compose down

 # 2. Deploy infra + Lambda
 cd deploy && ./setup.sh && ./deploy.sh
 source outputs.env
 curl "${APIGW_URL}/api/health"                           # → 200
 curl -X POST "${APIGW_URL}/api/upload" -w "%{http_code}" # → 401

 # 3. Auth test (use existing user or add-user.sh)
 ./add-user.sh testuser@example.com SomePassword123
 # Get token:
 TOKEN=$(aws cognito-idp admin-initiate-auth \
   --user-pool-id ap-south-1_28HVATwK2 \
   --client-id 1j0f2k3top2af4m8da7nbmeu63 \
   --auth-flow ADMIN_USER_PASSWORD_AUTH \
   --auth-parameters USERNAME=testuser@example.com,PASSWORD=SomePassword123 \
   --query 'AuthenticationResult.IdToken' --output text)
 curl -X POST "${APIGW_URL}/api/upload/json" \
   -H "Authorization: Bearer ${TOKEN}" \
   -H "Content-Type: application/json" \
   -d @server/test/000_layout.json -o /tmp/lambda.xlsx -w "%{http_code}"  # → 200

 # 4. Frontend
 cd pwa && npm run dev
 # Login → capture → process → result → works

