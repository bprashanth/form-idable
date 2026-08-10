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
  "cells": 565,
  "printed_cells": 11,
  "filled": 224,
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
    "yn",
    "yn",
    "code1",
    "date",
    "yn",
    "yn",
    "yn",
    "int",
    "yn",
    "int",
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
    "printed": 11,
    "int": 62,
    "code1": 310,
    "yn": 123,
    "species": 59
  },
  "writer_cohort": "hsf_1",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
