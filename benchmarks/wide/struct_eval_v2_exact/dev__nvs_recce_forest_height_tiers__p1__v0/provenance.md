# dev__nvs_recce_forest_height_tiers__p1__v0

REAL blank template `nvs_recce_forest_height_tiers.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_recce_forest_height_tiers.pdf",
  "page": 1,
  "seed": 17319,
  "density": 0.25,
  "hard": false,
  "cells": 273,
  "printed_cells": 15,
  "filled": 61,
  "fallback_coltypes": [
    "date",
    "int",
    "dec",
    "dec",
    "person",
    "dec",
    "int"
  ],
  "semantic_kind_counts": {
    "printed": 15,
    "date": 35,
    "int": 74,
    "dec": 111,
    "person": 37,
    "percent": 1
  },
  "writer_cohort": "hsf_6",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
