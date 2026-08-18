# Chronology experiment and release log

`chronology/` is the shared decision history for the Formidable PWA and the
Good Shepherd backend. Runtime code stays in its owning repository; the
chronology records why a candidate was accepted or rejected across both.

## When to add an entry

Add the next zero-padded Markdown file for any experiment or release that
changes a conclusion: a new baseline, failed control, model/harness result,
pipeline decision, deployment, rollback or production visual finding. Small
implementation commits that do not change evidence can share the surrounding
entry.

Use an informative name such as:

```text
020_backend_ownership_and_release_modes.md
021_targeted_reader_diversity_gate.md
```

Never rewrite an earlier failure to make the sequence cleaner. Add a later
entry explaining the correction so future work does not repeat the mistake.

## Required contents

Each experiment entry should state:

1. question and predeclared success/failure rule;
2. frozen control and both repository commits;
3. fixtures, models, reasoning settings, prompts and commands;
4. content, layout, blank/duplication and review-capture results;
5. durable price and actual provider bill when model calls were used;
6. visual inspection performed and screenshot/artifact paths;
7. failures, confounders and what was not tested;
8. decision: reject, continue locally, or candidate for production.

A production entry must additionally record job IDs, Lambda image digest, Low
and High image digests/task revisions, PWA commit/asset when relevant, rollback
status, both route-verification results and the production screenshot paths.

## Evidence lifecycle

Keep raw model responses, PDFs containing partner data, generated workbooks,
screenshots and large run directories local/S3 and gitignored. Commit the
reproducible harness, small synthetic fixtures where licensing permits, summary
tables and chronology. Never commit API keys, Cognito credentials, Codex auth or
presigned URLs.

The benchmark procedure and local-to-production gates are in
`docs/design/evals.md`. Backend release commands are authoritative in
`../good-shepherd/agents/formidable/docs/deployment.md`.
