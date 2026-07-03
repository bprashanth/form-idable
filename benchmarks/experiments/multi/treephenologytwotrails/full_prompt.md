You are transcribing a scanned handwritten ecological field datasheet
(Western Ghats forest plot surveys — tree plots, ground cover, leaf
litter biomass, regeneration counts, bird checklists, etc.) into a
spreadsheet.

You have been given `input.pdf` in the current directory. If it's a
PDF, you're working with page 1 (1-indexed) of it. If it's a single
image (PNG/JPG — e.g. a camera-phone photo), treat it as the only page
(ignore the page number). Your goal is to produce `output.xlsx`
containing one sheet named `v2`.

**You have a sandbox with PyMuPDF (fitz), Pillow, numpy, openpyxl, and a
shell.**

## The quality bar: structurally complete AND as accurate as you can make it

Every table, heading, metadata field, and grid visible on the page must
**show up** in `v2` — that's the non-negotiable part. Beyond that, you
have a generous turn budget: use it to verify and correct cell values,
read handwritten marks/ticks, and fill in any gaps you find. A human
reviewer will do a final pass, but the more you get right here, the less
they have to fix.

## Your inputs

`v1.json` (Textract's structured read of the page) and `v1_overview.png`
(a rendered overview of the page) are in the current directory. `v1.json`
has three keys:

- `tables`: tables Textract recognized as having a grid/ruled structure.
  Each is `{bbox, n_rows, n_cols, cells}`; each cell is
  `{r, c, text, conf, bbox, header?, rowspan?, colspan?}` (`conf` is
  Textract's confidence 0-100; `bbox` is `[x, y, width, height]` as
  fractions of the page).
- `key_values`: form fields Textract paired as label/value, each
  `{key, value, key_conf, value_conf, bbox}`.
- `other_text`: every other line of text Textract read on the page —
  `{text, conf, bbox}`. Textract puts a line here whenever it couldn't
  attribute it to a table or field. **This is where missed structure
  shows up**: section headings, a second grid of labels that has no
  ruled lines (so Textract didn't recognize it as a table), metadata
  fields Textract didn't pair into `key_values`, etc.

## Building v2

1. Use `v1.tables` and `v1.key_values` as your starting point/backbone for
   `v2` — but feel free to crop/zoom and correct any cell that looks
   wrong, low-confidence, or semantically off (e.g. a date that doesn't
   parse, a species name that's garbled, a number outside its column's
   range).

2. Look at `other_text` and `v1_overview.png` for any table/grid/section
   that has **no representation at all** in `v1.tables`/`key_values` (a
   common case on these forms: a second grid of category/level labels
   that Textract didn't recognize as a table because it has no ruled
   lines, e.g. a ground-cover abundance grid). Reconstruct it as a new
   table/section in `v2` — crop/zoom into that region as needed to read
   row/column headers AND the cell contents (marks, ticks, numbers).

3. If you added any section in step 2, write `v2_meta.json`:
   `{"new_sections": [{"sheet": "v2", "rows": [first_row, last_row], "bbox": [x0, y0, x1, y1]}]}`
   — one entry per new section, `rows` are 1-indexed row numbers in `v2`
   and `bbox` is the page region (fractions) it came from. Omit the file
   entirely if everything in `v2` traces back to a `v1` table/key_value.

## Using `/workspace/render_page.py` to crop and zoom

```
python3 /workspace/render_page.py input.pdf --out crop.png --bbox x0,y0,x1,y1 --zoom Z --page 1
```

- `--bbox x0,y0,x1,y1` is **fractions (0.0-1.0)** of the page width/height
  — the same convention as the bboxes in `v1.json`.
- `--zoom` is automatically capped at the source's native resolution (no
  fake upscaling) and at ~1568px on the output's longest edge — ask for
  more than you think you need, it won't over-render.
- Crop into specific regions (a table, a grid, a row, a header field) and
  read the resulting image. Iterate as needed — render a wider view first,
  then narrower crops of anything you're unsure about.

## Respect notation conventions

- a **dot/period** in a cell means the recorded value is literally `0`
- a **continuous line drawn through a cell** means "no entry" — leave
  the cell blank, don't transcribe it as a value
- **tally marks** (`I`, `l`, `1`, `|` repeated) are a count — sum them
  to an integer (separate from the dot/line rules above)

## Flag uncertainty

For any cell where you're not confident in the reading even after trying
multiple views, apply a yellow fill
(`PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")`)
so a human reviewer's eye goes there first. It's fine to be uncertain —
it's not fine to guess silently.

## Output

Write `output.xlsx` (containing the `v2` sheet) to the current working
directory using openpyxl, plus `v2_meta.json` if you added any v1-less
sections (see above). When you're done, briefly summarize in text what
you transcribed, what (if anything) you added beyond `v1`, and which
cells you flagged as uncertain.

---

Transcribe page 1 of input.pdf into output.xlsx as described above. v1.json (Textract's structured read of this page) and v1_overview.png (a rendered overview) are already present in /workspace (run `ls` to confirm). Begin now.
