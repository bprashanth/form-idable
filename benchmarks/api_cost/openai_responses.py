#!/usr/bin/env python3
"""Metered OpenAI Responses API adapter for Formidable experiments.

This module deliberately has no OpenAI SDK dependency.  The provider response's
complete ``usage`` object is retained in the per-call metadata written by the
existing structured pipeline.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


API_URL = "https://api.openai.com/v1/responses"

# USD per million tokens.  Prices are intentionally explicit and dated: cost
# reports retain the table entry used, so a later price change cannot silently
# rewrite an old experiment.
PRICES = {
    "gpt-5.6-sol": {"input": 5.00, "cached_input": 0.50, "output": 30.00,
                    "as_of": "2026-08-12"},
    "gpt-5.6-terra": {"input": 2.50, "cached_input": 0.25, "output": 15.00,
                      "as_of": "2026-08-12"},
    "gpt-5.6-luna": {"input": 1.00, "cached_input": 0.10, "output": 6.00,
                     "as_of": "2026-08-12"},
    "gpt-5.4-nano": {"input": 0.20, "cached_input": 0.02, "output": 1.25,
                     "as_of": "2026-08-12"},
    "gpt-5-nano": {"input": 0.05, "cached_input": 0.005, "output": 0.40,
                   "as_of": "2026-08-12"},
    "gpt-4.1-nano": {"input": 0.10, "cached_input": 0.025, "output": 0.40,
                     "as_of": "2026-08-12"},
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60,
                    "as_of": "2026-08-12"},
}


def _integer(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def usage_parts(usage: dict[str, Any]) -> dict[str, int]:
    """Normalize token accounting without discarding the raw provider object."""
    input_details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}
    input_tokens = _integer(usage.get("input_tokens"))
    cached = _integer(input_details.get("cached_tokens"))
    cache_write = _integer(input_details.get("cache_write_tokens"))
    # The API's input total includes detail buckets.  Be conservative if a
    # future response shape reports overlapping values.
    uncached = max(0, input_tokens - cached - cache_write)
    return {
        "input_tokens": input_tokens,
        "uncached_input_tokens": uncached,
        "cached_input_tokens": cached,
        "cache_write_tokens": cache_write,
        "output_tokens": _integer(usage.get("output_tokens")),
        "reasoning_tokens": _integer(output_details.get("reasoning_tokens")),
        "total_tokens": _integer(usage.get("total_tokens")),
    }


def price_usage(model: str, usage: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Price one usage object; reasoning is already part of output tokens."""
    if model not in PRICES:
        raise KeyError(f"No audited price for {model!r}; add it to PRICES before running")
    price = PRICES[model]
    parts = usage_parts(usage)
    dollars = (
        parts["uncached_input_tokens"] * price["input"]
        + parts["cached_input_tokens"] * price["cached_input"]
        # GPT-5.6 cache writes are billed at 1.25x uncached input.  Applying
        # the rule generically is conservative for a model that emits this
        # optional bucket.
        + parts["cache_write_tokens"] * price["input"] * 1.25
        + parts["output_tokens"] * price["output"]
    ) / 1_000_000
    return round(dollars, 8), {**price, "cache_write_multiplier": 1.25}


def _data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def build_payload(model: str, prompt: str, images: list[Path], schema: dict,
                  *, reasoning: str | None = "minimal", image_detail: str = "high",
                  max_output_tokens: int = 16384) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    content.extend({"type": "input_image", "image_url": _data_url(path),
                    "detail": image_detail} for path in images)
    text_config = {"format": {
        "type": "json_schema", "name": "formidable_extraction",
        "strict": True, "schema": schema,
    }}
    # verbosity is a GPT-5 control; older GPT-4.x structured-output models do
    # not consistently accept it.
    if not model.startswith("gpt-4"):
        text_config["verbosity"] = "low"
    payload = {
        "model": model,
        "input": [{"role": "user", "content": content}],
        "text": text_config,
        "max_output_tokens": max_output_tokens,
        "store": False,
    }
    # Legacy 4.x models do not accept the reasoning object. Current GPT-5 nano
    # accepts minimal/low/medium/high but not none.
    if reasoning:
        payload["reasoning"] = {"effort": reasoning}
    return payload


