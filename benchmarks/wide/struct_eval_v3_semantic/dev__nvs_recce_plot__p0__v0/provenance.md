# dev__nvs_recce_plot__p0__v0

REAL blank template `nvs_recce_plot.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_recce_plot.pdf",
  "page": 0,
  "seed": 47728,
  "density": 0.45,
  "hard": false,
  "cells": 143,
  "printed_cells": 62,
  "filled": 5,
  "fallback_coltypes": [
    "species",
    "vernacular",
    "int",
    "date",
    "yn",
    "yn",
    "int",
    "int",
    "int",
    "int",
    "int",
    "int"
  ],
  "semantic_kind_counts": {
    "printed": 62,
    "int": 16,
    "dec": 5,
    "coordinate": 2,
    "percent": 19,
    "yn": 5,
    "short": 9,
    "species": 25
  },
  "writer_cohort": "hsf_7",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
