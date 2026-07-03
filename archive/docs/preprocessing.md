# Preprocessing Layers

Three layers of processing, each building on the previous. The PWA server starts at Layer 0+1 and selectively adds Layer 2 functions as needed.

## Layer 0: Vanilla Textract

What AWS Textract returns directly from `analyze_document` with `FeatureTypes=["TABLES", "FORMS", "LAYOUT"]`.

| Block type | What it gives us | Relevant fields |
|---|---|---|
| `TABLE` | Table detection | EntityTypes: `STRUCTURED_TABLE` or `SEMI_STRUCTURED_TABLE` |
| `CELL` | Individual table cells | RowIndex, ColumnIndex, RowSpan, ColumnSpan, Confidence |
| `CELL` with EntityTypes `["COLUMN_HEADER"]` | Header cells (Textract marks these automatically) | Same as CELL + the entity type flag |
| `MERGED_CELL` | Cells spanning multiple columns/rows | ColumnSpan, RowSpan, child CELL Ids |
| `WORD` | OCR text | Text, Confidence, TextType (`PRINTED` or `HANDWRITING`) |
| `KEY_VALUE_SET` | Form fields outside table (e.g. "Date: 19/02/2025") | EntityTypes: `["KEY"]` or `["VALUE"]`, linked via Relationships |
| `LINE` | Text lines | Text, Confidence |
| `LAYOUT_TABLE` | Layout-level table region | BoundingBox |
| `LAYOUT_TEXT` | Layout-level text region | BoundingBox |

**Key insight:** `COLUMN_HEADER` is confirmed present in our existing Textract output (11 files, 29+ occurrences). This means Textract already distinguishes header cells from data cells for structured tables.

## Layer 1: textractor library

The `amazon-textract-textractor` library (v1.9.2) parses the raw Textract response into structured Python objects.

**Table parsing:**
```python
from textractor.data.constants import CellTypes

# Parse response
document = textractor.Document(textract_response)

# Get tables
for table in document.tables:
    # Column headers (uses COLUMN_HEADER entity type)
    headers = table.column_headers  # Dict[str, List[TableCell]]
    # Or: table.get_cells_by_type(CellTypes.COLUMN_HEADER)

    # All cells
    for cell in table.table_cells:
        cell.is_column_header  # bool
        cell.text              # str
        cell.confidence        # float
        cell.row_index         # int
        cell.col_index         # int

    # Strip headers to get just data
    table.strip_headers()
```

**Key-value pairs (form fields):**
```python
for kv in document.key_values:
    kv.key.text    # "Date:"
    kv.value.text  # "19/02/2025"
    kv.confidence  # float
```

**What Layer 1 gives us:**
- Column headers identified and extracted
- Data rows with cell-level confidence
- Key-value form fields (universal fields)
- Table type classification

**What Layer 1 does NOT give us:**
- Distinguishing which key-value pairs are "universal" (apply to all rows) vs incidental
- MIXED-row parsing (printed key + handwritten value in same table row)
- Hierarchical header flattening (multi-row headers → single-level snake_case keys)
- Row type classification (DATA vs HEADER vs UNIVERSAL vs TITLE_LEGEND)

## Universal fields

### What they are

Universal fields are key-value metadata that apply to **every row** in a table. On paper forms, they typically appear above the table as labels with handwritten values:

```
Transect #: 1          Area Name: BKM
Date: 19/02/2025       Plot #: 2
Names of research team: AK, HA, KK, MK, PK

┌──────┬────────────┬───────┬──────────┬──────────────┐
│      │ S.No       │ SPP   │ Habit    │ DBH in cms   │  ← column headers
├──────┼────────────┼───────┼──────────┼──────────────┤
│      │ 1          │ Corbu │ T        │ 23           │  ← data rows
│      │ 2          │ age   │ L        │ 4.2          │
└──────┴────────────┴───────┴──────────┴──────────────┘
```

Their semantic meaning: when this table is flattened into a dataset, every row should carry `Transect #=1`, `Area Name=BKM`, `Date=19/02/2025`, etc. They are not columns — they are row-level constants.

### How to distinguish them from column headers in Textract output

| | Column headers | Universal fields |
|---|---|---|
| **Textract block type** | `CELL` (inside a `TABLE`) | `KEY_VALUE_SET` (outside the table) |
| **EntityTypes** | `["COLUMN_HEADER"]` | `["KEY"]` or `["VALUE"]` |
| **Position** | Inside the table grid (RowIndex 1, typically) | Above the table (lower Y-coordinate than table top) |
| **textractor API** | `table.column_headers` | `document.key_values` |
| **Meaning** | Define the columns of the table | Define metadata shared by all rows |

They are entirely different Textract block types. Column headers are CELL blocks inside a TABLE. Universal fields are KEY_VALUE_SET blocks that are separate from the table.

### Two sources of universal fields

Verified against actual output (`cloud/output/000_layout.json` → `cloud/results/form_001_classified.json`):

**Source 1: KEY_VALUE_SET blocks (Layer 0/1)**
Textract detects these natively. Available via `document.key_values`.

