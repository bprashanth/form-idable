# test__nvs_tier1_metadata_record__p1__v1

REAL blank template `nvs_tier1_metadata_record.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_metadata_record.pdf",
  "page": 1,
  "seed": 88021,
  "density": 0.6,
  "hard": true,
  "cells": 19,
  "printed_cells": 13,
  "filled": 3,
  "fallback_coltypes": [
    "int",
    "yn",
    "yn",
    "date",
    "int",
    "yn",
    "int",
    "code1",
    "yn",
    "yn",
    "yn",
    "code1",
    "yn",
    "int",
    "date",
    "yn",
    "date",
    "date",
    "yn",
    "yn",
    "code1",
    "date",
    "yn",
    "yn",
    "int",
    "code1",
    "date",
    "code1",
    "date",
    "dec"
  ],
  "semantic_kind_counts": {
    "printed": 13,
    "code1": 3,
    "yn": 3
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
