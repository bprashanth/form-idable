# test__nvs_stem_diameter_sapling__p1__v0

REAL blank template `nvs_stem_diameter_sapling.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_stem_diameter_sapling.pdf",
  "page": 1,
  "seed": 47649,
  "density": 0.45,
  "hard": false,
  "cells": 252,
  "printed_cells": 3,
  "filled": 97,
  "fallback_coltypes": [
    "int",
    "vernacular",
    "date",
    "int",
    "int",
    "short"
  ],
  "semantic_kind_counts": {
    "printed": 3,
    "int": 165,
    "percent": 84
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
