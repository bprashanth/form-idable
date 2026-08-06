#!/usr/bin/env python3
"""Evaluate rule-geometry fingerprinting as a same-template classifier."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import template_id


def group(name):
    return re.sub(r"__v[01]$", "", name)


def evaluate(root: Path):
    forms = sorted(path for path in root.iterdir() if (path / "input.pdf").exists())
    fingerprints = {path.name: template_id.fingerprint(path / "input.pdf") for path in forms}
    pairs = []
    for index, first in enumerate(forms):
        for second in forms[index + 1:]:
            pairs.append({
                "first": first.name, "second": second.name,
                "same_template_page": group(first.name) == group(second.name),
                "score": template_id.geometry_similarity(
                    fingerprints[first.name], fingerprints[second.name]),
            })
    positives = [item for item in pairs if item["same_template_page"]]
    negatives = [item for item in pairs if not item["same_template_page"]]
    thresholds = []
    for threshold in (0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95):
        true_positive = sum(item["score"] >= threshold for item in positives)
        false_positive = sum(item["score"] >= threshold for item in negatives)
        thresholds.append({
            "threshold": threshold,
            "recall": round(true_positive / len(positives), 4),
            "false_positive_rate": round(false_positive / len(negatives), 4),
            "false_positives": false_positive,
        })
    return {
        "version": "formidable-template-geometry-eval-v1",
        "forms": len(forms), "positive_pairs": len(positives),
        "negative_pairs": len(negatives),
        "same_score": {
            "min": min(item["score"] for item in positives),
            "max": max(item["score"] for item in positives),
        },
        "different_score": {
            "min": min(item["score"] for item in negatives),
            "max": max(item["score"] for item in negatives),
        },
        "thresholds": thresholds,
        "decision": "reject geometry-only routing; require an independent printed-content channel",
        "top_false_matches": sorted(negatives, key=lambda item: item["score"], reverse=True)[:20],
        "lowest_true_matches": sorted(positives, key=lambda item: item["score"])[:20],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.root)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
