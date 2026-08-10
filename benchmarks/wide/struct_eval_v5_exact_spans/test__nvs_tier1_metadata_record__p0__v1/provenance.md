# test__nvs_tier1_metadata_record__p0__v1

REAL blank template `nvs_tier1_metadata_record.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_metadata_record.pdf",
  "page": 0,
  "seed": 13612,
  "density": 0.8,
  "hard": true,
  "cells": 70,
  "printed_cells": 31,
  "filled": 29,
  "fallback_coltypes": [
    "person",
    "vernacular",
    "date",
    "date",
    "date",
    "int",
    "code1",
    "date",
    "int",
    "date",
    "dec",
    "int",
    "int",
    "yn",
    "int",
    "code1",
    "code1",
    "code1",
    "int",
    "date",
    "code1",
    "yn",
    "yn",
    "code1",
    "yn",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 31,
    "time": 7,
    "int": 24,
    "short": 3,
    "dec": 2,
    "yn": 3
  },
  "writer_cohort": "hsf_0",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
