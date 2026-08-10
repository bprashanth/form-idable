# dev__nvs_recce_plot__p1__v1

REAL blank template `nvs_recce_plot.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_recce_plot.pdf",
  "page": 1,
  "seed": 73108,
  "density": 0.25,
  "hard": true,
  "cells": 273,
  "printed_cells": 15,
  "filled": 58,
  "fallback_coltypes": [
    "date",
    "person",
    "vernacular",
    "person",
    "dec",
    "dec",
    "person"
  ],
  "semantic_kind_counts": {
    "printed": 15,
    "date": 35,
    "person": 111,
    "vernacular": 37,
    "dec": 74,
    "percent": 1
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
