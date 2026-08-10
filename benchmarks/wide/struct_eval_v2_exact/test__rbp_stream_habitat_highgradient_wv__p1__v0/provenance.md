# test__rbp_stream_habitat_highgradient_wv__p1__v0

REAL blank template `rbp_stream_habitat_highgradient_wv.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "rbp_stream_habitat_highgradient_wv.pdf",
  "page": 1,
  "seed": 15652,
  "density": 0.25,
  "hard": false,
  "cells": 31,
  "printed_cells": 23,
  "filled": 1,
  "fallback_coltypes": [
    "person",
    "vernacular",
    "int",
    "person"
  ],
  "semantic_kind_counts": {
    "printed": 23,
    "vernacular": 3,
    "person": 5
  },
  "writer_cohort": "hsf_6",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
