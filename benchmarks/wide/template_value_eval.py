#!/usr/bin/env python3
"""Source-aware literal-value scoring for exact-template experiments."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def norm(value):
    # Numeric zero is a real field value, not an empty cell.  Avoid the common
    # ``value or ""`` shortcut because JSON producers need not stringify it.
    text = "" if value is None else " ".join(str(value).strip().split()).casefold()
    if not text:
        return ""
    try:
        number = float(text)
        return str(int(number)) if math.isfinite(number) and number.is_integer() else str(number)
    except ValueError:
        return text


def prf(correct, predicted, golden):
    precision = correct / predicted if predicted else 0.0
    recall = correct / golden if golden else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4)}


def score(ground_truth: str | Path, decisions: dict[str, dict]):
    payload = json.loads(Path(ground_truth).read_text())
    truth = {f"r{cell['row']}_c{cell['col']}": cell
             for cell in payload["cells"]
             if cell.get("source") in {"written", "blank"}}
    written = {cell_id: cell for cell_id, cell in truth.items()
               if cell.get("source") == "written" and norm(cell.get("value"))}
    blanks = set(truth) - set(written)
    predicted = {cell_id: norm((decisions.get(cell_id) or {}).get("value"))
                 for cell_id in truth}
    correct = {cell_id for cell_id, cell in written.items()
               if predicted[cell_id] == norm(cell.get("value"))}
    wrong = {cell_id for cell_id in written
             if predicted[cell_id] and cell_id not in correct}
    omitted = {cell_id for cell_id in written if not predicted[cell_id]}
    false_fills = {cell_id for cell_id in blanks if predicted[cell_id]}
    true_blanks = blanks - false_fills

    by_kind = defaultdict(lambda: {"correct": 0, "total": 0})
    by_mark = defaultdict(lambda: {"correct": 0, "total": 0})
    for cell_id, cell in truth.items():
        ok = (cell_id in correct) if cell_id in written else (cell_id in true_blanks)
        kind = cell.get("value_kind") or "unknown"
        mark = cell.get("mark") or "unknown"
        by_kind[kind]["correct"] += int(ok)
        by_kind[kind]["total"] += 1
        by_mark[mark]["correct"] += int(ok)
        by_mark[mark]["total"] += 1

    # Strong no-pixel control: oracle occupied coordinates plus per-column
    # modal written value. It is allowed to know where writing exists.
    columns = defaultdict(list)
    for cell in written.values():
        columns[cell["col"]].append(norm(cell.get("value")))
    modes = {column: Counter(values).most_common(1)[0][0]
             for column, values in columns.items()}
    modal_hits = sum(norm(cell.get("value")) == modes[cell["col"]]
                     for cell in written.values())

    errors = wrong | omitted | false_fills
    curves = []
    for threshold in (0.5, 0.6, 0.7, 0.8, 0.9):
        review = {cell_id for cell_id in truth
                  if float((decisions.get(cell_id) or {}).get("confidence") or 0) <= threshold}
        caught = review & errors
        curves.append({
            "confidence_lte": threshold, "reviewed": len(review),
            "review_fraction": round(len(review) / len(truth), 4) if truth else 0.0,
            "caught_errors": len(caught),
            "error_recall": round(len(caught) / len(errors), 4) if errors else None,
            "queue_precision": round(len(caught) / len(review), 4) if review else None,
        })

    predicted_nonblank = len(correct) + len(wrong) + len(false_fills)
    return {
        "golden_kind": "literal_writable_cells",
        "strict_metrics_are_headline": True,
        "printed_cells_excluded": True,
        "writable_cells_including_blanks": len(truth),
        "written_nonblank": len(written), "blank_or_struck": len(blanks),
        "exact_written": prf(len(correct), predicted_nonblank, len(written)),
        "all_writable_accuracy": round((len(correct) + len(true_blanks)) / len(truth), 4)
        if truth else None,
        "blank_specificity": round(len(true_blanks) / len(blanks), 4) if blanks else None,
        "modal_oracle": {
            "description": "oracle written positions plus per-column mode; reads no pixels",
            "exact_written_recall": round(modal_hits / len(written), 4) if written else None,
        },
        "errors": {"wrong": len(wrong), "omitted": len(omitted),
                   "false_fill": len(false_fills), "total": len(errors)},
        "error_cell_ids": {"wrong": sorted(wrong), "omitted": sorted(omitted),
                           "false_fill": sorted(false_fills)},
        "accuracy_by_value_kind": {
            key: {**value, "accuracy": round(value["correct"] / value["total"], 4)}
            for key, value in sorted(by_kind.items())},
        "accuracy_by_mark": {
            key: {**value, "accuracy": round(value["correct"] / value["total"], 4)}
            for key, value in sorted(by_mark.items())},
        "confidence_review_curve": curves,
    }