def _output_text(response: dict[str, Any]) -> str:
    pieces = []
    for item in response.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                pieces.append(content.get("text") or "")
    text = "".join(pieces)
    if not text:
        raise RuntimeError("OpenAI response contained no output_text")
    return text


def responses_json(model: str, prompt: str, images: list[Path], schema: dict,
                   *, thinking: str | None = "minimal") -> tuple[dict, dict]:
    """Call Responses API and return parsed structured data plus full usage."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    image_detail = os.environ.get("FORMIDABLE_OPENAI_IMAGE_DETAIL", "high")
    max_output = int(os.environ.get("FORMIDABLE_OPENAI_MAX_OUTPUT_TOKENS", "16384"))
    payload = build_payload(model, prompt, images, schema, reasoning=thinking,
                            image_detail=image_detail, max_output_tokens=max_output)
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    retry_delays = (0, 2, 5, 10)
    response: dict[str, Any] | None = None
    attempts = 0
    for attempts, delay in enumerate(retry_delays, start=1):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(request, timeout=900) as handle:
                response = json.loads(handle.read())
            break
        except urllib.error.HTTPError as error:
            body = error.read()[:1000]
            retryable = error.code in {408, 409, 429} or error.code >= 500
            # Credit exhaustion cannot heal during this process and must not
            # waste time retrying the same billable experiment.
            exhausted = b"credit_balance_exhausted" in body
            if not retryable or exhausted or attempts == len(retry_delays):
                raise RuntimeError(
                    f"OpenAI {model} failed with HTTP {error.code}: {body!r}") from error
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            if attempts == len(retry_delays):
                raise RuntimeError(
                    f"OpenAI {model} network failure after {attempts} attempts: {error}") from error
    if response is None:
        raise AssertionError("unreachable")
    if response.get("status") not in {None, "completed"}:
        raise RuntimeError(
            f"OpenAI {model} response status={response.get('status')!r}: "
            f"{response.get('incomplete_details')!r}")
    try:
        parsed = json.loads(_output_text(response))
    except json.JSONDecodeError as error:
        raise RuntimeError(f"OpenAI {model} returned invalid structured JSON") from error
    usage = response.get("usage") or {}
    cost, price = price_usage(model, usage)
    parts = usage_parts(usage)
    return parsed, {
        "provider": "openai_api_key",
        "model": response.get("model") or model,
        "response_id": response.get("id"),
        "in_tok": parts["input_tokens"],
        "cached_input_tok": parts["cached_input_tokens"],
        "cache_write_tok": parts["cache_write_tokens"],
        "out_tok": parts["output_tokens"],
        "thinking_tok": parts["reasoning_tokens"],
        "total_tok": parts["total_tokens"],
        "raw_usage": usage,
        "price_usd_per_million_tokens": price,
        "cost_usd": cost,
        "latency_s": round(time.time() - started, 1),
        "attempts": attempts,
        "image_detail": image_detail,
    }


def install(structured_pipeline) -> None:
    """Install an additive ``openai:MODEL`` provider in the saved pipeline."""
    original = structured_pipeline.provider_json

    def provider(model_spec, prompt, images, schema, *, thinking="minimal"):
        if model_spec.startswith("openai:"):
            effort = os.environ.get("FORMIDABLE_OPENAI_REASONING", "minimal")
            if effort == "omit":
                effort = None
            return responses_json(model_spec.split(":", 1)[1], prompt, images, schema,
                                  thinking=effort)
        return original(model_spec, prompt, images, schema, thinking=thinking)

    structured_pipeline.provider_json = provider
