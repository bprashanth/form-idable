
# Intermediate format

Core schema
```
{
  "universal_fields": { ... },
  "header_map": { ... },
  "rows": [ ... ]
}
```
1. Universal Fields Schema
Purpose: Fields that apply to all data rows (e.g., "Area Name: BKM", "Date: 19/02/2025")
```
"universal_fields": {
  "area_name": {
    "value": "BKM",
    "description": "",
    "alt_names": [],
    "merged": false,
    "system": {
      "group_id": "universal_field_1",
      "valid": true,
      "column_index": -1,  // Universal fields don't have specific columns
      "row_index": -1       // Universal fields don't have specific rows
    }
  }
}
```
Key Features:
* valid: Boolean flag for user toggling (if false, won't copy to all rows)
* `column_index`: -1, `row_index`: -1: Indicates these apply globally
* `group_id`: Unique identifier for UI grouping


2. Header Map Schema
Purpose: Column definitions with explicit Textract column indices

```
"header_map": {
  "sub_plot_no": {
    "field_name": "Sub plot no.",
    "system": {
      "merged": false,
      "group_id": "col_2",
      "column_index": 2,    // Actual Textract ColumnIndex
      "row_index": -1       // Headers don't have specific rows
    },
    "description": "Field: Sub plot no.",
    "alt_names": []
  },
  "canopy_openness_north": {
    "field_name": "Canopy Openness North",
    "system": {
      "merged": true,       // Indicates hierarchical header
      "group_id": "col_5",
      "column_index": 5,    // Actual Textract ColumnIndex
      "row_index": -1
    },
    "description": "Canopy openness measurement in the north direction",
    "alt_names": []
  }
}
```

Key Features:
* `column_index`: Actual Textract ColumnIndex (handles "ghost" columns/gaps)
* `merged: true:` Indicates hierarchical headers (e.g., "Canopy Openness" + "North")
* `group_id`: UI grouping identifier

3. Rows Schema
Purpose: Data rows with explicit Textract row/column indices

```
"rows": [
  {
    "sub_plot_no": "1",
    "s_no": "1.",
    "spp_name_local_name": "cadelei",
    "habit": "T",
    "system": {
      "bbox": { "Left": 0.065, "Top": 0.227, "Width": 0.748, "Height": 0.012 },
      "group_id": "row_2",
      "row_index": 2,       // Actual Textract RowIndex
      "column_index": -1,   // Rows don't have specific columns
      "cells": {
        "row_2_col_2": {
          "bbox": { "Left": 0.105, "Top": 0.227, "Width": 0.112, "Height": 0.012 },
          "confidence": 45.78,
          "text": "1",
          "header": "sub_plot_no",
          "row_index": 2,   // Actual Textract RowIndex
          "column_index": 2 // Actual Textract ColumnIndex
        }
      }
    }
  }
]
```
Key Features:
* `row_index`: Actual Textract RowIndex for precise row identification
* `cells`: Individual cell data with explicit `row_index` and `column_index`
* `header`: Maps to `header_map` key for column definition
* `confidence`: Textract confidence score for validation


