# Algorithmic alternatives for image -> layout -> content 

This document explains the two main alternatives for converting layout to boxes + content. 

Basically the problem is this: most cloud apis generate some sort of layout that doesn't embed meaning. It basically says: here is a line, here is a word. What we need is, here is some json with keys and values. The two alternatives presented below discuss this. 

## Top Down

1. Load and flatten textract output 
	- Extract all `CELL` blocks 
	- aggregate text in `WORD` blocks of each `CELL`, where there are multiple
	- This gives us a json with eg `(text, bbox, text_type, line_y_mid...)`
2. Classify words into horizontal rows (based on `line_y_mid`)
3. Detect header rows 
	- use `--row-density` to identify headers 
	- use `ColumnSpan` to group headers 
4. Header map
	- Range detect and combine `ColumnSpan` with subheaders (i.e. cells in next row)  
	- Fill forward empty cells, if missing due to merging
5. Build `rows.json` 
	- Everythign that's not a header row is a data row 
	- Create a row object for each of these `{header: value}`
6. Build `boxes.json`
	- For each "clickable" cell build an object like `{groupId, key, value, bbox, conf}`
	
__Header maps__


Textract sets `ColumnSpan` on merged cells. 

* Detect any header row cell with ColumnSpan > 1 (eg “Canopy Openness”).
* Record its column range, eg columns 5-8.
* Look in the next header row for cells with `ColumnIndex` within that range.
* Combine names, eg:
```
"Canopy Openness - North"
"Canopy Openness - East"
"Canopy Openness - West"
"Canopy Openness - South"
```
* For other header cells that don’t have subheaders, just use their own text (`Block Code`, `Transect #`, etc).


__Detecting headers vs non headers__

* Contains `Column Span`
* Avg confidence > 90: likely printed text, not handwriting
* Density: % of filled cells, typically higher for headers
* Alphabet ratio: alphabetic words vs numeric values, typically higher for headers


__Problems__

The main problem with this approach is that it forces us to second guess the layout structure returned from the cloud. We end up saying: we see a columnSpan, so it must be a "combined key" of some sort. But sometimes the cloud returns combined keys as just a line. And quickly doing this with rules gets very complicated. 

## Bottom up

The first two stages are the same as the top down approach. It only starts to differ when we classify the rows. Previously, we tried to classify the headers first, and assumed that everything that wasn't a header was data. Now, we will expliclity look at the `WORD` column `TextType` and classify based on whether it is `HANDWRITING`, `PRINTED` or `MIXED`. 

The reason this is called bottom up is because we start from the bottom in some ways, and group all "handwriting only" rows as data. Then focus on bucketing the remaining rows. 

1. Load and flatten textract output 
	- Extract all `CELL` blocks 
	- aggregate text in `WORD` blocks of each `CELL`, where there are multiple
	- This gives us a json with eg `(text, bbox, text_type, line_y_mid...)`
2. Classify words into horizontal rows (based on `line_y_mid`)
3. Classify each row as `HANDWRITING_ONLY`, `PRINTED_ONLY`, `MIXED`
4. Segment rows into logical zones: 
	- `data_rows`: contain handwritten data
	- `header_rows`: contain column headers 
	- `universal_fields`: are at the top of the form and apply to all rows of the form
	- `title_legend`: is the title or legends of the form
5. Build output JSON


