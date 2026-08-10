# test__nvs_foliar_browse_index_datasheets__p0__v0

REAL blank template `nvs_foliar_browse_index_datasheets.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_foliar_browse_index_datasheets.pdf",
  "page": 0,
  "seed": 2483,
  "density": 0.45,
  "hard": false,
  "cells": 47,
  "printed_cells": 11,
  "filled": 16,
  "fallback_coltypes": [
    "int",
    "yn",
    "int",
    "yn",
    "int",
    "yn",
    "date",
    "date",
    "int",
    "date",
    "yn",
    "yn",
    "date",
    "code1",
    "int",
    "int",
    "yn",
    "yn",
    "yn",
    "yn",
    "int",
    "int",
    "yn",
    "yn",
    "date",
    "code1",
    "code1",
    "date",
    "yn",
    "date",
    "code1",
    "code1",
    "code1"
  ],
  "semantic_kind_counts": {
    "printed": 11,
    "yn": 1,
    "int": 7,
    "code1": 28
  },
  "writer_cohort": "hsf_1",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
