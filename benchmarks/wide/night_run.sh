#!/usr/bin/env bash
# Overnight sequencer. Each stage VERIFIES ITS PRECONDITIONS before touching the
# GPU — this is not blind auto-chaining (which is what turned one host freeze
# into a reboot loop on 2026-07-31). Every GPU launch goes through gpu_run.sh,
# which enforces the memory cap, the >40GB free preflight and the recent-reboot
# refusal.
set -u
cd "$(dirname "$0")"
LOG() { echo "[$(date +%H:%M:%S)] $*"; }

need_free() {                      # need_free <gb>
  local a; a=$(free -g | awk 'NR==2{print $7}')
  if [ "$a" -lt "$1" ]; then LOG "ABORT: only ${a}G free, need $1G"; return 1; fi
  return 0
}

wait_container_gone() {            # wait_container_gone <name> <max_min>
  local n=$1 max=$2 i=0
  while docker ps --format '{{.Names}}' | grep -q "$n"; do
    sleep 60; i=$((i+1))
    if [ "$i" -ge "$max" ]; then LOG "timeout waiting for $n"; return 1; fi
    local a; a=$(free -g | awk 'NR==2{print $7}')
    if [ "$a" -lt 25 ]; then LOG "MEMORY CRITICAL ${a}G — killing $n"; docker rm -f "$n"; return 1; fi
  done
  return 0
}

serve() {                          # serve <merged_dir> <served_name>
  need_free 45 || return 1
  docker rm -f wide-vlm >/dev/null 2>&1
  nohup ./gpu_run.sh wide-vlm 45 -- --network host \
    -v /home/beeps/models/wide-bench:/models \
    vllm/vllm-openai:cu130-nightly \
    --model "/models/tuned/$1" --served-model-name "$2" \
    --port 8010 --gpu-memory-utilization 0.28 \
    --max-model-len 12288 --limit-mm-per-prompt.image 4 > "serve_$2.log" 2>&1 &
  local i=0
  until curl -s --max-time 2 http://localhost:8010/v1/models 2>/dev/null | grep -q "$2"; do
    sleep 10; i=$((i+1))
    [ "$i" -gt 90 ] && { LOG "server $2 failed to start"; return 1; }
    docker ps --format '{{.Names}}' | grep -q wide-vlm || { LOG "server container died"; return 1; }
  done
  LOG "serving $2"
}

train() {                          # train <sft> <adapter> <merged>
  need_free 60 || return 1
  docker rm -f wide-vlm >/dev/null 2>&1; sleep 10
  ./gpu_run.sh trainrun 50 -- \
    -v /home/beeps/models/wide-bench:/models \
    -v "$PWD":/work -w /work -v "$PWD/gen":/gen \
    --entrypoint bash vllm/vllm-openai:cu130-nightly \
    -c "pip install -q peft >/dev/null 2>&1; python3 /gen/train_lora_v2.py \
        --model /models/qwen3-vl-2b --sft /work/$1 \
        --adapter /models/tuned/$2 --merged /models/tuned/$3 \
        --epochs 2 --rank 32 --max-len 10240 --gpu-frac 0.40" > "train_$3.log" 2>&1
}

# ── stage 1: v3 eval ─────────────────────────────────────────────
LOG "stage 1: wait for v3 training"
wait_container_gone train2bv3 120 || exit 1
if [ -d "$HOME/models/wide-bench/tuned/merged-2b-v3" ]; then
  serve merged-2b-v3 qwen3-vl-2b-v3 && {
    LOG "stage 1: eval v3 on frozen struct_eval"
    ./run_struct_eval.sh local qwen3-vl-2b-v3 > eval_struct_v3.log 2>&1
    LOG "stage 1: eval v3 on partner forms"
    ./run_tuned_eval.sh qwen3-vl-2b-v3 > eval_partner_v3.log 2>&1
    LOG "stage 2: structured extraction (tier-3 ceiling) with v3"
    python3 run_structured_suite.py qwen3-vl-2b-v3 > struct_tier3.log 2>&1
  }
else
  LOG "no merged-2b-v3 — training failed"
fi

# ── stage 3: v4 (field-photo) train + eval ───────────────────────
if grep -q CORPUS-V4-DONE corpus_v4.log 2>/dev/null; then
  LOG "stage 3: build v4 SFT"
  .venv/bin/python3 gen/make_sft2.py train_forms_v4 sft_v4_arch >> sft_v4.log 2>&1
  cat sft_v4_arch/sft.jsonl sft_v3_tpl/sft.jsonl > sft_v4.jsonl
  LOG "stage 3: train v4 ($(wc -l < sft_v4.jsonl) samples)"
  train sft_v4.jsonl adapter-2b-v4 merged-2b-v4
  wait_container_gone trainrun 150 || true
  if [ -d "$HOME/models/wide-bench/tuned/merged-2b-v4" ]; then
    serve merged-2b-v4 qwen3-vl-2b-v4 && {
      ./run_struct_eval.sh local qwen3-vl-2b-v4 > eval_struct_v4.log 2>&1
      ./run_tuned_eval.sh qwen3-vl-2b-v4 > eval_partner_v4.log 2>&1
    }
  fi
fi
LOG "NIGHT-RUN-DONE"
