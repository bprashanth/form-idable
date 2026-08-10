# test__nvs_tier1_metadata_record__p0__v0

REAL blank template `nvs_tier1_metadata_record.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_metadata_record.pdf",
  "page": 0,
  "seed": 63620,
  "density": 0.45,
  "hard": false,
  "cells": 70,
  "printed_cells": 31,
  "filled": 16,
  "fallback_coltypes": [
    "person",
    "int",
    "date",
    "code1",
    "date",
    "int",
    "yn",
    "code1",
    "date",
    "person",
    "int",
    "int",
    "code1",
    "date",
    "yn",
    "yn",
    "code1",
    "int",
    "date",
    "person",
    "yn",
    "yn",
    "yn",
    "date",
    "code1",
    "code1"
  ],
  "semantic_kind_counts": {
    "printed": 31,
    "time": 7,
    "int": 24,
    "short": 3,
    "dec": 2,
    "code1": 2,
    "yn": 1
  },
  "writer_cohort": "hsf_7",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
