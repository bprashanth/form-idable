#!/usr/bin/env bash
# Serve a local VLM on the GB10 via the existing vLLM nightly image.
# Usage: ./serve_local.sh qwen8b|qwen2b|dsocr [port]
# One model at a time (unified memory). Stop with: docker rm -f wide-vlm
set -euo pipefail
MODELS_DIR="$HOME/models/wide-bench"
IMAGE="vllm/vllm-openai:cu130-nightly"
PORT="${2:-8010}"

case "$1" in
  qwen8b) MODEL="/models/qwen3-vl-8b-fp8";  SERVED="qwen3-vl-8b-fp8"; EXTRA="";;
  qwen2b) MODEL="/models/qwen3-vl-2b";      SERVED="qwen3-vl-2b";     EXTRA="";;
  dsocr)  MODEL="/models/deepseek-ocr";     SERVED="deepseek-ocr";
          EXTRA="--trust-remote-code";;
  *) echo "usage: $0 qwen8b|qwen2b|dsocr [port]"; exit 1;;
esac

docker rm -f wide-vlm 2>/dev/null || true
docker run -d --name wide-vlm --gpus all --memory 60g --memory-swap 60g --network host \
  -v "$MODELS_DIR":/models \
  --shm-size 8g \
  "$IMAGE" \
  --model "$MODEL" --served-model-name "$SERVED" \
  --port "$PORT" --gpu-memory-utilization 0.30 \
  --max-model-len 16384 --limit-mm-per-prompt.image 8 $EXTRA
echo "started wide-vlm ($SERVED) on :$PORT — watch: docker logs -f wide-vlm"
