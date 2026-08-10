# test__nvs_stem_diameter_sapling__p1__v1

REAL blank template `nvs_stem_diameter_sapling.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_stem_diameter_sapling.pdf",
  "page": 1,
  "seed": 26532,
  "density": 0.45,
  "hard": true,
  "cells": 252,
  "printed_cells": 3,
  "filled": 99,
  "fallback_coltypes": [
    "code1",
    "vernacular",
    "date",
    "date",
    "int",
    "species"
  ],
  "semantic_kind_counts": {
    "printed": 3,
    "vernacular": 42,
    "int": 83,
    "species": 42,
    "code1": 41,
    "date": 41
  },
  "writer_cohort": "hsf_6",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
