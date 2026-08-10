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
  "cells": 143,
  "printed_cells": 62,
  "filled": 9,
  "fallback_coltypes": [
    "person",
    "int",
    "yn",
    "date",
    "code1",
    "dec",
    "date",
    "int",
    "int",
    "date"
  ],
  "semantic_kind_counts": {
    "printed": 62,
    "coordinate": 3,
    "percent": 16,
    "yn": 4,
    "code1": 4,
    "dec": 2,
    "short": 11,
    "species": 27,
    "date": 9,
    "person": 5
  },
  "writer_cohort": "hsf_6",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
