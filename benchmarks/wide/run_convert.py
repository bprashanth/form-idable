#!/usr/bin/env python3
"""Converter pass for golden-building: transcribe each eval form PER PAGE
(both tiles of a page per request) and stitch with ### PAGE N markers.

Per-page requests sidestep provider image-count caps on multi-page forms and
keep page alignment exact for the adjudicator.

Usage: python3 run_convert.py <provider> <model> <form_dir> [form_dir ...]
Writes outputs/<provider>__<model>__pertile.{txt,json} (no scoring — goldens
don't exist yet).
"""
import json, sys, time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import wide_bench  # noqa: E402

PAGE_PROMPT = """You are transcribing ONE page of a scanned hand-filled paper form
(printed structure filled in by hand). You get the page as two overlapping
top/bottom half images — transcribe each region once.

Transcribe EVERYTHING: title, header fields, every table row incl. header,
checkbox states, tally marks, marginal notes.
Notation: lone dot=0; line struck through cell=blank; tally marks sum to an
integer; tick/X=X; empty box=blank.
Output ONLY CSV (cells comma-separated, label:value pairs as "label,value").
No prose, no markdown fences. Better an uncertain value than an omission.
"""


def convert(provider, model, form_dir: Path):
    sender = {"gemini": wide_bench.gemini_oneshot,
              "openrouter": wide_bench.openrouter_oneshot}[provider]
    tiles = sorted((form_dir / "tiles").glob("page_*_h*.png"))
    pages = sorted({int(t.stem.split("_")[1]) for t in tiles})
    wide_bench.TRANSCRIBE_PROMPT = PAGE_PROMPT
    parts, cost, t0 = [], 0.0, time.time()
    for p in pages:
        pt = [t for t in tiles if t.stem.startswith(f"page_{p}_")]
        for attempt in range(3):
            try:
                text, meta = sender(model, pt)
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 2: raise
                time.sleep(5)
        cost += meta.get("cost_usd") or 0
        parts.append(f"### PAGE {p}\n{text}")
    dt = time.time() - t0
    out_dir = form_dir / "outputs"; out_dir.mkdir(exist_ok=True)
    tag = f"{provider}__{model.replace('/', '_')}__pertile"
    (out_dir / f"{tag}.txt").write_text("\n".join(parts))
    row = {"form": form_dir.name, "provider": provider, "model": model,
           "mode": "pertile", "converter_only": True,
           "cost_usd": round(cost, 4), "latency_s": round(dt, 1), "error": ""}
    (out_dir / f"{tag}.json").write_text(json.dumps(row, indent=2))
    print(json.dumps(row))


if __name__ == "__main__":
    provider, model = sys.argv[1], sys.argv[2]
    for f in sys.argv[3:]:
        try:
            convert(provider, model, Path(f).resolve())
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"form": f, "model": model, "error": str(e)[:200]}))
