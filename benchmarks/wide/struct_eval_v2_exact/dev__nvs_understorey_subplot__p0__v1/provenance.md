# dev__nvs_understorey_subplot__p0__v1

REAL blank template `nvs_understorey_subplot.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_understorey_subplot.pdf",
  "page": 0,
  "seed": 76601,
  "density": 0.45,
  "hard": true,
  "cells": 588,
  "printed_cells": 12,
  "filled": 235,
  "fallback_coltypes": [
    "yn",
    "vernacular",
    "yn",
    "yn",
    "yn",
    "code1",
    "yn",
    "int",
    "code1",
    "date",
    "yn",
    "yn",
    "code1",
    "yn",
    "code1"
  ],
  "semantic_kind_counts": {
    "printed": 12,
    "vernacular": 42,
    "date": 42,
    "yn": 328,
    "code1": 164
  },
  "writer_cohort": "hsf_7",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
