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
  "cells": 13,
  "printed_cells": 12,
  "filled": 0,
  "fallback_coltypes": [
    "code1",
    "date",
    "code1",
    "vernacular",
    "date",
    "int",
    "yn",
    "code1",
    "date",
    "date",
    "int",
    "int",
    "code1",
    "date",
    "yn",
    "int",
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
    "printed": 12,
    "person": 1
  },
  "writer_cohort": "hsf_7",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
