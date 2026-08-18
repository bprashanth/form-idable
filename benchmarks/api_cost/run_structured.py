#!/usr/bin/env python3
"""Run API-key-only structured Formidable experiments with exact usage logs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WIDE = HERE.parent / "wide"
sys.path.insert(0, str(WIDE))
import structured_pipeline  # noqa: E402

from openai_responses import install  # noqa: E402


PRESETS = {
    # Exact structured portion of the current High release.  The separately
    # metered agentic primary is not hidden inside this number.
    "high-structured": {
        "schema_model": "openai:gpt-5.6-luna",
        "models": ["openai:gpt-5.6-terra", "openai:gpt-5.6-luna"],
        "tag": "api_high_structured_meter_v1",
        "reasoning": "medium",
    },
    # First cheap controlled comparison: it preserves two independent readers
    # and therefore the red disagreement UX.  It is a candidate, not an
    # accepted Mid architecture until it passes the frozen gates.
    "mid-dual-nano": {
        "schema_model": "openai:gpt-5-nano",
        "models": ["openai:gpt-5-nano", "openai:gpt-4.1-nano"],
        "tag": "api_mid_dual_nano_v1",
        "reasoning": "minimal",
    },
    # Cost floor/ablation.  It cannot provide true cross-model disagreement;
    # only promote it if confidence/geometry checks focus errors as well as the
    # dual reader at a materially lower price.
    "mid-single-nano": {
        "schema_model": "openai:gpt-5-nano",
        "models": ["openai:gpt-5-nano"],
        "tag": "api_mid_single_nano_v1",
        "reasoning": "minimal",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preset", choices=sorted(PRESETS))
    parser.add_argument("--form", type=Path,
                        default=WIDE / "eval_forms" / "eval_09")
    parser.add_argument("--tag", help="override output tag")
    parser.add_argument("--pages", default="", help="comma-separated 1-based pages")
    parser.add_argument("--reuse-structure", action="store_true")
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cfg = PRESETS[args.preset]
    tag = args.tag or cfg["tag"]
    pages = [int(value) for value in args.pages.split(",") if value.strip()]
    declaration = {
        "preset": args.preset,
        "form": str(args.form.resolve()),
        "schema_model": cfg["schema_model"],
        "models": cfg["models"],
        "tag": tag,
        "pages": pages or "all",
        "authentication": "OPENAI_API_KEY only",
    }
    print(json.dumps(declaration, indent=2), flush=True)
    if args.dry_run:
        return 0
    # The exact High CLI roles used the model default (medium); Mid is
    # intentionally minimal. Preserve any explicit caller override.
    import os
    os.environ.setdefault("FORMIDABLE_OPENAI_REASONING", cfg["reasoning"])
    install(structured_pipeline)
    report = structured_pipeline.run(
        args.form.resolve(), cfg["schema_model"], cfg["models"], tag,
        pages or None, reuse_structure=args.reuse_structure,
        reuse_existing=args.reuse_existing,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
