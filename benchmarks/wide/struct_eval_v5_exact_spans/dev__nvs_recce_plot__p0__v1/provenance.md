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
  "cells": 147,
  "printed_cells": 66,
  "filled": 12,
  "fallback_coltypes": [
    "person",
    "date",
    "person",
    "yn",
    "yn",
    "date",
    "code1",
    "short",
    "yn",
    "yn",
    "yn",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 66,
    "int": 4,
    "dec": 5,
    "coordinate": 2,
    "percent": 19,
    "yn": 17,
    "short": 9,
    "species": 20,
    "person": 5
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
