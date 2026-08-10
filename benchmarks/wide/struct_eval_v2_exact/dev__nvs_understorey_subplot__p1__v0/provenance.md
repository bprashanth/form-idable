# dev__nvs_understorey_subplot__p1__v0

REAL blank template `nvs_understorey_subplot.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_understorey_subplot.pdf",
  "page": 1,
  "seed": 93549,
  "density": 0.45,
  "hard": false,
  "cells": 616,
  "printed_cells": 12,
  "filled": 249,
  "fallback_coltypes": [
    "int",
    "vernacular",
    "code1",
    "yn",
    "yn",
    "yn",
    "yn",
    "date",
    "code1",
    "int",
    "yn",
    "yn",
    "yn",
    "yn",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 12,
    "vernacular": 44,
    "int": 87,
    "code1": 86,
    "yn": 387
  },
  "writer_cohort": "hsf_1",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
