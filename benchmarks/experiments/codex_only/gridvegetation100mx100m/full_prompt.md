You are transcribing a scanned handwritten ecological field datasheet
(Western Ghats forest plot surveys) into a spreadsheet.

You have been given `input.pdf` in the current directory. Your goal is
to produce `output.xlsx` containing one sheet named `v2`.

**You have a sandbox with PyMuPDF (fitz), Pillow, numpy, openpyxl, and a
shell. There is NO pre-processed Textract output — work directly from
the PDF.**

## The quality bar: structurally complete AND as accurate as you can make it

Every table, heading, metadata field, and grid visible on the page must
**show up** in `v2` — that's the non-negotiable part. Beyond that, you
have a generous turn budget: use it to verify and correct cell values,
read handwritten marks/ticks, and fill in any gaps you find. A human
reviewer will do a final pass, but the more you get right here, the less
they have to fix.

## Using `/workspace/render_page.py` to render and crop

```
python3 /workspace/render_page.py input.pdf --out crop.png --bbox x0,y0,x1,y1 --zoom Z --page N
```

- `--bbox x0,y0,x1,y1` is **fractions (0.0-1.0)** of the page width/height.
- `--zoom` is capped at source native resolution and ~1568px on longest edge.
- Start with a full-page overview (`--zoom 2`, no `--bbox`) to understand
  the layout, then crop/zoom into specific regions to read cell values.
- This PDF has multiple pages — check all of them.

## Building v2

1. Render each page at a low zoom first to understand the structure.
2. Crop into tables, header blocks, and any marginal annotations to read
   their content.
3. The form may contain repeated form-sheets stacked on one page or across
   pages — keep each form's data clearly separated in `v2`.

## Respect notation conventions

- a **dot/period** in a cell means the recorded value is literally `0`
- a **continuous line drawn through a cell** means "no entry" — leave blank
- **tally marks** (`I`, `l`, `1`, `|` repeated) are a count — sum to an integer
- **checkbox marks** (`✓`, `X`, `x`, ticks) mean "present/yes" — transcribe
  as `X`; an empty/unchecked box means absent — leave blank

## Flag uncertainty

For any cell where you're not confident even after cropping, apply yellow fill
(`PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")`).

## Output

Write `output.xlsx` (sheet `v2`) to `/workspace` using openpyxl. When done,
briefly summarize what you transcribed and which cells you flagged.

---

Transcribe input.pdf into output.xlsx as described above. Begin by rendering
an overview of page 1, then proceed page by page.
