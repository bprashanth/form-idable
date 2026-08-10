# test__nvs_tier1_understorey_record__p0__v1

REAL blank template `nvs_tier1_understorey_record.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_understorey_record.pdf",
  "page": 0,
  "seed": 21470,
  "density": 0.8,
  "hard": true,
  "cells": 585,
  "printed_cells": 11,
  "filled": 408,
  "fallback_coltypes": [
    "date",
    "date",
    "yn",
    "yn",
    "date",
    "date",
    "yn",
    "code1",
    "yn",
    "date",
    "code1",
    "code1",
    "int",
    "date",
    "int",
    "int",
    "code1",
    "int",
    "date",
    "yn",
    "date",
    "int",
    "int",
    "yn",
    "yn",
    "code1",
    "code1",
    "date",
    "yn",
    "date",
    "code1",
    "code1",
    "code1",
    "yn",
    "int",
    "yn",
    "code1",
    "yn",
    "date",
    "yn",
    "date",
    "code1",
    "yn",
    "date",
    "date",
    "code1",
    "date",
    "yn",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 11,
    "code1": 318,
    "yn": 193,
    "species": 63
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
