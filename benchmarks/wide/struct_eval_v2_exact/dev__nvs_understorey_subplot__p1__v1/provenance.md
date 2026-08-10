# dev__nvs_understorey_subplot__p1__v1

REAL blank template `nvs_understorey_subplot.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_understorey_subplot.pdf",
  "page": 1,
  "seed": 15602,
  "density": 0.8,
  "hard": true,
  "cells": 616,
  "printed_cells": 12,
  "filled": 434,
  "fallback_coltypes": [
    "int",
    "int",
    "yn",
    "yn",
    "yn",
    "code1",
    "yn",
    "date",
    "code1",
    "vernacular",
    "code1",
    "yn",
    "yn",
    "code1",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 12,
    "int": 87,
    "vernacular": 44,
    "yn": 301,
    "code1": 172
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
