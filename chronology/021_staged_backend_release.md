# 021 — Staged credential, Low and High production release

Date: 2026-08-18

## Scope

Release the backend ownership and deployment-mode changes from Good Shepherd
commit `6aa5af8` without combining authentication and image changes. The release
was deliberately split into credentials, Low and High stages. Each stage ran a
real Low job and a real High job through Cognito, API Gateway, S3, DynamoDB and
Fargate. No PWA source changed in this release.

## Starting state

- shared API image: `sha256:a59e4c7c147dce26d703dc4bb063cdfaf67837f5c8c5c3d4f5138f6722ad4680`
- Low image: `sha256:aacbe354d16bb79dda0ac30239e8d59a12b1353ab8ad75a245a5840fc21cc9bc`
- Low task: `formidable-worker:15` (implicit x86_64)
- High image: `sha256:231f223f3fd8a0a478a9a1669d20da855241bca70d7f43b2071e97fe10fbf627`
- High task: `formidable-high-worker:7` (ARM64)

The reviewed Good Shepherd commits were pushed to `origin/main` before the
first code release. Unrelated untracked files elsewhere in that repository were
not staged or included.

## Stage 1 — credentials only

Command: `./deploy.sh credentials`

The Codex login was published as Secrets Manager version
`14bf0062-7ea5-4add-83c3-1f33e059a7e2`. No image or task definition changed.
The rollback wrapper retained the previous version as `AWSPREVIOUS` but did not
need to restore it.

- Low job `56abd703-8ba2-4ab2-bf0b-f00beeeef9f3`: PASS; cell coverage 0.80,
  numeric recall 0.70 and word recall 0.50.
- High job `10ccbe5e-9bf6-44b5-acc9-5014c80e7e56`: PASS; agentic-primary route,
  three pages, 10 disagreement targets and three ecology flags.

## Stage 2 — Low only

Command: `./deploy.sh low`

The shared handler and Low worker were built for x86_64. Low task revision 16
now records the runtime architecture explicitly. The High digest and task
revision remained unchanged throughout the stage.

- Low job `9de9105f-6421-4c67-8edc-1ff6e62aeb8d`: PASS; cell coverage 0.79,
  numeric recall 0.71 and word recall 0.49.
- unchanged-High job `23edf804-7392-46a9-8b1e-d5eae2682056`: PASS;
  agentic-primary route, three pages, 19 disagreement targets and three ecology
  flags.

## Stage 3 — High only

Command: `./deploy.sh high`

The self-contained Good Shepherd High image built for ARM64 and passed its
container import smoke before upload. The accepted Low image digest and task
revision remained unchanged throughout the stage.

- unchanged-Low job `7b11d80f-719f-4114-a1bd-10d49086d966`: PASS; cell
  coverage 0.82, numeric recall 0.72 and word recall 0.48.
- High job `68adec26-8ea4-4495-ba59-20f90fccd03c`: PASS; agentic-primary route,
  three pages, 14 disagreement targets and three ecology flags.

## Accepted production state

- shared API image and Lambda code:
  `sha256:4d55d9c9325d44e5e0f042d39724b4808e8c8a543fa263d9110e718776c0f3da`
- Low image:
  `sha256:e8f8c06493eef380b932809f1229603dd236011102012867a1efc6dd546cf4e2`
- Low task: `formidable-worker:16`, explicit `X86_64` / `LINUX`
- High image:
  `sha256:d72a30606aa374d00fb939386310f7872e6f8d9052242a9bd874b51b813f48d5`
- High task: `formidable-high-worker:8`, explicit `ARM64` / `LINUX`
- Lambda routes name both `formidable-worker` and `formidable-high-worker`.

All three rollback-protected stages passed, so no rollback was executed. These
were production API/artifact gates rather than a new visual UX benchmark: no
PWA runtime code changed, and the High pipeline promoted into Good Shepherd was
byte-identical to the previously accepted production pipeline.
