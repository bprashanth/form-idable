# dev__nvs_recce_plot__p0__v1

REAL blank template `nvs_recce_plot.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_recce_plot.pdf",
  "page": 0,
  "seed": 64039,
  "density": 0.8,
  "hard": true,
  "cells": 177,
  "printed_cells": 46,
  "filled": 93,
  "fallback_coltypes": [
    "person",
    "date",
    "person",
    "code1",
    "yn",
    "date",
    "code1",
    "int",
    "yn",
    "yn",
    "yn",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 46,
    "yn": 45,
    "date": 4,
    "dec": 5,
    "code1": 9,
    "person": 43,
    "short": 9,
    "species": 16
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
