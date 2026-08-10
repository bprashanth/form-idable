# test__rbp_stream_habitat_highgradient_wv__p2__v1

REAL blank template `rbp_stream_habitat_highgradient_wv.pdf` (page 3) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "rbp_stream_habitat_highgradient_wv.pdf",
  "page": 2,
  "seed": 32241,
  "density": 0.25,
  "hard": true,
  "cells": 43,
  "printed_cells": 35,
  "filled": 2,
  "fallback_coltypes": [
    "person",
    "dec",
    "vernacular",
    "dec",
    "species",
    "person",
    "vernacular"
  ],
  "semantic_kind_counts": {
    "printed": 35,
    "dec": 1,
    "percent": 7
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
