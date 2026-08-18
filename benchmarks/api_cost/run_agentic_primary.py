#!/usr/bin/env python3
"""Meter the current agentic primary using an isolated API-key Codex home.

The command copies the production prompt and render tool, pins the otherwise
implicit model, saves Codex's full JSONL event stream, and never reads the
user's subscription auth.json.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from openai_responses import PRICES

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BACKEND = REPO.parent / "good-shepherd" / "agents" / "formidable"
DEFAULT_FORM = REPO / "benchmarks" / "wide" / "eval_forms" / "eval_09" / "input.pdf"
OPENROUTER_CONFIG = Path.home() / ".config/formidable/openrouter.json"
OPENROUTER_PRICES = {
    "gpt-5.6-sol": {"input": 5.00, "cached_input": 0.50, "output": 30.00,
                    "as_of": "2026-08-12"},
    "gpt-5.6-terra": {"input": 1.00, "cached_input": 0.10, "output": 6.00,
                      "as_of": "2026-08-12"},
    "gpt-5.6-luna": {"input": 0.10, "cached_input": 0.01, "output": 0.60,
                     "as_of": "2026-08-12"},
}


def _find_usage(value):
    if isinstance(value, dict):
        expected = {"input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                    "output_tokens", "reasoning_output_tokens"}
        if expected & set(value):
            return value
        for child in value.values():
            if (found := _find_usage(child)) is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            if (found := _find_usage(child)) is not None:
                return found
    return None


def usage_events(path: Path) -> list[dict]:
    """Return every JSONL usage event; do not assume a Codex envelope version."""
    found = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        usage = _find_usage(event)
        if usage is not None:
            found.append({"line": line_number, "event_type": event.get("type"),
                          "usage": usage})
    return found


def price_codex_usage(model: str, usage: dict, *, provider: str = "openai") -> dict:
    """Price Codex's native cumulative buckets, bounding hidden cache writes.

    Some Codex versions report cached reads but omit the cache-write bucket. In
    that case the lower bound treats all non-cached input as ordinary input and
    the upper bound treats it all as cache writes. A point estimate would imply
    precision the event stream does not contain.
    """
    price_model = model.split("/", 1)[-1]
    prices = OPENROUTER_PRICES if provider == "openrouter" else PRICES
    if price_model not in prices:
        return {
            "cost_usd": None, "cost_usd_range": [None, None],
            "cache_write_bucket_reported": "cache_write_input_tokens" in usage,
            "price": None,
        }
    price = prices[price_model]
    input_tokens = int(usage.get("input_tokens") or 0)
    cached = int(usage.get("cached_input_tokens") or 0)
    has_cache_write_bucket = "cache_write_input_tokens" in usage
    cache_write = int(usage.get("cache_write_input_tokens") or 0)
    output = int(usage.get("output_tokens") or 0)
    ordinary_input = max(0, input_tokens - cached - cache_write)
    lower_cost = (
        ordinary_input * price["input"]
        + cached * price["cached_input"]
        + cache_write * price["input"] * 1.25
        + output * price["output"]
    ) / 1_000_000
    upper_cost = lower_cost
    if not has_cache_write_bucket:
        upper_cost += ordinary_input * price["input"] * 0.25 / 1_000_000
    return {
        "cost_usd": round(lower_cost, 8),
        "cost_usd_range": [round(lower_cost, 8), round(upper_cost, 8)],
        "cache_write_bucket_reported": has_cache_write_bucket,
        "price": {**price, "cache_write_multiplier": 1.25},
    }


def final_usage(events: list[dict]) -> dict | None:
    """Codex token_count events are cumulative; the final event is authoritative."""
    cumulative = [item for item in events
                  if item.get("event_type") in {"token_count", "turn.completed",
                                                "turn_complete", "task_complete"}]
    return (cumulative or events)[-1]["usage"] if events else None


def credit_exhausted(events_path: Path, stderr: str = "") -> bool:
    text = stderr
    if events_path.exists():
        text += events_path.read_text(errors="replace")
    lowered = text.casefold()
    return "no credits remaining" in lowered or "credit_balance_exhausted" in lowered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_FORM)
    parser.add_argument("--output", type=Path,
                        default=REPO / "benchmarks" / "api_cost_runs" / "eval_09_agentic")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--provider", choices=("openai", "openrouter"), default="openai")
    parser.add_argument("--reasoning-effort", default="",
                        help="optional explicit Codex model_reasoning_effort ablation")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--container-image", default="formidable-high-worker:local",
                        help="production High image; empty string uses host Codex")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.provider == "openrouter":
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not key and OPENROUTER_CONFIG.exists():
            key = json.loads(OPENROUTER_CONFIG.read_text())["api_key"].strip()
        key_env = "OPENROUTER_API_KEY"
    else:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        key_env = "OPENAI_API_KEY"
    if not key and not args.dry_run:
        raise SystemExit(f"{key_env} is not set")
    print(json.dumps({
        "input": str(args.input.resolve()), "output": str(args.output.resolve()),
        "model": args.model, "provider": args.provider,
        "authentication": f"isolated {key_env} Codex provider",
        "prompt": str(BACKEND / "prompts" / "codex_prompt.md"),
        "container_image": args.container_image or None,
    }, indent=2), flush=True)
    if args.dry_run:
        return 0

    args.output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.input, args.output / "input.pdf")
    shutil.copy2(BACKEND / "tools" / "render_page.py", args.output / "render_page.py")
    template = (BACKEND / "prompts" / "codex_prompt.md").read_text()
    render_tool = ("/run/render_page.py" if args.container_image else
                   str((args.output / "render_page.py").resolve()))
    prompt = (template.replace("{input_file}", "input.pdf")
              .replace("{render_tool}", render_tool))
    events = args.output / "codex_events.jsonl"
    last_message = args.output / "last_message.txt"

    with tempfile.TemporaryDirectory(prefix="formidable-api-codex-home-",
                                     ignore_cleanup_errors=True) as home:
        env = {**os.environ, "CODEX_HOME": home, key_env: key}
        if args.provider == "openrouter":
            login_command = None
        elif args.container_image:
            login_command = [
                "docker", "run", "--rm", "-i", "--memory", "1g",
                "--memory-swap", "1g", "-v", f"{Path(home).resolve()}:/codex_home",
                "-e", "CODEX_HOME=/codex_home", "--entrypoint", "codex",
                args.container_image, "login", "--with-api-key",
            ]
        else:
            login_command = [args.codex_bin, "login", "--with-api-key"]
        if login_command:
            login = subprocess.run(login_command, input=key, text=True,
                                   capture_output=True, env=env, check=False)
            if login.returncode:
                raise RuntimeError(f"API-key Codex login failed: {login.stderr[-500:]}")
        if args.container_image:
            command = [
                "docker", "run", "--rm", "-i", "--memory", "8g",
                "--memory-swap", "8g", "--shm-size", "1g",
                "--user", f"{os.getuid()}:{os.getgid()}",
                "-v", f"{Path(home).resolve()}:/codex_home",
                "-v", f"{args.output.resolve()}:/run",
                "-e", "CODEX_HOME=/codex_home", "--entrypoint", "codex",
            ]
            if args.provider == "openrouter":
                command += ["-e", "OPENROUTER_API_KEY"]
            command += [args.container_image]
            workdir, last_path = "/run", "/run/last_message.txt"
        else:
            command = [args.codex_bin]
            workdir, last_path = str(args.output.resolve()), str(last_message.resolve())
        command += [
            "exec", "--ephemeral", "--ignore-user-config",
            "--dangerously-bypass-approvals-and-sandbox", "--skip-git-repo-check",
            "--json", "--model", args.model, "-C", workdir,
            "-o", last_path, "-",
        ]
        if args.reasoning_effort:
            insert_at = command.index("exec") + 1
            command[insert_at:insert_at] = [
                "-c", f'model_reasoning_effort="{args.reasoning_effort}"']
        if args.provider == "openrouter":
            command[command.index("exec") + 1:command.index("exec") + 1] = [
                "-c", 'model_provider="openrouter"',
                "-c", 'model_providers.openrouter.name="OpenRouter"',
                "-c", 'model_providers.openrouter.base_url="https://openrouter.ai/api/v1"',
                "-c", 'model_providers.openrouter.env_key="OPENROUTER_API_KEY"',
                "-c", 'model_providers.openrouter.wire_api="responses"',
            ]
        started = time.time()
        with events.open("w") as stream:
            result = subprocess.run(command, input=prompt, text=True, stdout=stream,
                                    stderr=subprocess.PIPE, env=env, check=False,
                                    timeout=3600)
        elapsed = round(time.time() - started, 1)
    # Do not persist the key or the isolated auth directory.
    observed_events = usage_events(events)
    cumulative_usage = final_usage(observed_events)
    priced = price_codex_usage(args.model, cumulative_usage or {}, provider=args.provider)
    durable = price_codex_usage(args.model, cumulative_usage or {}, provider="openai")
    summary = {
        "version": "formidable-agentic-api-meter-v1",
        "provider": args.provider, "model": args.model,
        "reasoning_effort_requested": args.reasoning_effort or None,
        "wall_time_s": elapsed,
        "returncode": result.returncode,
        "usage_events": observed_events,
        "final_cumulative_usage": cumulative_usage,
        "cost_usd": priced["cost_usd"],
        "experiment_price_cost_usd_range": priced["cost_usd_range"],
        "durable_official_list_cost_usd_range": durable["cost_usd_range"],
        "cache_write_bucket_reported": priced["cache_write_bucket_reported"],
        "price_usd_per_million_tokens": priced["price"],
        "durable_price_usd_per_million_tokens": durable["price"],
        "events_file": events.name,
        "complete_usage_claim": cumulative_usage is not None,
        "note": ("The JSONL stream is authoritative evidence. Set complete_usage_claim only "
                 "after confirming the installed Codex version emits a final cumulative usage "
                 "event; never sum cumulative and per-turn usage together."),
    }
    (args.output / "meter.json").write_text(json.dumps(summary, indent=2) + "\n")
    if result.returncode:
        if credit_exhausted(events, result.stderr):
            raise RuntimeError("Codex API-key project has no credits remaining")
        raise RuntimeError(f"Codex exited {result.returncode}: {result.stderr[-1000:]}")
    if not (args.output / "output.xlsx").exists():
        raise RuntimeError("Agentic primary completed without output.xlsx")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
