# Golden-building spec — ecology field datasheets (FROZEN EVAL SET)

You are building the reference transcription (`golden.xlsx`) for ONE scanned
field-survey form. These goldens are the scoring reference for a model
benchmark, so they must be **as close to perfect as a careful human can get**.
Do not rush. A wrong golden silently corrupts every score computed against it.

## Inputs in your form dir

- `pages/page_N.png` — full-page overviews (read these directly).
- `tiles/page_N_hK.png` — top/bottom halves at higher detail.
- `outputs/*.txt` / `outputs/*.xlsx` — INDEPENDENT transcriptions by 2-3
  converter models (gemini-3.6-flash, qwen3-vl-32b, sometimes codex CLI).
  Treat these as *hypotheses*, never as truth. They disagree; you adjudicate.
- Crop tool for zooming into any region:
  ```
  python3 ~/src/github.com/bprashanth/good-shepherd/agents/formidable/tools/render_page.py \
      <form_dir>/input.pdf --out /tmp/crop.png --page N --bbox x0,y0,x1,y1 --zoom 6
  ```
  `--bbox` is FRACTIONS (0-1) of page width/height. Crop aggressively — a
  10-row block of a table at zoom 6 is far more readable than the full page.

## Method (follow in order)

1. Read every page overview to understand the form's structure.
2. Read each converter's output for that page side by side.
3. Build the golden row by row. Where converters **agree** and the value is
   plausible given the image, accept it (spot-check ~20% of agreements
   against crops anyway — agreement on a misread is common for similar
   models).
4. Where converters **disagree**, or where a value looks implausible
   (impossible measurement, wrong column count, species name that isn't a
   real taxon), you MUST crop into that cell at high zoom and decide yourself.
   Record every such adjudication in `GOLDEN_NOTES.md`.
5. Verify structural integrity: row counts, ID sequences (note deliberate
   gaps — these forms often skip numbers), column alignment, and that no
   table block was dropped by all converters (check the image for tables
   nobody transcribed).

## What the golden must contain

Everything a careful human would transcribe from the page:

- Form title and any sub-title.
- Every header/metadata field as `label,value` (date, site/trail/grid ID,
  location, observers, weather, start time, treatment, etc.).
- Every table: the printed header row, then every data row.
- **Both printed and handwritten values** where a cell contains both (these
  forms often have a pre-printed prior measurement plus a new handwritten
  one — keep both, in reading order).
- Codes legends, footnote legends (`* = w/o cover`), and marginal notes.
- Row-spanning annotations (e.g. `DEAD/DRY tree (May 2017)`) as their own row.
- Rotated/sideways marginal writing, if legible.

## Notation rules (domain conventions)

- A lone dot/period in a cell = the value `0`.
- A continuous line/dash struck through a cell = no entry -> leave that cell
  empty (do not write "-" unless a dash is genuinely the recorded value, e.g.
  a printed `-` placeholder or an `NA` dash column).
- Tally marks = sum to an integer.
- Tick / X / checkmark = `X`.
- `NA` written out = `NA`.
- A value with an asterisk (`0.14*`) keeps the asterisk.
- A vertical squiggle/line drawn down several rows of one column = a "ditto"
  meaning the value above repeats. Transcribe the repeated value in each row
  it covers ONLY if that is clearly the intent; otherwise leave blank and
  note it in GOLDEN_NOTES.md.
- Circled values: transcribe the value (drop the circle).
- Corrections (struck value with a rewrite above): transcribe the FINAL
  intended value; note the correction.

## Genuinely illegible content

If, after cropping at high zoom, you cannot read a cell with reasonable
confidence: **omit the cell** (leave it empty) and list it in
`GOLDEN_NOTES.md` under "Excluded — illegible". Never guess. A golden with a
guessed value penalises correct models.

Single ambiguous characters common in these forms — decide carefully:
`4` vs `H`, `Y` vs `y` vs `4`, `N` vs `W` vs `M`, `0` vs `O` vs `o` vs `D`,
`1` vs `l` vs `I`, `5` vs `S`, `2` vs `Z`, `L` vs `C` vs `E`. Use the column's
value domain to disambiguate (e.g. a phenology column that only ever holds
`0/1/2/3/4` or `Y/N` constrains the reading), and say so in your notes.

## Output

1. `golden.xlsx` in the form dir — one sheet per page, named `page1`,
   `page2`, ... Each row of a sheet is one row of transcription; put
   `label,value` pairs as two cells; table rows as one cell per column.
   Write it with openpyxl.
2. `GOLDEN_NOTES.md` in the form dir, containing:
   - a 3-5 sentence description of the form (what it records, layout type),
   - the converter-disagreement adjudications you made (cell, candidates,
     your decision, why),
   - cells excluded as illegible,
   - anything structurally unusual (rotated text, sub-tables, ditto marks,
     row-spanning notes, skipped IDs).
3. Print a short summary: pages, table rows, header fields, adjudications
   made, cells excluded.
