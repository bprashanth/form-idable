# Subscription reader gates and the additive-primary decision

## Why this experiment existed

The first high image used two Gemini readers through OpenRouter and passed the
14-PDF local gate (aggregate semantic F1 0.923 high versus 0.887 low). It could
not remain a production dependency because both direct Gemini and OpenRouter
subsequently returned hard depleted-credit errors. The frozen low task/image
was never changed.

This sequence tested whether authenticated CLI subscriptions could replace the
unavailable API readers. Frozen goldens and the low workbooks stayed unchanged.
No candidate in this document was deployed.

## Codex Terra/Luna results

The generic pipeline gained a deterministic horizontal-rule oracle, preserved
physically present blank rows, and replaced fixed quadrants with
structure-declared high-resolution crops. Tall tables were also tested as
12-row bands with one-row overlap and a repeated printed header.

| Candidate | Fixture | Semantic F1 | Frozen low | Decision |
| --- | --- | ---: | ---: | --- |
| Terra primary + Luna peer, focused crops | eval09 | 0.862 | 0.947 | reject |
| Terra primary + Luna peer, banded crops | eval09 | 0.875 | 0.947 | reject |
| Agentic Sol primary + Luna peer | eval03 | 0.797 | 0.856 | reject |

Banding recovered 0.013 on eval09 but remained materially below low. The
Codex-only replacement was therefore stopped before an all-form sweep.

## Claude Sonnet results

Claude Code 2.1.226 can read local images with only the `Read` tool and return
strict `--json-schema` output. Replacing its default coding-agent system prompt
reduced a tiny probe from about 40k cache-creation tokens / $0.27 to about 7k /
$0.05. Full form pages were still expensive and slow.

Page-level, content-consensus headline results on eval09:

| Page | Claude Sonnet | Frozen low | Claude latency | Reported cost |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0.975 | 0.969 | 276 s | $0.55 |
| 2 | 0.965 | 0.986 | 505 s | $0.99 |
| 3, first prompt | 0.849 | 0.924 | 193 s | $0.41 |
| 3, typed/coverage prompt | 0.906 | 0.924 | 214 s | $0.44 |

Visual inspection found that page 3's open-top handwritten `4` looked like
`H`. A generic correction—honour the declared integer type, consult only a
legend printed on the same page, and explicitly include the final recorded
row—raised row-keyed table-cell F1 from 0.849-equivalent failure to 0.9955,
slightly above low's 0.9909 on that table. Page 2 remained genuinely worse:
row-keyed table F1 0.8511 versus low 0.9573.

Splitting page 2 into isolated bands did not rescue the model. The easy first
band scored 0.9808 while low was perfect at 1.0000. A later hard band scored
0.6163 while low scored 0.9725. Claude was rejected rather than hidden behind
the good first-page result.

## Provider availability

- Direct Gemini returns HTTP 429 `RESOURCE_EXHAUSTED`: prepayment credits are
  depleted.
- OpenRouter returns HTTP 402: insufficient credits.
- OpenAI API billing has no available credit.
- Codex subscription auth works for Luna, Terra, and Sol.
- Claude CLI OAuth works, but Sonnet failed the accuracy/latency gate above.

## The safer high architecture

The experiments show that replacing low's content with a weaker available
reader is unsafe. The next candidate therefore keeps the frozen low Codex
workbook as the immutable primary and uses independent structured readers only
as an attention oracle.

On saved eval09 artifacts, comparing low with Terra alone produced 848 red
flags across 2,725 golden table cells. It captured 76.1% of low errors, but only
27.4% of red cells were actual low errors (2.44x enrichment): too much human
fatigue.

Requiring Terra and Luna to agree with each other while disagreeing with low
reduced this to 103 red cells. Of those, 69.0% were actual low errors, a 6.16x
enrichment over the 11.2% base error rate. This smaller set captured 23.3% of
all low errors. The peer consensus was exactly correct in 19 cases; in another
52 cases low and peer consensus were both wrong in different ways, which still
makes the disagreement useful for human review. It must not auto-correct.

This is three executions (low primary plus two peer readers), not a disguised
two-model vote. Its value is review precision and non-regression: the uploaded
workbook retains low's content, red flags select the high-yield peer-consensus
disagreements, and orange ecology remains suggestion-only. The next gate is a
generic XLSX-to-page-geometry bridge followed by all-form benchmarking.
