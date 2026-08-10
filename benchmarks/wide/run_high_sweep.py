#!/usr/bin/env python3
"""Resumable, production-image benchmark over every real PDF fixture.

Each form runs in a fresh capped container. Completed runs are never repeated
unless --force is supplied. The summary preserves low and high metrics side by
side so the deployment decision cannot be made from a hand-picked form.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FORMS = HERE / "eval_forms"
DEFAULT_OUTPUT = REPO / "benchmarks" / "high_runs" / "sweep_v1"
DEFAULT_IMAGE = "formidable-high-worker:local"
sys.path.insert(0, str(HERE))
import wide_diff  # noqa: E402


def provider_key() -> str:
    existing = os.environ.get("OPENROUTER_API_KEY")
    if existing:
        return existing
    path = Path.home() / ".config/formidable/openrouter.json"
    value = json.loads(path.read_text())
    key = value.get("api_key") or value.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(f"No OpenRouter key in {path}")
    return key


def pdf_fixtures() -> list[Path]:
    return [directory for directory in sorted(FORMS.glob("eval_*"))
            if json.loads((directory / "source_map.json").read_text())[
                "original_path"].lower().endswith(".pdf")]


def score(fixture: Path, candidate: Path) -> dict:
    return wide_diff.compare(str(fixture / "golden.xlsx"), str(candidate))["metrics"]


def compact(metrics: dict) -> dict:
    names = ("semantic_all_recall", "semantic_all_precision", "semantic_all_f1",
             "num_f1", "word_f1", "semantic_code_f1", "cell_frac")
    return {name: metrics.get(name) for name in names}


def run_one(fixture: Path, output: Path, image: str, force: bool,
            rebuild_from_evidence: bool = False) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    finished = output / "run.json"
    if rebuild_from_evidence and not finished.exists():
        raise RuntimeError(f"Cannot rebuild incomplete run {output}")
    if not finished.exists() or force or rebuild_from_evidence:
        started = time.time()
        environment = os.environ.copy()
        environment["OPENROUTER_API_KEY"] = provider_key()
        command = [
            "docker", "run", "--rm", "--memory", "8g", "--memory-swap", "8g",
            "-e", "OPENROUTER_API_KEY",
            "-v", f"{(fixture / 'input.pdf').resolve()}:/input.pdf:ro",
            "-v", f"{output.resolve()}:/run",
            image, "python3", "-c",
            "from pathlib import Path; from high_worker import process; "
            f"process(Path('/input.pdf'), Path('/run'), "
            f"reuse_existing={rebuild_from_evidence!r})",
        ]
        subprocess.run(command, check=True, env=environment)
        (output / "wall_time.json").write_text(json.dumps({
            "seconds": round(time.time() - started, 1),
        }, indent=2) + "\n")

    # Score only literal page sheets. The production download additionally
    # carries an ecology_review audit sheet whose repeated observed values and
    # explanatory prose are useful to people but are not model transcription.
    content_workbook = output / "form" / "canonical_outputs" / "high_v1" / "output.xlsx"
    high = score(fixture, content_workbook)
    low_path = fixture / "codex_work" / "output.xlsx"
    low = score(fixture, low_path) if low_path.exists() else None
    run = json.loads(finished.read_text())
    return {
        "fixture": fixture.name,
        "source": json.loads((fixture / "source_map.json").read_text())["original_path"],
        "pages": fitz.open(fixture / "input.pdf").page_count,
        "low": compact(low) if low else None,
        "high": compact(high),
        "high_review": run["review"],
        "high_analytics": run["analytics"],
        "cost_usd": run["extraction"].get("cost_usd"),
        "provider_latency_s": run["extraction"].get("latency_s"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--only", action="append", help="fixture id, e.g. eval_13")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--rebuild-from-evidence", action="store_true",
        help="regenerate canonical/review/analytics/crops from saved model responses; no model calls",
    )
    args = parser.parse_args()
    selected = [item for item in pdf_fixtures()
                if not args.only or item.name in set(args.only)]
    if not selected:
        raise SystemExit("No PDF fixtures selected")

    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for index, fixture in enumerate(selected, 1):
        print(f"[{index}/{len(selected)}] {fixture.name}", flush=True)
        results.append(run_one(fixture, args.output / fixture.name,
                               args.image, args.force, args.rebuild_from_evidence))
        (args.output / "summary.json").write_text(json.dumps({
            "version": "formidable-high-sweep-v1",
            "selected": [item.name for item in selected],
            "completed": results,
        }, indent=2) + "\n")
        high = results[-1]["high"]
        low = results[-1]["low"] or {}
        print(f"  semantic F1 low={low.get('semantic_all_f1')} "
              f"high={high.get('semantic_all_f1')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
