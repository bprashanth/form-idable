#!/usr/bin/env python3
"""Benchmark DeepSeek-OCR (served locally via vLLM) on wide-bench forms.

OCR-specialist path: one request per page image with the model's native
grounding prompt (it ignores task instructions), outputs stitched with
"### PAGE N" separators, then scored through the same text->xlsx->diff
pipeline. Markdown table pipes tokenize fine in xlsx_diff (splits on |).

Usage: python3 run_dsocr.py <endpoint> <form_dir> [form_dir ...]
"""
import json, sys, time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import wide_bench, wide_diff  # noqa: E402

PROMPT = "<|grounding|>Convert the document to markdown."
MODEL = "deepseek-ocr"


def run_form(endpoint, form_dir: Path):
    pages = wide_bench._images(form_dir, "oneshot")
    assert pages, f"no pages for {form_dir}"
    parts, t0 = [], time.time()
    for i, p in enumerate(pages, 1):
        payload = {"model": MODEL, "temperature": 0, "max_tokens": 8192,
                   "messages": [{"role": "user", "content": [
                       {"type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{wide_bench._b64(p)}"}},
                       {"type": "text", "text": PROMPT}]}]}
        resp = wide_bench._post(f"{endpoint.rstrip('/')}/chat/completions", payload, {},
                                timeout=1800)
        parts.append(f"### PAGE {i}\n" + resp["choices"][0]["message"]["content"])
    dt = time.time() - t0
    text = "\n".join(parts)
    out_dir = form_dir / "outputs"; out_dir.mkdir(exist_ok=True)
    tag = f"local__{MODEL}__oneshot"
    (out_dir / f"{tag}.txt").write_text(text)
    xlsx = wide_bench.text_to_xlsx(text, out_dir / f"{tag}.xlsx")
    r = wide_diff.compare(str(form_dir / "golden.xlsx"), str(xlsx))
    m = r["metrics"]
    row = {"form": form_dir.name, "provider": "local", "model": MODEL,
           "mode": "oneshot", "passed": r["passed"], "cell_frac": m["cell_frac"],
           "num_recall": m["num_recall"], "num_precision": m["num_precision"],
           "num_f1": m["num_f1"], "word_recall": m["word_recall"],
           "word_precision": m["word_precision"], "word_f1": m["word_f1"],
           "cost_usd": 0.0, "latency_s": round(dt, 1), "error": ""}
    (out_dir / f"{tag}.json").write_text(json.dumps(row, indent=2))
    print(json.dumps(row))


if __name__ == "__main__":
    ep = sys.argv[1]
    for f in sys.argv[2:]:
        try:
            run_form(ep, Path(f).resolve())
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"form": f, "model": MODEL, "error": str(e)[:200]}))
