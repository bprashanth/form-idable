#!/usr/bin/env python3
"""LoRA fine-tune Qwen3-VL-2B on the synthetic form-transcription SFT set.

Runs inside the vLLM cu130 image (torch/transformers preinstalled; pip install
peft first). Vision tower frozen; LoRA on the language model's attention+MLP.
Saves the adapter, then merges to a full model dir for vLLM serving.

Usage (inside container):
  python3 train_qwen3vl_lora.py /models/qwen3-vl-2b /data/sft.jsonl /out/adapter /out/merged
"""
import json, random, sys
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import (AutoProcessor, AutoModelForImageTextToText,
                          Trainer, TrainingArguments)
from peft import LoraConfig, get_peft_model
from PIL import Image

MODEL_DIR, SFT_JSONL, ADAPTER_OUT, MERGED_OUT = sys.argv[1:5]
MAX_LEN = 10240


class FormSet(Dataset):
    def __init__(self, path, processor):
        self.rows = [json.loads(l) for l in open(path)]
        random.Random(0).shuffle(self.rows)
        self.p = processor

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        imgs = [Image.open(p).convert("RGB") for p in r["images"]]
        user = {"role": "user", "content":
                [{"type": "image"} for _ in imgs] + [{"type": "text", "text": r["prompt"]}]}
        asst = {"role": "assistant", "content": [{"type": "text", "text": r["response"]}]}
        prompt_text = self.p.apply_chat_template([user], tokenize=False,
                                                 add_generation_prompt=True)
        full_text = self.p.apply_chat_template([user, asst], tokenize=False,
                                               add_generation_prompt=False)
        enc = self.p(text=[full_text], images=imgs, return_tensors="pt",
                     max_length=MAX_LEN, truncation=True)
        prompt_len = self.p(text=[prompt_text], images=imgs,
                            return_tensors="pt").input_ids.shape[1]
        input_ids = enc.input_ids[0]
        labels = input_ids.clone()
        labels[:prompt_len] = -100
        item = {"input_ids": input_ids, "attention_mask": enc.attention_mask[0],
                "labels": labels, "pixel_values": enc.pixel_values,
                "image_grid_thw": enc.image_grid_thw}
        if "mm_token_type_ids" in enc:
            item["mm_token_type_ids"] = enc.mm_token_type_ids[0]
        return item


def collate(batch):  # batch size 1 — pass through
    b = batch[0]
    out = {"input_ids": b["input_ids"][None], "attention_mask": b["attention_mask"][None],
           "labels": b["labels"][None], "pixel_values": b["pixel_values"],
           "image_grid_thw": b["image_grid_thw"]}
    if "mm_token_type_ids" in b:
        out["mm_token_type_ids"] = b["mm_token_type_ids"][None]
    return out


def main():
    processor = AutoProcessor.from_pretrained(MODEL_DIR)
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_DIR, torch_dtype=torch.bfloat16, device_map="cuda")
    model.config.use_cache = False
    for p in model.model.visual.parameters():  # freeze vision tower
        p.requires_grad = False

    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"],
                      task_type="CAUSAL_LM")
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    ds = FormSet(SFT_JSONL, processor)
    args = TrainingArguments(
        output_dir=ADAPTER_OUT, num_train_epochs=2,
        per_device_train_batch_size=1, gradient_accumulation_steps=8,
        learning_rate=1e-4, lr_scheduler_type="cosine", warmup_ratio=0.05,
        logging_steps=5, save_strategy="no", bf16=True,
        gradient_checkpointing=True, report_to=[], remove_unused_columns=False,
        dataloader_num_workers=2)
    Trainer(model=model, args=args, train_dataset=ds, data_collator=collate).train()

    model.save_pretrained(ADAPTER_OUT)
    print("adapter saved; merging...")
    merged = model.merge_and_unload()
    merged.save_pretrained(MERGED_OUT, safe_serialization=True)
    processor.save_pretrained(MERGED_OUT)
    print(f"merged model -> {MERGED_OUT}")


if __name__ == "__main__":
    main()
