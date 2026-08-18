#!/usr/bin/env python3
"""Summarize raw per-call usage from a structured pipeline run."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_json", type=Path)
    args = parser.parse_args()
    run = json.loads(args.run_json.read_text())
    groups = defaultdict(lambda: {"calls": 0, "input_tokens": 0,
                                  "cached_input_tokens": 0, "cache_write_tokens": 0,
                                  "output_tokens": 0, "reasoning_tokens": 0,
                                  "cost_usd": 0.0})
    missing_usage = []
    for index, call in enumerate(run.get("calls") or []):
        key = f"{call.get('stage')}:{call.get('model')}"
        group = groups[key]
        group["calls"] += 1
        usage = call.get("raw_usage")
        if not isinstance(usage, dict):
            missing_usage.append(index)
            continue
        input_details = usage.get("input_tokens_details") or {}
        output_details = usage.get("output_tokens_details") or {}
        group["input_tokens"] += int(usage.get("input_tokens") or 0)
        group["cached_input_tokens"] += int(input_details.get("cached_tokens") or 0)
        group["cache_write_tokens"] += int(input_details.get("cache_write_tokens") or 0)
        group["output_tokens"] += int(usage.get("output_tokens") or 0)
        group["reasoning_tokens"] += int(output_details.get("reasoning_tokens") or 0)
        group["cost_usd"] += float(call.get("cost_usd") or 0)
    total = sum(float(call.get("cost_usd") or 0) for call in run.get("calls") or [])
    report = {
        "source": str(args.run_json),
        "groups": {key: {**value, "cost_usd": round(value["cost_usd"], 8)}
                   for key, value in sorted(groups.items())},
        "structured_cost_usd": round(total, 8),
        "structured_cost_per_100_same_size_forms_usd": round(total * 100, 4),
        "calls_missing_raw_usage": missing_usage,
        "complete": not missing_usage,
        "reasoning_billing_note": "reasoning tokens are included in output_tokens and not added twice",
    }
    print(json.dumps(report, indent=2))
    return 1 if missing_usage else 0


if __name__ == "__main__":
    raise SystemExit(main())
