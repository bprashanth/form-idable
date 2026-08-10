# test__bird_grassland_point_count__p0__v1

REAL blank template `bird_grassland_point_count.pdf` (page 1) filled with synthetic handwriting.
Structure and printed labels read directly from the PDF's vector text/line data — exact, no CV thresholds.
Golden is exact by construction: printed labels from the file + the values written here.

```json
{
  "template": "bird_grassland_point_count.pdf",
  "page": 0,
  "seed": 43507,
  "density": 0.6,
  "hard": true,
  "cells": 169,
  "printed_cells": 8,
  "filled": 83,
  "fallback_coltypes": [
    "vernacular",
    "code1",
    "code1",
    "date",
    "date",
    "person",
    "code1",
    "species"
  ],
  "semantic_kind_counts": {
    "printed": 8,
    "code1": 61,
    "vernacular": 20,
    "date": 40,
    "person": 20,
    "species": 20
  },
  "writer_cohort": "hsf_4",
  "ground_truth": "ground_truth.json",
  "layout_golden": "layout_golden.xlsx"
}
```