| Key | Value | Key confidence |
|---|---|---|
| Area Name | BKM | 99.3 |
| Date | 19/02/2025 | 91.8 |
| Plot # | 2 | 94.4 |
| Names of research team | AK,HA kk, MK, PK | 97.9 |
| Transect # | 1 | 95.3 |

Also returns some junk entries (confidence < 70) that should be filtered.

**Source 2: MIXED rows inside the table (Layer 2 only)**
Some forms embed key-value pairs inside the table grid as rows with printed labels + handwritten values. Textract treats these as regular CELL rows, not KEY_VALUE_SET. The preprocessor's `assign_row_types()` + `extract_universal_fields()` detects them by finding rows where PRINTED and HANDWRITING text coexist, separated by `:` or `-`.

| Key | Value | Detection method |
|---|---|---|
| block_name | 1 | MIXED-row parsing |
| name_of_researcher | Caropy Cover | MIXED-row parsing |
| sub_plot_no | 1 | MIXED-row parsing |
| notes | 12 | MIXED-row parsing |
| seedlings | Subplor: | MIXED-row parsing |

These 5 fields are **not** available from Layer 0/1 — they require Layer 2's `extract_universal_fields()`.

### How universal fields are represented in Excel

**Current (Phase 2):** Recorded naturally, as they appear on the paper form. Key-value pairs above the data table:

```
┌─────────────────────┬──────────────────────┬───┐
│ Transect #          │ 1                    │   │  ← universal fields
│ Area Name           │ BKM                  │   │     (rows above table)
│ Date                │ 19/02/2025           │   │
│ Plot #              │ 2                    │   │
│ Names of research…  │ AK, HA, KK, MK, PK  │   │
├─────────────────────┼──────────────────────┼───┤
│ (empty row)         │                      │   │
├─────────────────────┼──────────────────────┼───┤
│ S.No                │ SPP Name             │ … │  ← column headers (bold, gray)
├─────────────────────┼──────────────────────┼───┤
│ 1                   │ Corbu                │ … │  ← data rows
│ 2                   │ age                  │ … │
└─────────────────────┴──────────────────────┴───┘
```

Confidence coloring applies to universal field values too (same red/orange rules as data cells).

**Future (dataset flattening):** When exporting a final flat dataset, universal field values are replicated as extra columns on every row:

```
┌──────────┬───────────┬──────┬─────┬────────┬───┐
│Transect #│ Area Name │ Date │S.No │SPP Name│ … │
├──────────┼───────────┼──────┼─────┼────────┼───┤
│ 1        │ BKM       │19/02 │ 1   │ Corbu  │ … │
│ 1        │ BKM       │19/02 │ 2   │ age    │ … │
└──────────┴───────────┴──────┴─────┴────────┴───┘
```

This flattening is not done in Phase 2 — it's a future step. The Excel output preserves the natural form layout so reviewers can compare against the paper original.

## Layer 2: Custom preprocessors (`cloud/preprocessor.py`)

Each function below addresses a specific gap. They are independent and can be invoked selectively based on form characteristics.

### Invocation order

The current `HandwrittenTableForm.classify_rows()` (line 113) invokes them in this order:

```
1. extract_rows_from_cells()     → raw rows from CELL blocks
2. assign_row_types()            → classify each row as DATA/HEADER/UNIVERSAL/TITLE_LEGEND
3. extract_universal_fields()    → parse UNIVERSAL rows for key:value pairs
4. extract_key_value_sets_above_table() → parse KEY_VALUE_SET blocks above table
5. build_header_map_from_cells() → hierarchical header map from MERGED_CELL + header rows
6. create_structured_output()    → package everything into IMF JSON with system metadata
```

### Function reference

#### `extract_rows_from_cells()` (line 1055)
- **Input**: Raw Textract JSON
- **Output**: List of row dicts, each with `words` (text, TextType, confidence, bbox), `row_index`, `cells`
- **What it does**: Groups CELL blocks by RowIndex. For each cell, follows CHILD relationships to get WORD blocks. Attaches column indices and bounding boxes.
- **When needed**: Always (this is the base row extraction)

#### `assign_row_types()` (line 1156)
- **Input**: Rows from `extract_rows_from_cells()`
- **Output**: Mutates rows in-place, adding `row_type` and `basic_type` fields
- **What it does**: Bottom-up state machine. Classifies each row's words as PRINTED_ONLY, HANDWRITING_ONLY, MIXED, or EMPTY. Then walks rows from bottom to top:
  - Starts in DATA state (expects HANDWRITING)
  - Transitions to HEADER when hitting PRINTED_ONLY rows
  - Transitions to UNIVERSAL when hitting MIXED rows with `:` or `-` separators
  - Transitions to TITLE_LEGEND for remaining PRINTED rows above UNIVERSAL
- **When needed**: When COLUMN_HEADER entity type is absent (no native header detection from Textract). Also needed to identify UNIVERSAL rows (which Layer 0/1 cannot do).
- **Limitation**: Fails when all text is HANDWRITING (all rows become DATA)

