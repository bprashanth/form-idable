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
  "cells": 192,
  "printed_cells": 22,
  "filled": 123,
  "fallback_coltypes": [
    "int",
    "code1",
    "date",
    "date",
    "code1",
    "code1",
    "int",
    "yn",
    "code1",
    "code1",
    "yn",
    "date",
    "yn",
    "vernacular",
    "code1",
    "yn",
    "int",
    "code1",
    "yn",
    "code1",
    "code1",
    "int",
    "int",
    "code1",
    "yn",
    "yn",
    "yn",
    "person",
    "date",
    "code1",
    "int",
    "yn",
    "code1"
  ],
  "semantic_kind_counts": {
    "printed": 22,
    "int": 108,
    "short": 8,
    "species": 7,
    "code1": 27,
    "yn": 7,
    "percent": 13
  },
  "writer_cohort": "hsf_7",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
