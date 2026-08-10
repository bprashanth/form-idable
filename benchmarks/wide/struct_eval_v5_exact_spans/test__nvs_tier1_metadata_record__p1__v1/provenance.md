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
  "cells": 52,
  "printed_cells": 20,
  "filled": 18,
  "fallback_coltypes": [
    "int",
    "dec",
    "yn",
    "date",
    "int",
    "yn",
    "int",
    "yn",
    "person",
    "yn",
    "yn",
    "code1",
    "date",
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
    "person",
    "dec"
  ],
  "semantic_kind_counts": {
    "printed": 20,
    "int": 7,
    "code1": 25
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
