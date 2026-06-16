FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @openai/codex@0.139.0

RUN pip3 install --no-cache-dir --break-system-packages \
    pymupdf openpyxl numpy Pillow

WORKDIR /workspace
