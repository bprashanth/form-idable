# dev__agrra_coral_underwater_datasheet__p0__v1

REAL blank template `agrra_coral_underwater_datasheet.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "agrra_coral_underwater_datasheet.pdf",
  "page": 0,
  "seed": 81914,
  "density": 0.45,
  "hard": true,
  "cells": 513,
  "printed_cells": 20,
  "filled": 202,
  "fallback_coltypes": [
    "int",
    "int",
    "date",
    "int",
    "yn",
    "int",
    "yn",
    "code1",
    "code1",
    "int",
    "int",
    "dec"
  ],
  "semantic_kind_counts": {
    "printed": 20,
    "int": 246,
    "code1": 122,
    "time": 43,
    "date": 42,
    "yn": 40
  },
  "writer_cohort": "hsf_6",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
