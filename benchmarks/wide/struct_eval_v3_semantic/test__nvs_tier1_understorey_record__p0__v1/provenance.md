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
  "cells": 591,
  "printed_cells": 13,
  "filled": 397,
  "fallback_coltypes": [
    "date",
    "date",
    "code1",
    "yn",
    "date",
    "date",
    "yn",
    "code1",
    "yn",
    "date",
    "code1",
    "code1",
    "yn",
    "date",
    "int",
    "yn",
    "code1",
    "int",
    "yn",
    "yn",
    "date",
    "yn",
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
    "printed": 13,
    "time": 3,
    "yn": 69,
    "code1": 380,
    "species": 126
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
