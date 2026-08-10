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
  "cells": 13,
  "printed_cells": 12,
  "filled": 0,
  "fallback_coltypes": [
    "int",
    "date",
    "date",
    "person",
    "int",
    "code1",
    "yn",
    "int",
    "int",
    "yn",
    "vernacular",
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
    "printed": 12,
    "date": 1
  },
  "writer_cohort": "hsf_0",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
