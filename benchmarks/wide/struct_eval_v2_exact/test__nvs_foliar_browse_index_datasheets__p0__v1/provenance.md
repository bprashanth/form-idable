# test__nvs_foliar_browse_index_datasheets__p0__v1

REAL blank template `nvs_foliar_browse_index_datasheets.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nvs_foliar_browse_index_datasheets.pdf",
  "page": 0,
  "seed": 79135,
  "density": 0.8,
  "hard": true,
  "cells": 47,
  "printed_cells": 11,
  "filled": 26,
  "fallback_coltypes": [
    "date",
    "date",
    "code1",
    "code1",
    "int",
    "yn",
    "code1",
    "yn",
    "yn",
    "date",
    "int",
    "code1",
    "date",
    "yn",
    "code1",
    "yn",
    "yn",
    "code1",
    "int",
    "int",
    "code1",
    "yn",
    "date",
    "yn",
    "date",
    "yn",
    "yn",
    "code1",
    "int",
    "code1",
    "yn",
    "code1",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 11,
    "code1": 8,
    "int": 7,
    "yn": 21
  },
  "writer_cohort": "hsf_7",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
