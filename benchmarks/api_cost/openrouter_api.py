#!/usr/bin/env python3
"""Metered OpenRouter structured-vision adapter for local cost experiments."""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


URL = "https://openrouter.ai/api/v1/chat/completions"
CONFIG = Path.home() / ".config/formidable/openrouter.json"


def _key() -> str:
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    return json.loads(CONFIG.read_text())["api_key"]


def _image(path: Path) -> dict:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {
        "url": f"data:image/png;base64,{encoded}"}}


def openrouter_json(model: str, prompt: str, images: list[Path], schema: dict,
                    *, thinking: str | None = "minimal",
                    max_tokens: int = 16384) -> tuple[dict, dict]:
    """Return strict JSON and the provider's unmodified usage accounting."""
    reasoning = ({"enabled": False} if thinking in {"none", "off", "disabled"}
                 else ({"effort": thinking} if thinking else None))
    content = [{"type": "text", "text": prompt}, *[_image(path) for path in images]]
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "formidable_extraction", "strict": True, "schema": schema}},
        "usage": {"include": True},
    }
    if reasoning is not None:
        payload["reasoning"] = reasoning
    headers = {
        "Authorization": f"Bearer {_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://fomoscribe.netlify.app",
        "X-Title": "Formidable local API cost benchmark",
    }
    started = time.time()
    request = urllib.request.Request(
        URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            envelope = json.load(response)
    except urllib.error.HTTPError as error:
        body = error.read()[:1000]
        raise RuntimeError(f"OpenRouter {model} HTTP {error.code}: {body!r}") from error

    message = envelope["choices"][0]["message"]["content"]
    if isinstance(message, list):
        message = "".join(part.get("text", "") for part in message
                          if isinstance(part, dict))
    usage = envelope.get("usage") or {}
    parsed = json.loads(message)
    return parsed, {
        "provider": "openrouter", "model": model, "reasoning_policy": thinking,
        "in_tok": usage.get("prompt_tokens"),
        "cached_in_tok": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
        "out_tok": usage.get("completion_tokens"),
        "thinking_tok": (usage.get("completion_tokens_details") or {}).get(
            "reasoning_tokens", usage.get("reasoning_tokens", 0)),
        "cost_usd": usage.get("cost"),
        "latency_s": round(time.time() - started, 2),
        "raw_usage": usage,
        "provider_name": envelope.get("provider"),
        "generation_id": envelope.get("id"),
    }
