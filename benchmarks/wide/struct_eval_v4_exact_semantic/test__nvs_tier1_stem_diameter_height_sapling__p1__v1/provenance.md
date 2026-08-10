# test__nvs_tier1_stem_diameter_height_sapling__p1__v1

REAL blank template `nvs_tier1_stem_diameter_height_sapling.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_stem_diameter_height_sapling.pdf",
  "page": 1,
  "seed": 86555,
  "density": 0.8,
  "hard": true,
  "cells": 213,
  "printed_cells": 3,
  "filled": 145,
  "fallback_coltypes": [
    "int",
    "yn",
    "int",
    "yn",
    "code1",
    "yn",
    "yn",
    "date",
    "code1",
    "yn",
    "date",
    "yn",
    "code1",
    "int",
    "yn",
    "code1",
    "code1",
    "int",
    "yn",
    "code1",
    "code1",
    "date",
    "int",
    "int",
    "yn",
    "int",
    "yn",
    "int",
    "code1",
    "int",
    "short"
  ],
  "semantic_kind_counts": {
    "printed": 3,
    "short": 30,
    "int": 89,
    "species": 20,
    "dec": 40,
    "code1": 3,
    "yn": 28
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
