## The data challenge 

Output of the cloud apis 
```json
{
	Blocks: [
		{BlockType: WORD, Text: Cestrum, Geometry: {}, Conf: 95},
	]
}
```

1. Group words into cells (hopefully automatic) and rows
2. Distinguish headings vs data (skip headings in serialization) 
3. Identify doubt fields 

UI structure 

```
-------------------------------------------------
| [Form Image + Overlays]   | [Right Panel]    |
|                           | Field editor     |
|                           | Suggested fixes  |
-------------------------------------------------
```


## Structure and content 

* Define a known representation between python and js 
	- `rows.json`: logical structure (content) 
	- `boxes.json`: geometry for overlay 
* Preprocess the textract output to match `rows.json` and `boxes.json`

__Preprocessing__

```console
$ python preprocess.py \
  --input 002_cropped.json \
  --rows rows.json \
  --boxes boxes.json \
  --row-density 0.6 \
  --confidence-threshold 80
```

Algorithm: 

1. Load and flatten textract output 
	- Extract all `CELL` blocks 
	- aggregate text in `WORD` blocks of each `CELL`, where there are multiple
2. Detect header rows 
	- use `--row-density` to identify headers 
	- use `ColumnSpan` to group headers 
3. Header map
	- Range detect and combine `ColumnSpan` with subheaders (i.e. cells in next row)  
	- Fill forward empty cells, if missing due to merging
4. Build `rows.json` 
	- Everythign that's not a header row is a data row 
	- Create a row object for each of these `{header: value}`
5. Build `boxes.json`
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
