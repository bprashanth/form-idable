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
  "cells": 67,
  "printed_cells": 46,
  "filled": 9,
  "fallback_coltypes": [
    "int",
    "date",
    "code1",
    "vernacular",
    "yn",
    "dec",
    "dec"
  ],
  "semantic_kind_counts": {
    "printed": 46,
    "date": 4,
    "percent": 8,
    "int": 1,
    "yn": 1,
    "code1": 6,
    "dec": 1
  },
  "writer_cohort": "hsf_1",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
