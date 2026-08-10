# test__rbp_stream_habitat_highgradient_wv__p2__v0

REAL blank template `rbp_stream_habitat_highgradient_wv.pdf` (page 3) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "rbp_stream_habitat_highgradient_wv.pdf",
  "page": 2,
  "seed": 11477,
  "density": 0.45,
  "hard": false,
  "cells": 52,
  "printed_cells": 41,
  "filled": 4,
  "fallback_coltypes": [
    "person",
    "date",
    "dec",
    "person",
    "code1",
    "vernacular",
    "dec"
  ],
  "semantic_kind_counts": {
    "printed": 41,
    "dec": 1,
    "percent": 10
  },
  "writer_cohort": "hsf_1",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
