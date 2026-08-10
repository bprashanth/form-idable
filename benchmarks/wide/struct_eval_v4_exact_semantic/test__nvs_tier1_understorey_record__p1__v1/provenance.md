# test__nvs_tier1_understorey_record__p1__v1

REAL blank template `nvs_tier1_understorey_record.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_understorey_record.pdf",
  "page": 1,
  "seed": 31425,
  "density": 0.45,
  "hard": true,
  "cells": 571,
  "printed_cells": 13,
  "filled": 213,
  "fallback_coltypes": [
    "int",
    "int",
    "code1",
    "code1",
    "date",
    "code1",
    "int",
    "code1",
    "int",
    "int",
    "int",
    "yn",
    "code1",
    "yn",
    "code1",
    "yn",
    "yn",
    "yn",
    "code1",
    "int",
    "yn",
    "yn",
    "yn",
    "date",
    "int",
    "code1",
    "date",
    "yn",
    "yn",
    "date",
    "int",
    "yn",
    "code1",
    "code1",
    "yn",
    "int",
    "yn",
    "int",
    "int",
    "code1",
    "code1",
    "code1",
    "code1",
    "date",
    "code1",
    "yn",
    "date",
    "yn",
    "code1"
  ],
  "semantic_kind_counts": {
    "printed": 13,
    "time": 3,
    "code1": 371,
    "yn": 64,
    "species": 120
  },
  "writer_cohort": "hsf_1",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
