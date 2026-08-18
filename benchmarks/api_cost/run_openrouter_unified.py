#!/usr/bin/env python3
"""Run the compact targeted-peer experiment through OpenRouter API-key auth."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import openrouter_api
import unified_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--form", type=Path,
                        default=unified_pipeline.WIDE / "eval_forms" / "eval_09")
    parser.add_argument("--model", default="openai/gpt-5.6-luna")
    parser.add_argument("--peer-model", default="google/gemini-3.5-flash-lite")
    parser.add_argument("--no-peer", action="store_true")
    parser.add_argument("--tag", default="api_mid_openrouter_unified_v1")
    parser.add_argument("--pages", default="")
    parser.add_argument("--confidence", type=float, default=.8)
    parser.add_argument("--peer-cap-fraction", type=float, default=.1)
    parser.add_argument("--peer-cap-count", type=int, default=80)
    parser.add_argument("--reasoning", default="none",
                        choices=("none", "minimal", "low", "medium", "high"))
    parser.add_argument("--peer-reasoning", default="minimal",
                        choices=("none", "minimal", "low", "medium", "high"))
    parser.add_argument("--reuse-existing", action="store_true")
    args = parser.parse_args()
    pages = [int(value) for value in args.pages.split(",") if value.strip()]

    def call(model, prompt, images, schema, *, thinking=None):
        return openrouter_api.openrouter_json(
            model, prompt, images, schema, thinking=thinking)

    unified_pipeline.responses_json = call
    result = unified_pipeline.run(
        args.form.resolve(), args.model,
        None if args.no_peer else args.peer_model, args.tag,
        pages=pages or None, threshold=args.confidence,
        cap_fraction=args.peer_cap_fraction, cap_count=args.peer_cap_count,
        provider="openrouter", reasoning=args.reasoning,
        peer_reasoning=args.peer_reasoning, reuse_existing=args.reuse_existing)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
