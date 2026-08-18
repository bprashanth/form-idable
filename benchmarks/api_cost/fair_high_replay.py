#!/usr/bin/env python3
"""Replay saved structured evidence through the unchanged production High wrapper.

This is the apples-to-apples bridge missing from the earlier API-cost study.
It holds the agentic-primary workbook fixed, places one saved structure/two-reader
run at High's ``high_v1`` evidence path, and invokes ``high_worker.process`` with
``reuse_existing=True``. No model call, golden value, or production mutation is
used while routing, selecting content, creating red/orange review evidence,
building Analytics, or writing the delivered workbook.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
WIDE = REPO / "benchmarks" / "wide"
BACKEND = REPO.parent / "good-shepherd" / "agents" / "formidable"


def copy_evidence(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in source.glob("page_*__*.json"):
        shutil.copy2(path, destination / path.name)
    run = json.loads((source / "run.json").read_text())
    run["tag"] = "high_v1"
    (destination / "run.json").write_text(json.dumps(run, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True,
                        help="real fixture id, for example eval_09")
    parser.add_argument("--evidence", type=Path, required=True,
                        help="saved structured-pipeline output directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--primary", type=Path,
                        help="fixed agentic output.xlsx; defaults to additive_v1 fixture")
    args = parser.parse_args()

    fixture = WIDE / "eval_forms" / args.fixture
    primary = args.primary or (
        REPO / "benchmarks" / "high_runs" / "additive_v1" /
        args.fixture / "primary" / "output.xlsx")
    for required in (fixture / "input.pdf", fixture / "golden.xlsx",
                     args.evidence / "run.json", primary):
        if not required.exists():
            raise FileNotFoundError(required)
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite replay: {args.output}")

    args.output.mkdir(parents=True)
    (args.output / "primary").mkdir()
    shutil.copy2(primary, args.output / "primary" / "output.xlsx")
    canonical_dir = args.output / "form" / "canonical_outputs" / "high_v1"
    copy_evidence(args.evidence.resolve(), canonical_dir)

    sys.path.insert(0, str(BACKEND))
    os.environ["FORMIDABLE_HIGH_PIPELINE_DIR"] = str(WIDE)
    import high_worker  # noqa: E402
    run = high_worker.process(
        fixture / "input.pdf", args.output, ecology_online=False,
        reuse_existing=True)

    sys.path.insert(0, str(WIDE))
    import wide_diff  # noqa: E402
    metrics = wide_diff.compare(
        str(fixture / "golden.xlsx"), str(args.output / "content.xlsx"))["metrics"]
    report = {
        "version": "formidable-fair-high-replay-v1",
        "fixture": args.fixture,
        "pipeline": "unchanged production High wrapper over saved structured evidence",
        "agentic_primary": str(primary),
        "structured_evidence": str(args.evidence.resolve()),
        "models": run["extraction"].get("models"),
        "schema_model": run["extraction"].get("schema_model"),
        "reasoning": "as recorded by the saved evidence",
        "route": run["route"],
        "selected_reader": run["content"].get("selected_reader"),
        "semantic": {key: metrics[key] for key in (
            "semantic_all_f1", "semantic_all_precision", "semantic_all_recall",
            "num_f1", "word_f1", "semantic_code_f1", "cell_frac")},
        "review": run["review"],
        "analytics": run["analytics"],
        "ecology": json.loads((args.output / "ecology_review.json").read_text()),
        "structured_cost_usd": run["extraction"].get("cost_usd"),
        "structured_provider_latency_s": run["extraction"].get("latency_s"),
    }
    (args.output / "fair_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
