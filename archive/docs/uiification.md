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

see [docs/ppalgorithms](./ppalgorithms.md) for a description of alternatives. 

