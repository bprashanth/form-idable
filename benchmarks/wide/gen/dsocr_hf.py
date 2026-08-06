#!/usr/bin/env python3
"""DeepSeek-OCR via its own transformers infer() API (model-card path).
Inside container: python3 /gen/dsocr_hf.py /work/forms /work/dsocr_out [probe]
"""
import sys, time
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

FORMS_ROOT, OUT_DIR = Path(sys.argv[1]), Path(sys.argv[2])
PROBE = len(sys.argv) > 3 and sys.argv[3] == "probe"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL = "/models/deepseek-ocr"

tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
model = AutoModel.from_pretrained(MODEL, trust_remote_code=True,
                                  _attn_implementation="eager",
                                  use_safetensors=True)
model = model.eval().cuda().to(torch.bfloat16)

PROMPT = "<image>\n<|grounding|>Convert the document to markdown."

jobs = []
for form_dir in sorted(FORMS_ROOT.iterdir()):
    for p in sorted((form_dir / "pages").glob("page_*.png")):
        jobs.append((form_dir.name, p))
if PROBE:
    jobs = jobs[:1]

for form, p in jobs:
    dst = OUT_DIR / f"{form}__{p.stem}.txt"
    if dst.exists() and dst.stat().st_size > 400:
        continue
    t0 = time.time()
    scratch = OUT_DIR / "_scratch"
    scratch.mkdir(exist_ok=True)
    res = model.infer(tok, prompt=PROMPT, image_file=str(p),
                      output_path=str(scratch), base_size=1024,
                      image_size=640, crop_mode=True, save_results=True,
                      test_compress=False)
    # infer() writes result.mmd into output_path; prefer its return if str
    text = res if isinstance(res, str) else ""
    mmd = scratch / "result.mmd"
    if (not text) and mmd.exists():
        text = mmd.read_text()
    dst.write_text(text or "")
    print(form, p.stem, len(text), f"{time.time()-t0:.0f}s", flush=True)
print("DSOCR-HF-DONE")
