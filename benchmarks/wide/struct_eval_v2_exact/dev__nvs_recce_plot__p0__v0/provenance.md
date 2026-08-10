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
  "cells": 177,
  "printed_cells": 46,
  "filled": 52,
  "fallback_coltypes": [
    "int",
    "vernacular",
    "int",
    "yn",
    "yn",
    "yn",
    "int",
    "int",
    "int",
    "int",
    "int",
    "code1"
  ],
  "semantic_kind_counts": {
    "printed": 46,
    "code1": 20,
    "vernacular": 4,
    "dec": 5,
    "yn": 18,
    "int": 59,
    "short": 9,
    "species": 16
  },
  "writer_cohort": "hsf_7",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
