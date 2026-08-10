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
  "cells": 273,
  "printed_cells": 11,
  "filled": 180,
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
    "yn",
    "code1",
    "int",
    "short",
    "species"
  ],
  "semantic_kind_counts": {
    "printed": 11,
    "short": 30,
    "int": 119,
    "species": 25,
    "dec": 50,
    "code1": 4,
    "yn": 34
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
