# Textract specific details on layout 

## Figuring out rows via CELL Blocks

* CELL blocks have built-in row information: Each CELL has RowIndex and ColumnIndex properties that Textract automatically detects from the table structure.
* Reliable row grouping: Instead of clustering by Y-coordinates, we group CELL blocks by their RowIndex
* Extract words from each cell: For each row, get all the WORD blocks that belong to the CELLs in that row through the CHILD relationships.
* Sort words within each row: Words are sorted by X-coordinate (left-to-right) within each row.

An added advantage of using CELL blocks is they're auto-limited to within the printed table. There are no CELL blocks generated for text outside the table. 


## Understanding non CELL universal keys 

* There are some boxes outside the table which aren't classified as CELLs by textract. Examples are the `KEY_VALUE_PAIR` fields. These are the universal keys. 
* `KEY` blocks: Have CHILD relationships with key words (like "Area", "Name:") and VALUE relationships pointing to value blocks
* `VALUE` blocks: Have CHILD relationships with value words (like "BKM", "1", "2")


## Understanding MERGED cells

* We ignore `MERGED_CELLS` in all but the header rows (i.e. rows with mostly print that come after the handwriting rows from the bottom) 
* `MERGED_CELL` blocks that have ColumnSpan > 1 are given special consideration 
* Note the cells below the column indices of the `ColumnSpan` of the `MERGED_CELL` and combine them using `snake_case` 
* Ignore `CELL` blocks that coincide with `MERGED_CELL` blocks in the same row to avoid double counting headers 

