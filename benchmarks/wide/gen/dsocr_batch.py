#!/usr/bin/env python3
"""Offline DeepSeek-OCR over all wide-bench form pages via vLLM's Python API
(the documented path for this model; the OpenAI chat endpoint mistokenises it).

Runs INSIDE the vLLM container:
  python3 /gen/dsocr_batch.py /work/forms /work/dsocr_out
Writes one <form>__pN.txt per page into the output dir.
"""
import sys
from pathlib import Path

from PIL import Image
from vllm import LLM, SamplingParams

FORMS_ROOT, OUT_DIR = Path(sys.argv[1]), Path(sys.argv[2])
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = "<image>\n<|grounding|>Convert the document to markdown."

llm = LLM(model="/models/deepseek-ocr", trust_remote_code=True,
          max_model_len=8192, gpu_memory_utilization=0.30,
          enforce_eager=False)
sp = SamplingParams(temperature=0, max_tokens=4096,
                    skip_special_tokens=False)

jobs = []
for form_dir in sorted(FORMS_ROOT.iterdir()):
    pages = sorted((form_dir / "pages").glob("page_*.png"))
    for p in pages:
        jobs.append((form_dir.name, p))

inputs = [{"prompt": PROMPT,
           "multi_modal_data": {"image": Image.open(p).convert("RGB")}}
          for _, p in jobs]
outs = llm.generate(inputs, sp)
for (form, p), o in zip(jobs, outs):
    dst = OUT_DIR / f"{form}__{p.stem}.txt"
    dst.write_text(o.outputs[0].text)
    print(form, p.stem, len(o.outputs[0].text))
