A list of challenges that humans intuitively understand but computers do not. Non comprehensive. 

## Sparse headers

Humans understand that something like BlockID (as described in form `002`) at the top of a bunch of columns, apply to all rows till it has been specified again. Eg

block id | plot id |... |
---------|---------|----|
1	 |	0  |    |
	 |	1  |	|
	 |	2  |	|

Indicates that within a block (id 1) there are 3 subplots. 
The computer on the other hand tends to "see" the first non zero number in a line, and associate that with the first column name (so it thinks blockID=1, plotID=1 is blockID=1 and plotID=NA).

The fix for this is to explicitly call out the hierarchy propogation logic for IDs. 
This is a special case of empty field policy. 

## Repitition at the plot level

In some cases, there is no repitiont at the subplot level. This is the case for the "canopy" readings, where the greyed out background color is to indicate "this value is only taken once for a plot, regardless of the number of subplots in it". Humans understand this, but the computer needs an explicit policy around how to deal with empty cells.

Whats worse, the model tends to treat stray pencil notes as valid when they fall within the greyed out blocks. 

## Special characters 

In code, special characters like ``` have special meaning. The most common case here is the `#`. In forms, it is common to use the `#` to mean "number". In code, depending on the language, it is used to markup text or include a library. So we must choose to map such symbols consistently, eg `#` should _always_ turn into `_no` or `_ID`.  

## Ordinality

Maintaining order is difficult. I can't just say "parse these rows in visual order" because the model doesn't "see" geometric rows. It sees text blobs. Even with a "top to bottom order" clause in the prompt, it sometimes jumps around or groups similar numbers/indices. 

We must rely on practical strategies to fix this.

```
(1) Detect / crop rows  →  (2) Run OCR  →  (3) Ask LLM to clean each row
```

## Reproducibility 

Reproducibility is a _huge_ problem. The model outputs different json for the same form on different runs. Each invocation requires careful tuning. With exactly once classification (based on fingerprints - which seems like a relatively reproducible operation) and one-shot extraction the results were somewhat manageable, but with more complex forms, like the soil moisture form, that needed multiple passes - even within the same form reproducibility proved impossible.  


## Alternatives 

* SAM:	Easy, universal	Not geometric; fails on plain tables
* OpenCV: Fast, Sensitive to lighting/skew
* Table Transformer/PaddleOCR-Structure: Designed for tables, Slightly heavier install - untested 
* docTR / LayoutParser: Good general layout engine, Need post-grouping logic - untested
* Cloud OCR (Google DocAI, Azure Form Recognizer): Best accuracy, API cost/privacy
