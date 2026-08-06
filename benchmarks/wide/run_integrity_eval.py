#!/usr/bin/env python3
"""Apply integrity_eval to existing benchmark workbooks without API calls."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import integrity_eval


HERE = Path(__file__).parent


def mean(rows, path):
    values = []
    for row in rows:
        value = row
        for key in path.split("."):
            value = value[key]
        if value is not None:
            values.append(value)
    return round(statistics.mean(values), 4) if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(HERE / "eval_forms"))
    parser.add_argument("--out", default=str(HERE / "integrity_results.json"))
    args = parser.parse_args()

    root = Path(args.root)
    rows = []
    for form in sorted(root.glob("eval_*")):
        golden = form / "golden.xlsx"
        if not golden.exists():
            continue
        for candidate in sorted((form / "outputs").glob("*.xlsx")):
            result = integrity_eval.score(golden, candidate)
            metadata_path = candidate.with_suffix(".json")
            metadata = {}
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text())
                except (OSError, json.JSONDecodeError):
                    pass
            rows.append({
                "form": form.name,
                "candidate": candidate.stem,
                "path": str(candidate.relative_to(HERE)),
                "metadata": metadata,
                "integrity": result,
            })

    grouped = {}
    for row in rows:
        # The filename is the durable key; some old JSON sidecars omitted tags.
        grouped.setdefault(row["candidate"], []).append(row["integrity"])
    summary = []
    for candidate, group in grouped.items():
        summary.append({
            "candidate": candidate,
            "n_forms": len(group),
            "content_f1_mean": mean(group, "content_anywhere.f1"),
            "exact_cell_f1_mean_diagnostic": mean(group, "exact_cell.f1"),
            "occupied_position_f1_mean_diagnostic": mean(group, "occupied_position.f1"),
            "page_f1_mean": mean(group, "pages.f1"),
            "cell_count_ratio_mean": mean(group, "cell_count_ratio"),
            "false_fill_mean": mean(group, "errors.false_fill_or_extra_position"),
            "constancy_excess_mean": mean(group, "constancy.max_excess_over_golden"),
            "content_lift_over_modal_mean": mean(
                group, "oracle_modal_control.candidate_content_f1_lift"),
            "exact_recall_lift_over_modal_mean_diagnostic": mean(
                group, "oracle_modal_control.candidate_exact_recall_lift"),
        })
    summary.sort(key=lambda row: (-row["n_forms"], -(row["content_f1_mean"] or 0)))
    report = {
        "warning": (
            "Real eval goldens are content-consensus workbooks. Exact-cell and occupied-position "
            "metrics are structural diagnostics, not accuracy headlines."
        ),
        "n_outputs": len(rows),
        "summary": summary,
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(json.dumps({"out": args.out, "n_outputs": len(rows), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
