#!/usr/bin/env python3
"""LoRA fine-tune a Qwen3-VL model on the form-transcription SFT set.

v2 changes over train_qwen3vl_lora.py: configurable epochs / max length / rank,
truncation reporting (a silently truncated target teaches the model to stop
early — the worst failure mode for a transcription model), and a held-out
loss split.

Inside the vLLM container:
  python3 train_lora_v2.py --model /models/qwen3-vl-2b --sft /work/sft.jsonl \
      --adapter /models/tuned/a --merged /models/tuned/m [--epochs 3] [--max-len 16384]
"""
import argparse, json, random, sys
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import (AutoProcessor, AutoModelForImageTextToText,
                          Trainer, TrainingArguments)
from peft import LoraConfig, get_peft_model
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--sft", required=True)
ap.add_argument("--adapter", required=True)
ap.add_argument("--merged", required=True)
ap.add_argument("--epochs", type=float, default=3.0)
ap.add_argument("--max-len", type=int, default=16384)
ap.add_argument("--rank", type=int, default=32)
ap.add_argument("--lr", type=float, default=1e-4)
ap.add_argument("--accum", type=int, default=8)
ap.add_argument("--gpu-frac", type=float, default=0.45,
                help="hard cap on GPU memory as a fraction of total. On the "
                     "GB10 the 121GB pool is shared with the CPU and GPU "
                     "allocations are charged to NO process, so a docker "
                     "--memory cap does NOT bound them — only this does. "
                     "Without it an over-allocation livelocks the host.")
A = ap.parse_args()

# Bound the CUDA caching allocator BEFORE any weights are loaded.
if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(A.gpu_frac, 0)
    total = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU memory capped at {A.gpu_frac:.0%} of {total:.0f}GB "
          f"= {A.gpu_frac * total:.0f}GB", flush=True)


class FormSet(Dataset):
    def __init__(self, rows, processor, max_len):
        self.rows, self.p, self.max_len = rows, processor, max_len
        self.truncated = 0

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        imgs = [Image.open(p).convert("RGB") for p in r["images"]]
        user = {"role": "user", "content":
                [{"type": "image"} for _ in imgs] + [{"type": "text", "text": r["prompt"]}]}
        asst = {"role": "assistant", "content": [{"type": "text", "text": r["response"]}]}
        p_text = self.p.apply_chat_template([user], tokenize=False, add_generation_prompt=True)
        f_text = self.p.apply_chat_template([user, asst], tokenize=False,
                                            add_generation_prompt=False)
        full = self.p(text=[f_text], images=imgs, return_tensors="pt")
        if full.input_ids.shape[1] > self.max_len:
            self.truncated += 1
        enc = self.p(text=[f_text], images=imgs, return_tensors="pt",
                     max_length=self.max_len, truncation=True)
        plen = self.p(text=[p_text], images=imgs, return_tensors="pt").input_ids.shape[1]
        ids = enc.input_ids[0]
        labels = ids.clone()
        labels[:plen] = -100
        item = {"input_ids": ids, "attention_mask": enc.attention_mask[0],
                "labels": labels, "pixel_values": enc.pixel_values,
                "image_grid_thw": enc.image_grid_thw}
        if "mm_token_type_ids" in enc:
            item["mm_token_type_ids"] = enc.mm_token_type_ids[0]
        return item


def collate(batch):
    b = batch[0]
    out = {"input_ids": b["input_ids"][None], "attention_mask": b["attention_mask"][None],
           "labels": b["labels"][None], "pixel_values": b["pixel_values"],
           "image_grid_thw": b["image_grid_thw"]}
    if "mm_token_type_ids" in b:
        out["mm_token_type_ids"] = b["mm_token_type_ids"][None]
    return out


def main():
    processor = AutoProcessor.from_pretrained(A.model)
    model = AutoModelForImageTextToText.from_pretrained(
        A.model, torch_dtype=torch.bfloat16, device_map="cuda")
    model.config.use_cache = False
    visual = getattr(model, "visual", None) or getattr(model.model, "visual", None)
    if visual is not None:
        for p in visual.parameters():
            p.requires_grad = False
        print("vision tower frozen")

    model = get_peft_model(model, LoraConfig(
        r=A.rank, lora_alpha=A.rank * 2, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM"))
    model.print_trainable_parameters()

    rows = [json.loads(l) for l in open(A.sft)]
    random.Random(0).shuffle(rows)
    n_val = max(8, len(rows) // 20)
    train_rows, val_rows = rows[n_val:], rows[:n_val]
    ds = FormSet(train_rows, processor, A.max_len)
    vs = FormSet(val_rows, processor, A.max_len)
    print(f"train {len(ds)}  val {len(vs)}")

    args = TrainingArguments(
        output_dir=A.adapter, num_train_epochs=A.epochs,
        per_device_train_batch_size=1, gradient_accumulation_steps=A.accum,
        learning_rate=A.lr, lr_scheduler_type="cosine", warmup_ratio=0.05,
        logging_steps=10, save_strategy="no", bf16=True,
        eval_strategy="epoch", per_device_eval_batch_size=1,
        gradient_checkpointing=True, report_to=[], remove_unused_columns=False,
        dataloader_num_workers=4)
    Trainer(model=model, args=args, train_dataset=ds, eval_dataset=vs,
            data_collator=collate).train()

    if ds.truncated or vs.truncated:
        print(f"WARNING: {ds.truncated + vs.truncated} samples exceeded "
              f"max_len={A.max_len} and were truncated")
    model.save_pretrained(A.adapter)
    print("adapter saved; merging...")
    merged = model.merge_and_unload()
    merged.save_pretrained(A.merged, safe_serialization=True)
    processor.save_pretrained(A.merged)
    print(f"merged model -> {A.merged}")


if __name__ == "__main__":
    main()
