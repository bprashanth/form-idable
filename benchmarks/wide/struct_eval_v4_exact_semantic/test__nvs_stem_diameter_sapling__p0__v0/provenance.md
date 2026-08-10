# test__nvs_stem_diameter_sapling__p0__v0

REAL blank template `nvs_stem_diameter_sapling.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_stem_diameter_sapling.pdf",
  "page": 0,
  "seed": 28174,
  "density": 0.25,
  "hard": false,
  "cells": 240,
  "printed_cells": 3,
  "filled": 52,
  "fallback_coltypes": [
    "int",
    "dec",
    "yn",
    "code1",
    "code1",
    "species"
  ],
  "semantic_kind_counts": {
    "printed": 3,
    "int": 130,
    "percent": 80,
    "code1": 27
  },
  "writer_cohort": "hsf_7",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
