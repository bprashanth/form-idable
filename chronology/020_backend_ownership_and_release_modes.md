# 020 — Backend ownership and explicit release modes

Date: 2026-08-18

## Problem

The accepted High image was reproducible only when Good Shepherd and Formidable
were checked out as siblings. `Dockerfile.high` copied eight runtime modules
from Formidable's experimental `benchmarks/wide/` directory. This ensured the
first production image reused the evaluated prototype exactly, but it made a
backend deploy depend on a frontend/benchmark worktree. A dirty local model
experiment in `structured_pipeline.py` could therefore enter a production image
without being committed in the backend repository.

The original release wrapper also mixed Codex auth rotation with a Low image
release. After High was added, the High-only wrapper verified High while the
Low wrapper verified Low; neither expressed the fact that the Lambda router and
Codex secret are shared by both routes.

## Ownership decision

Production runtime code now belongs entirely to
`good-shepherd/agents/formidable/`. The exact committed pipeline used by the
accepted High release was promoted into `high_pipeline/`, and
`Dockerfile.high` copies it from the local backend context. Formidable retains
experimental copies, fixtures, scorers, saved artifacts, browser gates and the
cross-repository chronology. Experimental changes do not affect an image until
they are deliberately promoted to Good Shepherd and pass the release ladder.

This is a source-ownership change, not a model or selector change. The dirty
local provider/reasoning experiment was intentionally excluded from the copied
production baseline.

## Release decision

The backend dispatcher exposes four modes:

1. `credentials`: rotate only `formidable/codex-auth`, verify real Low and
   High, and restore the captured secret version on failure;
2. `low`: rebuild the shared Lambda and Low worker, assert High image/task are
   unchanged, and verify both routes;
3. `high`: rebuild the shared Lambda and High worker, assert Low image/task are
   unchanged, and verify both routes;
4. `all`: rebuild the shared Lambda and both workers, then verify both routes.

Code modes never rotate auth. Credential mode never rebuilds an image. The
shared Lambda is the reason every code mode verifies both routes even when only
one worker changes.

The audit also found that the historical Low build inherited its architecture
from the deployment host. Lambda and Low are now explicitly built/registered as
x86_64 while High remains explicitly ARM64. The local Lambda smoke test polls a
bounded readiness window so cross-architecture emulation is not mistaken for a
failed service.

## Documentation decision

The authoritative backend commands live beside backend code in
`good-shepherd/agents/formidable/docs/deployment.md`. Formidable's deployment
doc covers Netlify and cross-repository release order and links to that runbook.
`docs/design/evals.md` distinguishes model/harness, UX-only, API-only and full
end-to-end benchmarks. `docs/chronology.md` defines what must be recorded for an
experiment or production acceptance.

## Gate status

At this checkpoint no AWS resource, ECR tag, task definition, secret or Netlify
site has been changed. Required local gates are shell syntax, backend unit
tests, byte comparison of the promoted pipeline with the accepted source,
self-contained High Docker build/import, PWA build/browser tests and Git/secret
hygiene. A production release, if later authorized, must use the explicit mode
and create a subsequent chronology entry with live digests, task revisions,
job IDs and browser screenshots.
