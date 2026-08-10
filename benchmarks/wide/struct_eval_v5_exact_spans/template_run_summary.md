# Exact-template experiment summary

## Runs

| tag | forms | macro F1 | micro F1 | correct | wrong | omitted | false fill | known cost | latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude_sonnet5_page_v2 | 2 | 0.8776 | 0.8776 | 43 | 4 | 2 | 2 | unknown | unknown |
| cursor_gpt54mini_page_v1 | 2 | 0.0527 | 0.0870 | 1 | 2 | 17 | 0 | unknown | unknown |
| gemini35_page_v1 | 5 | 0.9652 | 0.9671 | 353 | 8 | 8 | 0 | $0.3848 | 141.2s |
| gemini36_bands_v1 | 4 | 0.9796 | 0.9799 | 292 | 5 | 0 | 2 | $0.4545 | 158.1s |
| gemini36_page_v1 | 5 | 0.9629 | 0.9644 | 352 | 9 | 8 | 0 | $0.3366 | 140.1s |

## Pairwise disagreement

### gemini36_page_v1 vs gemini36_bands_v1

Common forms: 4; cells including blanks: 708; disagreements: 13 (1.84%).

For `gemini36_page_v1`, disagreements capture 87.50% of errors. Its error rate is 53.85% inside disagreement and 0.14% in agreement.

Only A correct: 6; only B correct: 7; both wrong differently: 0.

### gemini36_page_v1 vs gemini35_page_v1

Common forms: 5; cells including blanks: 877; disagreements: 18 (2.05%).

For `gemini36_page_v1`, disagreements capture 70.59% of errors. Its error rate is 66.67% inside disagreement and 0.58% in agreement.

Only A correct: 6; only B correct: 7; both wrong differently: 5.
