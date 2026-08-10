# test__nvs_tier1_stem_diameter_height_sapling__p1__v0

REAL blank template `nvs_tier1_stem_diameter_height_sapling.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_stem_diameter_height_sapling.pdf",
  "page": 1,
  "seed": 17956,
  "density": 0.45,
  "hard": false,
  "cells": 213,
  "printed_cells": 3,
  "filled": 86,
  "fallback_coltypes": [
    "int",
    "yn",
    "date",
    "int",
    "code1",
    "code1",
    "int",
    "code1",
    "date",
    "date",
    "code1",
    "yn",
    "code1",
    "int",
    "code1",
    "yn",
    "code1",
    "int",
    "code1",
    "int",
    "int",
    "date",
    "yn",
    "code1",
    "code1",
    "yn",
    "code1",
    "code1",
    "date",
    "int",
    "dec"
  ],
  "semantic_kind_counts": {
    "printed": 3,
    "short": 30,
    "int": 76,
    "species": 20,
    "dec": 40,
    "code1": 30,
    "yn": 14
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
