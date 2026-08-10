# test__nvs_tier1_metadata_record__p1__v0

REAL blank template `nvs_tier1_metadata_record.pdf` (page 2) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_tier1_metadata_record.pdf",
  "page": 1,
  "seed": 29651,
  "density": 0.45,
  "hard": false,
  "cells": 52,
  "printed_cells": 20,
  "filled": 14,
  "fallback_coltypes": [
    "int",
    "vernacular",
    "code1",
    "date",
    "yn",
    "int",
    "yn",
    "yn",
    "dec",
    "date",
    "date",
    "int",
    "code1",
    "yn",
    "int",
    "yn",
    "int",
    "code1",
    "code1",
    "int",
    "code1",
    "date",
    "code1",
    "int",
    "int",
    "date",
    "code1",
    "int",
    "vernacular",
    "date"
  ],
  "semantic_kind_counts": {
    "printed": 20,
    "int": 7,
    "code1": 25
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
