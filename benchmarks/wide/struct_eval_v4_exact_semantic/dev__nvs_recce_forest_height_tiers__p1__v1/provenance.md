# dev__nvs_recce_forest_height_tiers__p1__v1

REAL blank template `nvs_recce_forest_height_tiers.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_recce_forest_height_tiers.pdf",
  "page": 1,
  "seed": 30508,
  "density": 0.8,
  "hard": true,
  "cells": 273,
  "printed_cells": 15,
  "filled": 171,
  "fallback_coltypes": [
    "int",
    "date",
    "vernacular",
    "dec",
    "date",
    "date",
    "dec"
  ],
  "semantic_kind_counts": {
    "printed": 15,
    "code1": 257,
    "percent": 1
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
