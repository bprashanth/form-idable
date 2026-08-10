# dev__nvs_recce_forest_height_tiers__p0__v1

REAL blank template `nvs_recce_forest_height_tiers.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_recce_forest_height_tiers.pdf",
  "page": 0,
  "seed": 22228,
  "density": 0.6,
  "hard": true,
  "cells": 140,
  "printed_cells": 37,
  "filled": 56,
  "fallback_coltypes": [
    "person",
    "yn",
    "yn",
    "date",
    "code1",
    "date",
    "int",
    "int",
    "date",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 37,
    "yn": 40,
    "code1": 8,
    "person": 17,
    "short": 11,
    "species": 18,
    "int": 9
  },
  "writer_cohort": "hsf_6",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
