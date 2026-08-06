#!/usr/bin/env python3
"""Measure whether a review manifest actually concentrates exact-cell errors."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def norm(value):
    text = " ".join(str(value or "").strip().split()).casefold()
    if not text:
        return ""
    try:
        number = float(text)
        return str(int(number)) if math.isfinite(number) and number.is_integer() else str(number)
    except ValueError:
        return text


def evaluate(form_dir: Path, manifest_path: Path):
    truth_payload = json.loads((form_dir / "ground_truth.json").read_text())
    truth = {f"r{cell['row']}_c{cell['col']}": norm(cell.get("value"))
             for cell in truth_payload["cells"]
             if cell.get("source") in {"written", "blank"}}
    manifest = json.loads(manifest_path.read_text())
    cells = {cell["id"].split(":")[-1]: cell for cell in manifest["cells"]}
    common = set(truth) & set(cells)
    errors = {cell_id for cell_id in common
              if norm(cells[cell_id].get("presented_value")) != truth[cell_id]}
    reviewed = {item["cell_id"].split(":")[-1]
                for item in manifest["views"]["transcription_attention"]}
    caught = errors & reviewed
    return {
        "form": form_dir.name, "manifest": str(manifest_path),
        "target_cells_including_blanks": len(common),
        "errors": len(errors), "reviewed": len(reviewed), "caught_errors": len(caught),
        "error_recall": round(len(caught) / len(errors), 4) if errors else None,
        "queue_precision": round(len(caught) / len(reviewed), 4) if reviewed else None,
        "review_fraction": round(len(reviewed) / len(common), 4) if common else None,
        "errors_outside_queue": sorted(errors - reviewed),
        "reviewed_correct_cells": sorted(reviewed - errors),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("form", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.form, args.manifest)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
