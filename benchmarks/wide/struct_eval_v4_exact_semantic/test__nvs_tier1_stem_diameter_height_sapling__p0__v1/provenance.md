# test__nvs_tier1_stem_diameter_height_sapling__p0__v1

REAL blank template `nvs_tier1_stem_diameter_height_sapling.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_stem_diameter_height_sapling.pdf",
  "page": 0,
  "seed": 17776,
  "density": 0.8,
  "hard": true,
  "cells": 249,
  "printed_cells": 3,
  "filled": 176,
  "fallback_coltypes": [
    "int",
    "code1",
    "code1",
    "date",
    "date",
    "code1",
    "code1",
    "date",
    "date",
    "date",
    "date",
    "int",
    "yn",
    "code1",
    "int",
    "yn",
    "date",
    "yn",
    "code1",
    "yn",
    "code1",
    "code1",
    "code1",
    "code1",
    "date",
    "yn",
    "yn",
    "code1",
    "yn",
    "int",
    "int",
    "vernacular"
  ],
  "semantic_kind_counts": {
    "printed": 3,
    "int": 92,
    "species": 24,
    "dec": 48,
    "short": 30,
    "code1": 5,
    "yn": 32,
    "date": 15
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
