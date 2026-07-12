# Multi-user Architecture Design

Post-MVP extension. The current system supports one user uploading forms and
reviewing them. This document describes how to extend it so many field workers
can submit data, an admin can see all data on a map, and access is governed
by explicit per-worker consent.

**Status:** not yet built. Everything in this document is design, not code.

---

## Current state (single-user baseline)

Read `docs/architecture.md` for the full system diagram. The relevant parts:

- Cognito user pool `ap-south-1_28HVATwK2` with client `6ks3cg4jmvqgaqo3n3gdmqpuul`. All
  users are in the same pool with no group assignments.
- Every POST /vision/extract reads `user_id` from the Cognito JWT claims and
  stores it in the DynamoDB `formidable-jobs` table alongside the job record.
- GET /vision/jobs filters on `user_id`, so each user sees only their own jobs.
- No location data is collected.
- No admin view exists.

This is not a dead end. `user_id` is already stored per job. The single-user
code is the multi-user code with the admin paths and map view missing.

---

## What changes

### 1. Cognito groups

Add two groups to the existing user pool:

```
field-workers   Default group for all end users uploading forms.
admins          Org staff who can see all data and the map view.
```

Assign every existing user to `field-workers`. Assign admin accounts to both
groups (Cognito allows multiple group memberships).

When Cognito issues a JWT, it includes a `cognito:groups` claim listing the
user's groups. The Lambda already receives and validates the JWT via the API
Gateway Cognito authorizer. The only code change is: extract `cognito:groups`
from the decoded token and check group membership before allowing admin paths.

No Cognito configuration change is needed beyond creating the groups and
assigning users. The existing user pool, client, and JWT authorizer are reused
as-is.

### 2. Location data

Add two optional fields to POST /vision/extract:

```
lat    float    WGS84 latitude, e.g. 12.9716
lng    float    WGS84 longitude, e.g. 77.5946
```

Store them in the DynamoDB job record. If the frontend passes them, they appear
in the map view. If not, the job is created normally and simply has no pin on
the map.

