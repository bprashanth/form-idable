# dev__nvs_understorey_subplot__p0__v0

REAL blank template `nvs_understorey_subplot.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_understorey_subplot.pdf",
  "page": 0,
  "seed": 15269,
  "density": 0.6,
  "hard": false,
  "cells": 588,
  "printed_cells": 12,
  "filled": 300,
  "fallback_coltypes": [
    "code1",
    "date",
    "code1",
    "yn",
    "code1",
    "yn",
    "code1",
    "int",
    "yn",
    "person",
    "code1",
    "yn",
    "yn",
    "yn",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 12,
    "date": 42,
    "person": 42,
    "code1": 205,
    "yn": 287
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
