# Design: Case-insensitive Siblings and Similar Proposals

## Goals

1. **Case-insensitive siblings** — "Kage" and "kage" in the same Excel sheet are the
   same species value. They should be treated as one proposal with combined row
   highlighting, not two independent proposals.

2. **Similar proposals** — When multiple distinct original values (e.g. "Bootheham",
   "Boothern") resolve to the same corrected species, surface them as related so the
   user can confirm or reject the bulk correction in one step rather than reviewing
   each independently.

---

## 1. Case-insensitive siblings

### Problem

`extract_species_with_system_serials` uses the raw cell value as the unique key.
"Kage" and "kage" produce two separate proposals. Clicking "Kage" highlights only
rows containing "Kage"; the "kage" rows are invisible until the user clicks the
second card.

### Fix

Normalize to lowercase when building the deduplication key in
`extract_species_with_system_serials`. All case variants fold into one proposal
entry. The `original` field carries the first-seen casing (for display). When
`apply-species` runs, cell matching is also case-insensitive.

No UI change required — the existing primary/amber highlight layers handle the
combined `system_serials` correctly.

### Contract change

`apply_species_corrections` in `excel.py` changes from exact string match to
`cell_value.strip().lower() == original.lower()`. The correction value written to
the cell is still `corrected` (the expanded scientific name), not the cased variant.

---

## 2. Similar proposals

### Concept

After all proposals are generated, proposals that share the same `corrected` value
are "similar". A configurable threshold (`SIMILAR_SPECIES_THRESHOLD`, default 70%)
filters out low-confidence proposals from being listed as similar — if a proposal's
own match score is below the threshold it is not surfaced as a sibling even if its
`corrected` value happens to match.

### Server response shape

`check-species` returns each proposal extended with a `similar_proposals` list:

```json
{
  "original": "Bootheham",
  "corrected": "Symplocos cochinchinensis",
  "matched_display": "Boothakani",
  "match_field": "abbr",
  "score": 73.0,
  "system_serials": [3],
  "similar_proposals": [
    { "original": "Boothakani", "system_serials": [1, 5], "score": 100.0 },
    { "original": "Boothern",   "system_serials": [7],    "score": 85.0  }
  ]
}
```

`similar_proposals` contains other top-level proposals whose `corrected` value is
identical AND whose `score` is ≥ `SIMILAR_SPECIES_THRESHOLD`. A proposal never
lists itself. Proposals below threshold remain independent and are reviewed on their
own card.

`SIMILAR_SPECIES_THRESHOLD` lives in `agent/server/config.py` and can be overridden
by environment variable `SIMILAR_SPECIES_THRESHOLD` at deploy time.

### Three-color highlight overlay

| Color  | Meaning                                                   |
|--------|-----------------------------------------------------------|
| Red    | Primary — `system_serials[0]` of the active proposal      |
| Amber  | Secondary — `system_serials[1:]` of the active proposal   |
| Purple | Similar — all `system_serials` across `similar_proposals` |

`FormImageOverlay` gains a third prop `similarEntries: [{serial, bbox}]`. The same
consecutive-serial merge logic applies per color group independently.

### Proposal card display

```
#3  Bootheham → Boothakani (Symplocos cochinchinensis)  73%
    Related: Boothakani (#1 #5)  Boothern (#7)
    [edit]
```

The "Related" line is a subtle secondary line in a muted color. Row numbers are
shown so the user can cross-reference the paper form. Clicking the proposal card
highlights all three color groups on the image simultaneously.

### Two-step inline confirmation

After `doneEdit` (or when the auto-match is accepted), the confirmation UI replaces
the edit button with two sequential steps. Each step is resolved independently
before the next appears:

**Step 1 — exact matches:**
```
Apply to N rows with "Bootheham"?
[Update all]   [Just this row]
```
Same mechanic as the existing single-step confirmation, now explicitly labelled
"exact matches".

**Step 2 — similar matches (only shown if similar_proposals is non-empty):**
```
Apply same correction to 3 similar rows?
Boothakani (#1 #5)  Boothern (#7)
[Apply to similar]   [Skip]
```
- **Apply to similar** — folds all `similar_proposals` into this correction.
  Their `system_serials` are appended to this proposal's correction entry in the
  batch sent to `apply-species`. The folded proposal cards are marked as reviewed
  (green border) with a label "Resolved via Bootheham" and are no longer editable.
- **Skip** — similar proposals remain independent. When the user reaches their
  cards, they see their own match suggestion. If their suggestion is the same
  corrected value, the card already shows "100%" and needs only a confirm click.

### State machine per proposal card

```
initial
  └─ (user clicks done, value unchanged)   → reviewed
  └─ (user edits, clicks done)
       └─ looking_up
            └─ (RPC returns, system_serials.length == 1, no similar)  → reviewed
            └─ (RPC returns, system_serials.length > 1, no similar)   → pending_exact
            └─ (RPC returns, has similar_proposals)                   → pending_exact
                 └─ (Update all / Just this row chosen)
                      └─ (no similar_proposals)     → reviewed
                      └─ (has similar_proposals)    → pending_similar
                           └─ (Apply to similar)    → reviewed  (siblings → resolved)
                           └─ (Skip)                → reviewed  (siblings stay independent)
```

### apply-species contract

No new endpoint. The corrections array sent to `apply-species` includes all
system_serials explicitly (both from exact and folded similar proposals), so the
server applies corrections by row ID as before:

```json
[
  {
    "original": "Bootheham",
    "corrected": "Symplocos cochinchinensis",
    "system_serials": [3, 1, 5, 7]
  }
]
```

The server does not need to know about "exact" vs "similar" — that distinction is
only UX. One correction entry, one pass over the workbook.

Note: because `apply_species_corrections` matches case-insensitively (change #1
above), folding "Boothakani" rows into the "Bootheham" correction works even though
the cell values differ.

### What this design explicitly excludes

- No threshold UI in the PWA (threshold is a server-side deploy-time config).
- No multi-level similarity (similar-of-similar is not surfaced).
- No partial folding (Apply to similar is all-or-nothing per proposal group).
- No changes to the `lookup-species` RPC — it returns a single best match;
  similarity grouping happens only in `check-species` over the full proposal set.
