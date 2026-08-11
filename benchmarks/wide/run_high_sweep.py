#!/usr/bin/env python3
"""Resumable, production-image benchmark over every real PDF fixture.

Each form runs in a fresh capped container. Completed runs are never repeated
unless --force is supplied. The summary preserves low and high metrics side by
side so the deployment decision cannot be made from a hand-picked form.
"""
from __future__ import annotations

import argparse
import concurrent.futures
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
        resume_existing = (rebuild_from_evidence or
                           (not force and (output / "primary" / "output.xlsx").exists()))
        command = [
            "docker", "run", "--rm", "--memory", "8g", "--memory-swap", "8g",
            "-v", f"{(fixture / 'input.pdf').resolve()}:/input.pdf:ro",
            "-v", f"{output.resolve()}:/run",
        ]
        codex_auth = Path.home() / ".codex/auth.json"
        if not codex_auth.exists():
            raise RuntimeError(f"Codex subscription auth not found at {codex_auth}")
        command += ["-v", f"{codex_auth.resolve()}:/root/.codex/auth.json:ro"]
        for name in ("HIGH_SCHEMA_MODEL", "HIGH_PRIMARY_MODEL", "HIGH_PEER_MODEL"):
            if os.environ.get(name):
                command += ["-e", name]
        command += [
            image, "python3", "-c",
            "from pathlib import Path; from high_worker import process; "
            f"process(Path('/input.pdf'), Path('/run'), "
            f"reuse_existing={resume_existing!r})",
        ]
        subprocess.run(command, check=True)
        (output / "wall_time.json").write_text(json.dumps({
            "seconds": round(time.time() - started, 1),
        }, indent=2) + "\n")

    # Score exactly the content workbook selected by the production coverage
    # gate. The delivered workbook differs only by its ecology_review audit
    # sheet, which is excluded from transcription metrics.
    content_workbook = output / "content.xlsx"
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
    parser.add_argument("--workers", type=int, choices=(1, 2), default=1,
                        help="parallel form containers; capped at 2 for DGX memory safety")
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
    results_by_fixture = {}

    def finish(fixture):
        return run_one(fixture, args.output / fixture.name,
                       args.image, args.force, args.rebuild_from_evidence)

    def record(fixture, result):
        results_by_fixture[fixture.name] = result
        results = [results_by_fixture[item.name] for item in selected
                   if item.name in results_by_fixture]
        (args.output / "summary.json").write_text(json.dumps({
            "version": "formidable-high-sweep-v1",
            "selected": [item.name for item in selected],
            "completed": results,
        }, indent=2) + "\n")
        high = result["high"]
        low = result["low"] or {}
        print(f"  {fixture.name}: semantic F1 low={low.get('semantic_all_f1')} "
              f"high={high.get('semantic_all_f1')}", flush=True)

    if args.workers == 1:
        for index, fixture in enumerate(selected, 1):
            print(f"[{index}/{len(selected)}] {fixture.name}", flush=True)
            record(fixture, finish(fixture))
        return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        pending = {}
        for index, fixture in enumerate(selected, 1):
            print(f"[{index}/{len(selected)}] {fixture.name}", flush=True)
            pending[executor.submit(finish, fixture)] = fixture
        for future in concurrent.futures.as_completed(pending):
            fixture = pending[future]
            record(fixture, future.result())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
