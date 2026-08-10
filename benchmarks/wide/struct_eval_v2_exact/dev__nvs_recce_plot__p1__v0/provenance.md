# dev__nvs_recce_plot__p1__v0

REAL blank template `nvs_recce_plot.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_recce_plot.pdf",
  "page": 1,
  "seed": 8683,
  "density": 0.8,
  "hard": false,
  "cells": 273,
  "printed_cells": 15,
  "filled": 180,
  "fallback_coltypes": [
    "int",
    "date",
    "int",
    "int",
    "person",
    "dec",
    "vernacular"
  ],
  "semantic_kind_counts": {
    "printed": 15,
    "int": 109,
    "date": 37,
    "person": 37,
    "dec": 37,
    "vernacular": 37,
    "percent": 1
  },
  "writer_cohort": "hsf_6",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
