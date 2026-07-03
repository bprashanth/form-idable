# Scaling and Cost

This document describes where concurrency limits apply, what the AWS free tier covers, and estimated cost per form above the free tier. All cost figures use an exchange rate of roughly re 85 per USD and should be treated as ballpark estimates since both AWS pricing and the exchange rate change over time.

---

## Concurrency model

The system has three distinct concurrency zones. Understanding them separately is important because they have very different characteristics and limits.

The first zone is API request concurrency, handled by the Lambda function. The Lambda is configured with `RESERVED_CONCURRENCY=10`, meaning at most 10 API requests can be in flight simultaneously. Each request is fast (a few hundred milliseconds for a status poll, two to three seconds for an upload) so in practice 10 concurrent users can be served without queuing. If more than 10 simultaneous requests arrive, the excess are throttled with a 429 response. Raising `RESERVED_CONCURRENCY` in `config.sh` and redeploying is all that is needed to lift this limit.

The second zone is form processing concurrency, handled by Fargate tasks. Each uploaded form launches one Fargate task. Tasks run fully in parallel with no coordination between them. The default AWS limit is 250 running tasks per region per account. For a small team uploading a few dozen forms at once this is not a concern. If that limit is approached, AWS Support can raise it on request. One risk worth noting: if ECS cannot launch a task (e.g. the limit is hit), the job stays in status `queued` indefinitely with no automatic retry. A monitoring alert on stale `queued` jobs is advisable at larger scale.

The third zone is within-form processing concurrency. The codex CLI runs as a single process inside the Fargate task, working through one form sequentially. Multi-page forms are processed page by page. There is no parallelism within a single job, so a 20-page form takes roughly 20x the time of a 1-page form.

---

## Parallel request patterns in the review UI

When a user opens the review page, the PWA makes several concurrent requests. It fetches the manifest JSON, the xlsx, and then all page and crop images in parallel using presigned S3 URLs. S3 has no meaningful concurrency limit at this scale, so loading a review with 30+ images is fine. The Lambda is not involved in these reads -- all assets go directly from S3 to the browser.

---

## Free tier coverage

AWS provides a 12-month free tier for new accounts. The following estimates are for the formidable workload specifically.

```
Service      | Free tier                         | Roughly covers
------------ | --------------------------------- | -------------------------------------------
Lambda       | 1M requests + 400K GB-seconds/mo  | ~3,000 form uploads/month (2GB, 60s each)
DynamoDB     | 25 WCU + 25 RCU + 25 GB storage   | ~50,000 jobs (well above expected volume)
S3           | 5 GB storage + 20K GET + 2K PUT   | ~300 forms at 15 MB each, then pay per use
API Gateway  | 300M calls/month (first 12 mo)    | Effectively unlimited at this scale
Cognito      | 50,000 MAU (permanent, no expiry) | Permanent
SES          | 62,000 emails/month from Lambda   | Permanent
```

Two components have no free tier and are billed from the first use: Fargate compute and the OpenAI API (used by the codex CLI). These are the dominant costs.

---

## Cost per form above the free tier

The figures below are for a typical single-page ecology form taking around 10 minutes to process. Multi-page forms or complex layouts take longer and cost proportionally more.

**OpenAI API (codex CLI).** Experiments on real forms show roughly 19,000 tokens per form. At GPT-4.1 pricing ($2 per million input tokens, $8 per million output tokens), assuming a 14K input and 5K output split, the API cost is approximately $0.068 per form, which is re 5.80. This is the largest and most variable cost. Complex forms, retries, or switching to a more capable model can push this to re 15 to 25.

**Fargate compute.** The task definition uses 2 vCPU and 4 GB memory. At current Fargate spot prices in ap-south-1 (approximately $0.04 per vCPU-hour and $0.004 per GB-hour), a 10-minute task costs around re 1.40. A 30-minute task costs around re 4.

**S3 storage and requests.** Each form stores roughly 15 MB (PDF, page renders, crops, xlsx). Storage costs re 0.10 per form per month. GET and PUT request costs are negligible.

**Lambda, API Gateway, SES, DynamoDB.** At the volumes expected for a small NGO these costs are below re 0.50 per form combined.

A rough total: re 7 to 12 per form for a standard single-page form, and re 18 to 35 for a complex multi-page form with longer processing time.

---

## Known bottlenecks and how to address them

**Lambda concurrency cap.** The current limit of 10 simultaneous requests is deliberate -- it prevents runaway API costs if the UI has a polling bug. If the team grows, raise `RESERVED_CONCURRENCY` to 25 or 50 in `config.sh` and redeploy.

**Fargate task cold start.** Fargate tasks take 30 to 60 seconds to start before codex begins running. This cold start is visible to the user as a delay before the progress indicator moves. It cannot easily be eliminated in the current architecture. Keeping the worker image small reduces it slightly.

**OpenAI rate limits.** The codex CLI talks to the OpenAI API. Free or low-tier OpenAI accounts have tight rate limits (e.g. 500 requests per minute for GPT-4.1). If multiple Fargate tasks run simultaneously and each makes many API calls, rate limiting can slow processing or cause retries. Upgrading to a higher OpenAI tier resolves this.

**SES sandbox.** In sandbox mode, both sender and recipient email addresses must be individually verified. This means notification emails only work for pre-registered recipients. Requesting production access from the SES console removes this restriction. In production mode the sending limit is 200 emails per second, which is more than sufficient.

**DynamoDB on-demand vs provisioned.** The table currently uses on-demand mode, which costs more per request than provisioned but requires no capacity planning. At low job volumes on-demand is cheaper. If the team scales to hundreds of forms per day, provisioned capacity with auto-scaling would reduce DynamoDB costs by roughly 50 percent.
