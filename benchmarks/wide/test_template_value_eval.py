#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import template_value_eval


def main():
    truth = {"cells": [
        {"row": 0, "col": 0, "source": "printed", "value": "Header"},
        {"row": 1, "col": 0, "source": "written", "value": "8.4",
         "value_kind": "dec", "mark": "text"},
        {"row": 1, "col": 1, "source": "written", "value": 0,
         "value_kind": "int", "mark": "dot"},
        {"row": 2, "col": 0, "source": "blank", "value": None,
         "value_kind": "dec", "mark": "strike"},
        {"row": 2, "col": 1, "source": "blank", "value": None,
         "value_kind": "int", "mark": "text"},
    ]}
    decisions = {
        "r1_c0": {"value": "6.4", "confidence": 0.5},
        "r1_c1": {"value": "0", "confidence": 0.4},
        "r2_c0": {"value": "-", "confidence": 0.6},
        "r2_c1": {"value": None, "confidence": 0.9},
    }
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "truth.json"
        path.write_text(json.dumps(truth))
        report = template_value_eval.score(path, decisions)
    assert report["printed_cells_excluded"]
    assert report["writable_cells_including_blanks"] == 4
    assert report["exact_written"]["f1"] == 0.4
    assert report["errors"] == {"wrong": 1, "omitted": 0, "false_fill": 1, "total": 2}
    assert report["all_writable_accuracy"] == 0.5
    assert report["confidence_review_curve"][0]["error_recall"] == 0.5


if __name__ == "__main__":
    main()
