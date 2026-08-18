#!/usr/bin/env python3
"""Meter current High structured calls through Codex 0.147.0 API-key auth."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
WIDE = HERE.parent / "wide"
sys.path.insert(0, str(WIDE))
import structured_pipeline  # noqa: E402

from run_agentic_primary import (OPENROUTER_CONFIG, credit_exhausted, final_usage,  # noqa: E402
                                  price_codex_usage, usage_events)


def cli_json(model: str, prompt: str, images: list[Path], schema: dict,
             *, thinking: str = "minimal") -> tuple[dict, dict]:
    del thinking  # Current High did not override the CLI/model default.
    home = os.environ["FORMIDABLE_API_CODEX_HOME"]
    events_dir = Path(os.environ["FORMIDABLE_API_EVENTS_DIR"])
    events_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="formidable-cli-meter-call-") as temporary:
        root = Path(temporary)
        schema_path, output_path = root / "schema.json", root / "output.json"
        safe_model = model.replace("/", "_").replace(":", "_")
        events_path = events_dir / f"{safe_model}__{uuid.uuid4().hex}.jsonl"
        schema_path.write_text(json.dumps(schema))
        command = [
            os.environ.get("FORMIDABLE_CODEX_BIN", "codex"),
            "exec", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
            "--sandbox", "read-only", "--json", "--model", model,
            "--output-schema", str(schema_path),
            "--output-last-message", str(output_path),
        ]
        provider = os.environ.get("FORMIDABLE_CLI_PROVIDER", "openai")
        if provider == "openrouter":
            insert_at = command.index("exec") + 1
            command[insert_at:insert_at] = [
                "-c", 'model_provider="openrouter"',
                "-c", 'model_providers.openrouter.name="OpenRouter"',
                "-c", 'model_providers.openrouter.base_url="https://openrouter.ai/api/v1"',
                "-c", 'model_providers.openrouter.env_key="OPENROUTER_API_KEY"',
                "-c", 'model_providers.openrouter.wire_api="responses"',
                # Unknown OpenRouter models fall back to Codex metadata that
                # disables reasoning; Gemini's Responses endpoint rejects
                # that. Make the experiment setting explicit and record the
                # actual reasoning tokens from the usage event below.
                "-c", f'model_reasoning_effort="{os.environ.get("FORMIDABLE_STRUCTURED_REASONING", "minimal")}"',
            ]
        for image in images:
            command.extend(["--image", str(image.resolve())])
        command.append("-")
        with events_path.open("w") as stream:
            result = subprocess.run(command, input=prompt, text=True, stdout=stream,
                                    stderr=subprocess.PIPE, timeout=900, check=False,
                                    env={**os.environ, "CODEX_HOME": home})
        if result.returncode or not output_path.exists():
            if credit_exhausted(events_path, result.stderr):
                raise RuntimeError(f"Codex API-key {model} has no credits remaining")
            raise RuntimeError(f"Codex API-key {model} failed: {result.stderr[-1000:]}")
        parsed = json.loads(output_path.read_text())
        usage = final_usage(usage_events(events_path))
        if usage is None:
            raise RuntimeError(f"Codex {model} JSONL had no usage event: {events_path}")
        priced = price_codex_usage(model, usage, provider=provider)
        return parsed, {
            "provider": f"codex_cli_{provider}_api_key", "model": model,
            "codex_version": "0.147.0",
            "in_tok": usage.get("input_tokens"),
            "cached_input_tok": usage.get("cached_input_tokens"),
            "cache_write_tok": usage.get("cache_write_input_tokens"),
            "out_tok": usage.get("output_tokens"),
            "thinking_tok": usage.get("reasoning_output_tokens"),
            "total_tok": usage.get("total_tokens"), "raw_usage": usage,
            "cost_usd": priced["cost_usd"],
            "price_usd_per_million_tokens": priced["price"],
            "latency_s": round(time.time() - started, 1),
            "events_file": str(events_path), "attempts": 1,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--form", type=Path, default=WIDE / "eval_forms" / "eval_09")
    parser.add_argument("--tag", default="api_high_cli_meter_v1")
    parser.add_argument("--pages", default="")
    parser.add_argument("--events", type=Path,
                        default=HERE.parent / "api_cost_runs" / "eval_09_structured_events")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--provider", choices=("openai", "openrouter"), default="openai")
    parser.add_argument("--schema-model", default="gpt-5.6-luna")
    parser.add_argument("--models", default="gpt-5.6-terra,gpt-5.6-luna")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps({
        "form": str(args.form.resolve()), "tag": args.tag,
        "schema_model": args.schema_model, "readers": args.models.split(","),
        "codex_bin": args.codex_bin, "required_codex_version": "0.147.0",
        "authentication": ("isolated OPENAI_API_KEY Codex login" if args.provider == "openai"
                           else "OPENROUTER_API_KEY custom Responses provider"),
    }, indent=2), flush=True)
    if args.dry_run:
        return 0
    key_name = "OPENAI_API_KEY" if args.provider == "openai" else "OPENROUTER_API_KEY"
    key = os.environ.get(key_name, "").strip()
    if not key and args.provider == "openrouter" and OPENROUTER_CONFIG.exists():
        key = json.loads(OPENROUTER_CONFIG.read_text())["api_key"].strip()
    if not key:
        raise SystemExit(f"{key_name} is not set")
    os.environ[key_name] = key
    version = subprocess.run([args.codex_bin, "--version"], capture_output=True,
                             text=True, check=True).stdout.strip()
    if "0.147.0" not in version:
        raise RuntimeError(f"Expected High Codex 0.147.0, got {version!r}")
    pages = [int(value) for value in args.pages.split(",") if value.strip()]
    with tempfile.TemporaryDirectory(prefix="formidable-api-codex-home-") as home:
        if args.provider == "openai":
            login = subprocess.run([args.codex_bin, "login", "--with-api-key"], input=key,
                                   text=True, capture_output=True, check=False,
                                   env={**os.environ, "CODEX_HOME": home})
            if login.returncode:
                raise RuntimeError(f"API-key Codex login failed: {login.stderr[-500:]}")
        os.environ.update({
            "FORMIDABLE_API_CODEX_HOME": home,
            "FORMIDABLE_API_EVENTS_DIR": str(args.events.resolve()),
            "FORMIDABLE_CODEX_BIN": args.codex_bin,
            "FORMIDABLE_CLI_PROVIDER": args.provider,
        })
        original = structured_pipeline.provider_json

        def provider(spec, prompt, images, schema, *, thinking="minimal"):
            if spec.startswith("codexapi:"):
                return cli_json(spec.split(":", 1)[1], prompt, images, schema,
                                thinking=thinking)
            return original(spec, prompt, images, schema, thinking=thinking)

        structured_pipeline.provider_json = provider
        report = structured_pipeline.run(
            args.form.resolve(), f"codexapi:{args.schema_model}",
            [f"codexapi:{model.strip()}" for model in args.models.split(",")],
            args.tag, pages or None)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
