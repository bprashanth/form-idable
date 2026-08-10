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
  "cells": 191,
  "printed_cells": 21,
  "filled": 72,
  "fallback_coltypes": [
    "int",
    "yn",
    "yn",
    "int",
    "yn",
    "int",
    "yn",
    "date",
    "date",
    "yn",
    "date",
    "yn",
    "code1",
    "person",
    "yn",
    "yn",
    "int",
    "yn",
    "int",
    "code1",
    "yn",
    "int",
    "int",
    "code1",
    "yn",
    "yn",
    "code1",
    "int",
    "date",
    "code1",
    "vernacular",
    "yn",
    "code1"
  ],
  "semantic_kind_counts": {
    "printed": 21,
    "int": 108,
    "short": 8,
    "species": 7,
    "code1": 14,
    "yn": 20,
    "percent": 13
  },
  "writer_cohort": "hsf_1",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