The PWA can populate these via `navigator.geolocation.getCurrentPosition()` at
upload time. The user should be shown a prompt ("Allow location access to pin
this submission on the admin map") so they understand why it's being requested.
If they deny, the form is still uploaded, just without coordinates.

### 3. Publish flag

Add a boolean field `published` (default `false`) to each DynamoDB job record.

A field worker can flip this per-job from the review page ("Share with org"
toggle). Once published, the job appears in the admin map view. Unpublished jobs
are visible only to the worker who created them.

This is Option B from the design discussion. See the Permission model section
below for alternatives.

### 4. New API routes

All new routes go through the existing API Gateway (`hachry61xe`) and require a
Cognito JWT. Admin routes additionally require the JWT to contain `admins` in
`cognito:groups`; the Lambda returns 403 if not.

```
PATCH  /vision/jobs/{job_id}/publish     field-worker    Toggle published flag (true/false in body)
GET    /vision/map                       admin           Return all published jobs with coordinates
GET    /vision/jobs?scope=all            admin           Return all jobs across all users (for admin list view)
```

The PATCH route must verify the requesting user owns the job before allowing the
update (compare JWT `sub` claim against the job's `user_id`).

The GET /vision/map response shape:

```json
{
  "jobs": [
    {
      "job_id": "bd6a19ac-...",
      "user_id": "us-east-1:...",
      "lat": 12.9716,
      "lng": 77.5946,
      "status": "done",
      "filename": "GridVegetation_Block3.pdf",
      "created_at": "2026-06-15T10:32:00Z"
    }
  ]
}
```

Jobs with null lat/lng are excluded from this response. The `user_id` field
lets the admin know which worker submitted the job but does not expose PII
directly -- the admin would need a separate lookup to map `user_id` to a name
or email (that mapping is in Cognito and can be fetched via the Cognito admin
SDK if needed).

### 5. Frontend: admin map view

New route in the PWA: `/map` (admin-only, guarded by group check in
`router.beforeEach`). Fetches `GET /vision/map` and renders pins using
Leaflet.js (`leaflet` npm package, ~40KB gzipped). Each pin is clickable and
navigates to `/review/{job_id}`. The admin can already open any job's review
page since the review page fetches assets via presigned S3 URLs that the Lambda
issues after checking job ownership -- the Lambda ownership check needs to be
relaxed for admins (skip the `user_id` filter if the JWT has `admins` group).

### 6. Frontend: publish toggle

In `JobReviewView.vue`, add a toggle in the toolbar next to "Submit Review":
"Share with org" / "Private". On change, PATCH /vision/jobs/{job_id}/publish.
Persist the current state from the job record returned by GET /vision/jobs/{job_id}
(add `published` to the response there).

---

## Permission model options

Three designs in increasing complexity. The current design spec is Option B.

```
Option A: Blanket consent at onboarding
  Field workers agree at signup that the org owns all submitted data. No
  per-record control. Every job is visible to admins. Appropriate if workers
  are org employees with no personal stake in the data. Requires no new
  DynamoDB fields and no frontend changes beyond adding the admin map view.

Option B: Publish flag (CURRENT SPEC)
  Each job defaults to private (published=false). The worker explicitly shares
  individual jobs via a toggle in the review page. Admin sees only published
  jobs on the map. Workers control their own data per submission.

Option C: Access request flow
  Admin sends a data access request targeting a specific worker. Worker receives
  an SES email with Approve/Deny links. Approval stores a record in a new
  DynamoDB table (form: {requester_id, owner_id, approved_job_ids, expires_at}).
  Admin can then access approved jobs for the agreed scope. Most worker-friendly
  for sensitive data (e.g. location-identifying surveys in conflict zones), most
  implementation work (~3-4 days beyond Option B).
```

Option C requires a new DynamoDB table, two new Lambda routes (POST
/vision/access-requests, POST /vision/access-requests/{id}/respond), and SES
templated emails with token-signed approve/deny links. Not scoped now.

---

## DynamoDB schema additions

The existing `formidable-jobs` table gets three new attributes on job records.
DynamoDB is schemaless so no migration is needed -- new attributes are simply
absent on existing records (treat as null/false).

```
lat          Number     WGS84 latitude, absent if not captured
lng          Number     WGS84 longitude, absent if not captured
published    Boolean    false if absent; true once worker shares the job
```

No new tables needed for Options A or B. Option C adds a `formidable-permissions`
table (not scoped).

---

## Lambda code changes

All changes are in the Lambda FastAPI handler (`good-shepherd/agents/formidable/`).
The Fargate worker does not change.

1. Add a helper `get_user_groups(token_claims: dict) -> list[str]` that reads
   `cognito:groups` from the decoded JWT claims (already available in the route
   handler via the API Gateway event context).

2. Add a helper `require_group(claims, group)` that raises HTTP 403 if the
   group is not in the user's list.

3. Modify GET /vision/jobs: if `scope=all` is in the query params and the caller
   is in `admins`, omit the `user_id` filter on the DynamoDB scan. Otherwise
   behave as today.

4. Modify GET /vision/jobs/{job_id}: if the caller is in `admins`, skip the
   ownership check. Otherwise require `user_id` match.

5. Add PATCH /vision/jobs/{job_id}/publish: load job, verify ownership, update
   `published` attribute.

6. Add GET /vision/map: require `admins` group. DynamoDB scan with filter
   `attribute_exists(lat) AND published = true`. Return the slim response shape
   above.

7. Modify POST /vision/extract: accept optional `lat` and `lng` fields in the
   JSON body; store them in DynamoDB if present.

---

## Rollout order

Build in this order to keep each step independently shippable:

1. Cognito groups: create groups, assign users. Zero code change. Verify by
   decoding a JWT and checking the `cognito:groups` claim.

2. Location capture + storage: add lat/lng to the upload form (with browser
   geolocation prompt), add to POST /vision/extract, store in DynamoDB. No new
   UI views. Verify by checking a new job record in the DynamoDB console.

3. Publish flag: add `published` to DynamoDB, add PATCH route, add toggle in
   the review page. Verify by toggling in the UI and checking DynamoDB.

4. Admin map view: add GET /vision/map route, add `/map` page in the PWA with
   Leaflet, guard with group check in the router. Verify by logging in as an
   admin and seeing pins.

5. Admin list view: modify GET /vision/jobs to support `scope=all`, add a
   separate admin section in the dashboard. Verify by seeing all jobs across
   users.

Each step can be deployed independently via the existing `push.sh` (backend) and
Netlify auto-deploy (frontend). No step requires another to be complete.

---

## What does not change

- The Cognito user pool, client ID, JWT authorizer, and `auth_config.json` S3
  object. New users are added the same way (via Cognito console or admin SDK).
- The Fargate worker. It receives `user_id` from the Lambda at task launch but
  does not use it for any access control -- it just passes it through to
  DynamoDB via the progress update path.
- The S3 layout and presigned URL model. Admins access job assets via the same
  presigned URLs issued by the Lambda; the only change is that the Lambda stops
  enforcing `user_id` ownership on presigned URL generation for admin callers.
- The evals / QA report feature (see `docs/design/evals.md`). It uses
  `job_id` and does not depend on the single-user assumption.
