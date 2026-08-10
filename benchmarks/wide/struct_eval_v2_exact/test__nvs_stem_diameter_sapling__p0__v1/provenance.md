# test__nvs_stem_diameter_sapling__p0__v1

REAL blank template `nvs_stem_diameter_sapling.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_stem_diameter_sapling.pdf",
  "page": 0,
  "seed": 89680,
  "density": 0.6,
  "hard": true,
  "cells": 240,
  "printed_cells": 3,
  "filled": 130,
  "fallback_coltypes": [
    "code1",
    "vernacular",
    "date",
    "int",
    "yn",
    "species"
  ],
  "semantic_kind_counts": {
    "printed": 3,
    "vernacular": 40,
    "yn": 40,
    "species": 40,
    "code1": 39,
    "int": 78
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
