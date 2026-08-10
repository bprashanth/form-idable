# dev__nrcs_pedon_soil_description__p0__v1

REAL blank template `nrcs_pedon_soil_description.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "nrcs_pedon_soil_description.pdf",
  "page": 0,
  "seed": 47155,
  "density": 0.8,
  "hard": true,
  "cells": 9,
  "printed_cells": 7,
  "filled": 0,
  "fallback_coltypes": [
    "yn",
    "yn",
    "yn",
    "code1",
    "code1",
    "yn",
    "int",
    "code1",
    "code1",
    "date",
    "code1",
    "yn",
    "code1",
    "code1",
    "yn",
    "yn",
    "yn"
  ],
  "semantic_kind_counts": {
    "printed": 7,
    "int": 2
  },
  "writer_cohort": "hsf_3",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
