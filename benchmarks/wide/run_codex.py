#!/usr/bin/env python3
"""Run the codex CLI agentic baseline on wide-bench forms (the way prod does:
codex exec in a workdir with input.pdf + render_page.py, crop/zoom allowed),
then score output.xlsx with wide_diff. Sector-agnostic variant of
prompts/codex_prompt.md.

Usage: python3 run_codex.py <form_dir> [form_dir ...]
"""
import json, shutil, subprocess, sys, time
from pathlib import Path

HERE  = Path(__file__).parent
GSHEP = Path.home() / "src/github.com/bprashanth/good-shepherd/agents/formidable"
sys.path.insert(0, str(HERE))
import wide_diff  # noqa: E402

PROMPT = """You are transcribing a scanned hand-filled paper form (printed
structure — titles, labels, table grids, checkboxes — filled in by hand) into
a spreadsheet.

You have been given `input.pdf` in the current directory. Your goal is to
produce `output.xlsx` containing one sheet named `v2`.

You have a sandbox with PyMuPDF (fitz), Pillow, numpy, openpyxl, and a shell.
Work directly from the PDF.

## The quality bar

Every table, heading, metadata field, checkbox state, tally mark and marginal
note visible on every page must show up in `v2`. Use your turn budget to
verify and correct cell values by cropping/zooming.

## Using render_page.py to render and crop

```
python3 render_page.py input.pdf --out crop.png --bbox x0,y0,x1,y1 --zoom Z --page N
```

- `--bbox x0,y0,x1,y1` is **fractions (0.0-1.0)** of the page width/height.
- `--zoom` is capped at source native resolution and ~1568px on longest edge.
- Start with a full-page overview (`--zoom 2`, no `--bbox`), then crop into
  regions to read cell values. Check all pages.

## Notation conventions

- A **dot/period** alone in a cell means the recorded value is literally `0`
- A **continuous line drawn through a cell** means "no entry" — leave blank
- **Tally marks** (`I`, `l`, `1`, `|` repeated) are a count — sum to an integer
- **Checkbox/tick marks** mean "present/yes" — transcribe as `X`; an empty box
  means absent — leave blank

Transcribe values as literally as you can read them; better an uncertain value
than an omission. When done, `output.xlsx` must exist in the current directory.
"""


def run_form(form_dir: Path, timeout=None):
    import os
    timeout = timeout or int(os.environ.get("CODEX_TIMEOUT", "900"))
    work = form_dir / "codex_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    shutil.copy(form_dir / "input.pdf", work / "input.pdf")
    shutil.copy(GSHEP / "tools/render_page.py", work / "render_page.py")
    t0 = time.time()
    proc = subprocess.run(
        ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox",
         "--skip-git-repo-check", "-C", str(work),
         "-o", str(work / "last_message.txt"), "-"],
        input=PROMPT, text=True, capture_output=True, timeout=timeout,
        cwd=str(work))
    dt = time.time() - t0
    (work / "run.log").write_text(proc.stdout[-20000:] + "\n=== STDERR ===\n" + proc.stderr[-5000:])
    out = work / "output.xlsx"
    tag = "codex__cli__agentic"
    out_dir = form_dir / "outputs"; out_dir.mkdir(exist_ok=True)
    if not out.exists():
        row = {"form": form_dir.name, "provider": "codex", "model": "codex-cli",
               "mode": "agentic", "error": f"no output.xlsx (rc={proc.returncode})",
               "latency_s": round(dt, 1)}
    elif not (form_dir / "golden.xlsx").exists():
        # converter mode (golden being built): save output, skip scoring
        shutil.copy(out, out_dir / f"{tag}.xlsx")
        row = {"form": form_dir.name, "provider": "codex", "model": "codex-cli",
               "mode": "agentic", "converter_only": True, "latency_s": round(dt, 1),
               "error": ""}
        (out_dir / f"{tag}.json").write_text(json.dumps(row, indent=2))
        print(json.dumps(row))
        return row
    else:
        shutil.copy(out, out_dir / f"{tag}.xlsx")
        r = wide_diff.compare(str(form_dir / "golden.xlsx"), str(out))
        m = r["metrics"]
        # token count from codex stdout if present (rough: look for 'tokens used')
        row = {"form": form_dir.name, "provider": "codex", "model": "codex-cli",
               "mode": "agentic", "passed": r["passed"],
               "cell_frac": m["cell_frac"], "num_recall": m["num_recall"],
               "num_precision": m["num_precision"], "num_f1": m["num_f1"],
               "word_recall": m["word_recall"], "word_precision": m["word_precision"],
               "word_f1": m["word_f1"], "cost_usd": None, "latency_s": round(dt, 1),
               "error": ""}
    (out_dir / f"{tag}.json").write_text(json.dumps(row, indent=2))
    print(json.dumps(row))
    # merge into results.json
    res_path = HERE / "results.json"
    rows = json.loads(res_path.read_text()) if res_path.exists() else []
    rows = [x for x in rows if not (x["form"] == row["form"] and x.get("provider") == "codex")]
    row["sector"] = form_dir.name.split("__")[0]
    rows.append(row)
    res_path.write_text(json.dumps(rows, indent=2))
    return row


if __name__ == "__main__":
    for f in sys.argv[1:]:
        try:
            run_form(Path(f).resolve())
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"form": f, "provider": "codex", "error": str(e)[:300]}))
