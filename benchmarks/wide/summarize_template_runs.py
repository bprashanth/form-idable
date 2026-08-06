#!/usr/bin/env python3
"""Summarise exact-template runs and quantify pairwise disagreement value.

The script deliberately derives micro metrics from error counts instead of
averaging per-form F1.  Pairwise comparisons operate on every writable target,
including blanks, so disagreement enrichment cannot be inflated by ignoring
false fills.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def norm(value: Any) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).strip().split())
    if not text:
        return ""
    try:
        number = float(text)
        if math.isfinite(number):
            return str(int(number)) if number.is_integer() else str(number)
    except ValueError:
        pass
    return text.casefold()


def prf(correct: int, predicted: int, golden: int) -> dict[str, float]:
    precision = correct / predicted if predicted else 0.0
    recall = correct / golden if golden else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def load_runs(root: Path) -> list[dict[str, Any]]:
    runs = []
    for score_path in sorted(root.glob("*/template_outputs/*/run.json")):
        run = json.loads(score_path.read_text())
        run["path"] = str(score_path)
        runs.append(run)

    # Agent-driven pilots may have only a score because their provider did not
    # expose normal request metadata.  Include them without inventing cost.
    for score_path in sorted(root.glob("*/template_outputs/*/score.json")):
        out_dir = score_path.parent
        if (out_dir / "run.json").exists():
            continue
        score = json.loads(score_path.read_text())
        runs.append({
            "form": out_dir.parents[1].name,
            "tag": out_dir.name,
            "model": out_dir.name,
            "mode": "page" if "page" in out_dir.name else "unknown",
            "cost_usd": None,
            "latency_s": None,
            "integrity": score,
            "path": str(score_path),
        })
    return runs


def aggregate(runs: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[run["tag"]].append(run)
    result = {}
    for tag, items in sorted(grouped.items()):
        golden = candidate = correct = omitted = wrong = false_fill = 0
        f1s = []
        costs, latencies = [], []
        for run in items:
            literal = run.get("literal")
            score = run["integrity"]
            if literal:
                errors = literal["errors"]
                g = int(literal["written_nonblank"])
                w, o, f = (int(errors["wrong"]), int(errors["omitted"]),
                           int(errors["false_fill"]))
                c = g - o + f
                exact_f1 = float(literal["exact_written"]["f1"])
            else:
                errors = score["errors"]
                g = int(score["golden_cells"])
                c = int(score["candidate_cells"])
                w = int(errors["wrong_value_at_occupied_position"])
                o = int(errors["omitted"])
                f = int(errors["false_fill_or_extra_position"])
                exact_f1 = float(score["exact_cell"]["f1"])
            golden += g
            candidate += c
            correct += g - w - o
            omitted += o
            wrong += w
            false_fill += f
            f1s.append(exact_f1)
            if run.get("cost_usd") is not None:
                costs.append(float(run["cost_usd"]))
            if run.get("latency_s") is not None:
                latencies.append(float(run["latency_s"]))
        result[tag] = {
            "model": sorted({str(x.get("model")) for x in items}),
            "mode": sorted({str(x.get("mode")) for x in items}),
            "headline_metric": ("literal writable-cell F1 (printed excluded)"
                                if all(x.get("literal") for x in items)
                                else "mixed/legacy exact-cell F1"),
            "forms": len(items),
            "form_names": sorted(x["form"] for x in items),
            "macro_exact_f1": round(sum(f1s) / len(f1s), 4),
            "micro_exact": prf(correct, candidate, golden),
            "counts": {
                "golden_nonblank": golden,
                "correct": correct,
                "wrong": wrong,
                "omitted": omitted,
                "false_fill": false_fill,
            },
            "cost_usd_known_calls": round(sum(costs), 6) if costs else None,
            "provider_latency_s_known_calls": round(sum(latencies), 1) if latencies else None,
            "cost_complete": len(costs) == len(items),
            "latency_complete": len(latencies) == len(items),
        }
    return result


def prediction_map(out_dir: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in sorted(out_dir.glob("batch_*.json")):
        if path.name.endswith(".meta.json") or path.name.endswith(".targets.json"):
            continue
        payload = json.loads(path.read_text())
        for cell in payload.get("cells", []):
            cell_id = cell.get("cell_id")
            if cell_id is not None:
                values[str(cell_id)] = norm(cell.get("value"))
    return values


def truth_and_targets(form_dir: Path, out_dir: Path) -> tuple[dict[str, str], set[str]]:
    truth_payload = json.loads((form_dir / "ground_truth.json").read_text())
    truth = {
        f"r{cell['row']}_c{cell['col']}": norm(cell.get("value"))
        for cell in truth_payload["cells"]
        if cell.get("source") in {"written", "blank"}
    }
    targets: set[str] = set()
    for path in sorted(out_dir.glob("batch_*.targets.json")):
        targets.update(str(x["cell_id"]) for x in json.loads(path.read_text()))
    # Band mode records the same decisions but historically did not persist a
    # separate targets sidecar.  Its returned IDs are therefore the audit set.
    if not targets:
        targets.update(prediction_map(out_dir))
    return truth, targets


def compare_pair(root: Path, tag_a: str, tag_b: str) -> dict[str, Any]:
    forms_a = {p.parents[2].name: p.parent for p in root.glob(f"*/template_outputs/{tag_a}/batch_*.json")
               if not p.name.endswith((".meta.json", ".targets.json"))}
    forms_b = {p.parents[2].name: p.parent for p in root.glob(f"*/template_outputs/{tag_b}/batch_*.json")
               if not p.name.endswith((".meta.json", ".targets.json"))}
    common = sorted(set(forms_a) & set(forms_b))
    counts = defaultdict(int)
    for form in common:
        form_dir = root / form
        a, b = prediction_map(forms_a[form]), prediction_map(forms_b[form])
        truth, targets_a = truth_and_targets(form_dir, forms_a[form])
        _truth_b, targets_b = truth_and_targets(form_dir, forms_b[form])
        targets = targets_a & targets_b
        for cell_id in targets:
            expected = truth.get(cell_id, "")
            va, vb = a.get(cell_id, ""), b.get(cell_id, "")
            a_bad, b_bad = va != expected, vb != expected
            disagree = va != vb
            counts["cells"] += 1
            counts["a_errors"] += int(a_bad)
            counts["b_errors"] += int(b_bad)
            if disagree:
                counts["disagreements"] += 1
                counts["a_errors_in_disagreement"] += int(a_bad)
                counts["b_errors_in_disagreement"] += int(b_bad)
                counts["a_only_correct"] += int(not a_bad and b_bad)
                counts["b_only_correct"] += int(a_bad and not b_bad)
                counts["both_wrong_different"] += int(a_bad and b_bad)
            else:
                counts["agreement_errors"] += int(a_bad)

    cells = counts["cells"]
    disagreements = counts["disagreements"]
    agreements = cells - disagreements
    return {
        "tag_a": tag_a,
        "tag_b": tag_b,
        "forms": len(common),
        "form_names": common,
        "cells_including_blanks": cells,
        "disagreements": disagreements,
        "disagreement_rate": round(disagreements / cells, 4) if cells else None,
        "a_errors": counts["a_errors"],
        "b_errors": counts["b_errors"],
        "a_error_capture": round(counts["a_errors_in_disagreement"] / counts["a_errors"], 4)
        if counts["a_errors"] else None,
        "b_error_capture": round(counts["b_errors_in_disagreement"] / counts["b_errors"], 4)
        if counts["b_errors"] else None,
        "a_error_rate_disagreement": round(counts["a_errors_in_disagreement"] / disagreements, 4)
        if disagreements else None,
        "a_error_rate_agreement": round(counts["agreement_errors"] / agreements, 4)
        if agreements else None,
        "a_only_correct": counts["a_only_correct"],
        "b_only_correct": counts["b_only_correct"],
        "both_wrong_different": counts["both_wrong_different"],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = ["# Exact-template literal-value summary", "",
             "Printed cells are excluded from value F1; all writable blanks remain in false-fill checks.",
             "", "## Runs", "",
             "| tag | forms | macro literal F1 | micro literal F1 | correct | wrong | omitted | false fill | known cost | latency |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for tag, item in report["runs"].items():
        c = item["counts"]
        cost = "unknown" if item["cost_usd_known_calls"] is None else f"${item['cost_usd_known_calls']:.4f}"
        latency = "unknown" if item["provider_latency_s_known_calls"] is None else f"{item['provider_latency_s_known_calls']:.1f}s"
        lines.append(f"| {tag} | {item['forms']} | {item['macro_exact_f1']:.4f} | "
                     f"{item['micro_exact']['f1']:.4f} | {c['correct']} | {c['wrong']} | "
                     f"{c['omitted']} | {c['false_fill']} | {cost} | {latency} |")
    lines.extend(["", "## Pairwise disagreement", ""])
    for pair in report["pairs"]:
        disagreement_rate = pair["disagreement_rate"] or 0.0
        capture = pair["a_error_capture"] or 0.0
        inside = pair["a_error_rate_disagreement"] or 0.0
        outside = pair["a_error_rate_agreement"] or 0.0
        lines.extend([
            f"### {pair['tag_a']} vs {pair['tag_b']}", "",
            f"Common forms: {pair['forms']}; cells including blanks: {pair['cells_including_blanks']}; "
            f"disagreements: {pair['disagreements']} ({disagreement_rate:.2%}).",
            "",
            f"For `{pair['tag_a']}`, disagreements capture {capture:.2%} of errors. "
            f"Its error rate is {inside:.2%} inside disagreement and "
            f"{outside:.2%} in agreement.",
            "",
            f"Only A correct: {pair['a_only_correct']}; only B correct: {pair['b_only_correct']}; "
            f"both wrong differently: {pair['both_wrong_different']}.", "",
        ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--pair", nargs=2, action="append", default=[])
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    runs = load_runs(args.root)
    report = {
        "root": str(args.root),
        "runs": aggregate(runs),
        "pairs": [compare_pair(args.root, a, b) for a, b in args.pair],
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.json:
        args.json.write_text(rendered)
    if args.markdown:
        args.markdown.write_text(markdown(report) + "\n")
    if not args.json and not args.markdown:
        print(rendered, end="")


if __name__ == "__main__":
    main()
