# Exact-template experiment summary

## Runs

| tag | forms | macro F1 | micro F1 | correct | wrong | omitted | false fill | known cost | latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude_sonnet5_page_v1 | 1 | 0.9828 | 0.9828 | 57 | 1 | 0 | 0 | unknown | unknown |
| gemini35_page_v1 | 7 | 0.9706 | 0.9698 | 434 | 9 | 9 | 0 | $0.4335 | 156.4s |
| gemini36_bands_v1 | 6 | 0.9723 | 0.9778 | 352 | 7 | 0 | 2 | $0.5283 | 186.7s |
| gemini36_page_v1 | 7 | 0.9674 | 0.9676 | 433 | 10 | 9 | 0 | $0.3743 | 157.1s |

## Pairwise disagreement

### gemini36_page_v1 vs gemini36_bands_v1

Common forms: 6; cells including blanks: 800; disagreements: 15 (1.87%).

For `gemini36_page_v1`, disagreements capture 80.00% of errors. Its error rate is 53.33% inside disagreement and 0.25% in agreement.

Only A correct: 7; only B correct: 8; both wrong differently: 0.

### gemini36_page_v1 vs gemini35_page_v1

Common forms: 7; cells including blanks: 969; disagreements: 21 (2.17%).

For `gemini36_page_v1`, disagreements capture 73.68% of errors. Its error rate is 66.67% inside disagreement and 0.53% in agreement.

Only A correct: 7; only B correct: 8; both wrong differently: 6.

### gemini36_page_v1 vs claude_sonnet5_page_v1

Common forms: 1; cells including blanks: 120; disagreements: 3 (2.50%).

For `gemini36_page_v1`, disagreements capture 100.00% of errors. Its error rate is 100.00% inside disagreement and 0.00% in agreement.

Only A correct: 0; only B correct: 2; both wrong differently: 1.