#### `extract_universal_fields()` (line 191)
- **Input**: Rows (with row_type assigned)
- **Output**: Dict of `{snake_case_key: value_string}`
- **What it does**: Filters rows with `row_type == "UNIVERSAL"`. For each, splits cell text on `:` or `-` separator. Left part = key, right part = value. Converts key to snake_case.
- **When needed**: When form has MIXED rows (printed key + handwritten value) that are NOT detected as KEY_VALUE_SET blocks by Textract. This is common for forms where key-value pairs are inside the table grid rather than floating above it.
- **Depends on**: `assign_row_types()` must run first

#### `extract_key_value_sets_above_table()` (line 315)
- **Input**: Raw Textract JSON + rows (to determine table top boundary)
- **Output**: Dict of `{snake_case_key: value_string}`
- **What it does**: Finds KEY_VALUE_SET blocks whose Y-coordinate is above the table's top edge. Follows KEY→VALUE relationships to extract text. Converts to snake_case.
- **When needed**: Always useful — these are the "obvious" universal fields that Textract detects natively. Layer 1's key-value extraction gets the same data, so this function is mostly redundant with Layer 1. The position filtering (above table only) is the added value.
- **Depends on**: `extract_rows_from_cells()` (to know where the table starts)

#### `build_header_map_from_cells()` (line 398)
- **Input**: Raw Textract JSON + rows (with row_type assigned)
- **Output**: Dict mapping `{snake_case_header: [column_indices]}`
- **What it does**: Finds rows with `row_type == "HEADER"`. For each header cell, extracts text and maps to column indices. Handles MERGED_CELL blocks by building parent-child header hierarchies (e.g. "Canopy Openness" spanning columns 5-6, with children "North" col 5 and "South" col 6 → flattened to `canopy_openness_north`, `canopy_openness_south`).
- **When needed**: Complex forms with multi-row merged headers. Simple forms with single-row headers don't need this — Layer 1's `Table.column_headers` suffices.
- **Depends on**: `assign_row_types()` must run first (to know which rows are HEADER)

#### `create_structured_output()` (line 590)
- **Input**: Raw Textract JSON + rows + universal_fields + header_map
- **Output**: IMF JSON (the intermediate format with `universal_fields`, `header_map`, `rows` sections, each with `system` metadata including group_ids, bboxes, confidence)
- **What it does**: Packages everything into the intermediate format documented in [imf.md](imf.md). Adds system metadata: group_ids for UI grouping, aggregated bounding boxes, per-cell confidence, column/row indices.
- **When needed**: When the downstream consumer expects IMF format (e.g. form-viewer). The PWA doesn't use IMF — it goes straight to Excel.

#### `to_snake_case()` (line 75)
- **Input**: Human-readable field name string
- **Output**: snake_case string (e.g. "Transect #:" → "transect_no")
- **When needed**: Normalization. Maps `#` → `_no`, removes special chars, lowercases.

## Form attribute → preprocessor mapping (future)

Different forms have different characteristics. Rather than running all preprocessors on every form, we can detect form attributes and invoke only the relevant functions.

| Form attribute | How to detect | Preprocessors to invoke |
|---|---|---|
| Has COLUMN_HEADER cells | Check CELL EntityTypes | None — Layer 1 handles it |
| No COLUMN_HEADER cells, has PRINTED→HANDWRITING transition | Check TextType distribution across rows | `assign_row_types()` → `build_header_map_from_cells()` |
| All HANDWRITING or all PRINTED, no COLUMN_HEADER | Check TextType uniformity | First row = header (simple heuristic, no preprocessor) |
| Has MIXED rows (printed key + handwritten value in table) | Check for rows with both TextTypes | `assign_row_types()` → `extract_universal_fields()` |
| Has KEY_VALUE_SET blocks above table | Check KEY_VALUE_SET block positions | `extract_key_value_sets_above_table()` (or just use Layer 1 key-value parsing) |
| Has MERGED_CELL / multi-row headers | Check for MERGED_CELL blocks or ColumnSpan > 1 | `build_header_map_from_cells()` |
| Needs IMF format output | When feeding form-viewer | `create_structured_output()` |

### Future registry pattern

```python
# Conceptual — not implemented yet
PREPROCESSOR_REGISTRY = {
    "has_mixed_rows": [assign_row_types, extract_universal_fields],
    "no_column_headers": [assign_row_types, build_header_map_from_cells],
    "has_merged_headers": [build_header_map_from_cells],
    "needs_imf": [create_structured_output],
}

def preprocess(textract_response, form_attributes):
    """Run textractor first (Layer 1), then selectively apply Layer 2."""
    document = textractor.Document(textract_response)
    result = extract_with_textractor(document)  # Layer 1

    for attr in form_attributes:
        for fn in PREPROCESSOR_REGISTRY.get(attr, []):
            result = fn(result)  # Layer 2 post-processing

    return result
```

The attribute detection itself can be automatic (inspect the Textract response for MIXED rows, missing COLUMN_HEADER, etc.) or manual (user selects form type).
