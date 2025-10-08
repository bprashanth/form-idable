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
2. Detect "clusters" (words that belong to the same logical row even if its multi row)
3. Distinguish headings vs data (skip headings in serialization) 
4. Identify doubt fields 

UI structure 

```
-------------------------------------------------
| [Form Image + Overlays]   | [Right Panel]    |
|                           | Field editor     |
|                           | Suggested fixes  |
-------------------------------------------------
```




