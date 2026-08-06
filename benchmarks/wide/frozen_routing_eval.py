#!/usr/bin/env python3
"""One-shot false-route evaluation on frozen real forms.

The pixel matcher is only a shortlist channel.  This benchmark deliberately
uses fixed thresholds and unknown real partner forms to measure how often that
channel proposes a wrong public template.  Where cached generic structure is
available, the independent printed-label gate is evaluated too.  Cached xlsx
tokens are reported separately as a proxy and never promoted to final-gate
evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz
import openpyxl

import template_labels
import template_match


def page_count(path: Path) -> int:
    with fitz.open(path) as document:
        return document.page_count


def label_registry(manifest: Path, templates: Path):
    return {
        f"{item['template']}#page={item['page']}":
        template_labels.template_tokens(
            templates / item["template"], int(item["page"]) - 1)
        for item in json.loads(manifest.read_text())
    }


def workbook_proxy(form: Path, source_page: int):
    candidates = (
        form / "outputs" / "codex__cli__agentic.xlsx",
        form / "codex_work" / "output.xlsx",
        form / "golden.xlsx",
    )
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        return None
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    source_pages = page_count(form / "input.pdf")
    if len(workbook.worksheets) == source_pages:
        sheet = workbook.worksheets[source_page - 1]
        scope = "page"
    else:
        sheet = workbook.worksheets[0]
        scope = "document"
    text = " ".join(str(cell.value) for row in sheet.iter_rows() for cell in row
                    if cell.value is not None)
    observed = template_labels.tokens(text)
    workbook.close()
    return {"path": str(path), "sheet": sheet.title, "scope": scope,
            "tokens": observed}


def proxy_verdict(candidate: str, observed: set[str], registry):
    ranking = template_labels.rank(observed, registry)
    score, top = ranking[0]
    runner = ranking[1][0] if len(ranking) > 1 else 0.0
    accepted = (top == candidate and score >= 0.50 and score - runner >= 0.10)
    return {"accepted": accepted, "candidate": candidate, "top": top,
            "score": score, "runner_up_score": runner,
            "margin": round(score - runner, 6),
            "observed_token_count": len(observed),
            "thresholds": {"min_score": 0.50, "min_margin": 0.10}}


def evaluate(evals: Path, corpus: Path, templates: Path, manifest: Path,
             structure_tag: str, schema_model: str):
    pixels = template_match.corpus_registry(corpus, templates)
    labels = label_registry(manifest, templates)
    rows = []
    for input_path in sorted(evals.glob("eval_*/input.pdf")):
        form = input_path.parent
        for source_page in range(1, page_count(input_path) + 1):
            ranking = template_match.rank(
                template_match.render(input_path, source_page - 1), pixels)
            pixel = template_match.verdict(
                ranking, min_score=0.50, min_margin=0.02)
            row = {"form": form.name, "source_page": source_page, "pixel": pixel,
                   "printed_labels": None, "workbook_label_proxy": None}
            if pixel["status"] == "known_template":
                structure = (form / "canonical_outputs" / structure_tag /
                             f"page_{source_page}__structure__{schema_model}.json")
                if structure.exists():
                    row["printed_labels"] = template_labels.confirm(
                        pixel["candidate"], json.loads(structure.read_text()), labels)
                proxy = workbook_proxy(form, source_page)
                if proxy:
                    result = proxy_verdict(pixel["candidate"], proxy.pop("tokens"), labels)
                    row["workbook_label_proxy"] = {**proxy, **result}
            rows.append(row)

    pixel_candidates = [row for row in rows
                        if row["pixel"]["status"] == "known_template"]
    actual = [row["printed_labels"] for row in pixel_candidates
              if row["printed_labels"] is not None]
    proxies = [row["workbook_label_proxy"] for row in pixel_candidates
               if row["workbook_label_proxy"] is not None]
    return {
        "version": "formidable-frozen-real-negative-routing-v2",
        "cohort": {
            "role": "unknown-template negatives; never used to tune this policy",
            "documents": len({row["form"] for row in rows}), "pages": len(rows),
        },
        "fixed_policy": {
            "pixel": {"min_score": 0.50, "min_margin": 0.02,
                      "role": "candidate only; never sufficient for exact routing"},
            "printed_labels": {"min_score": 0.50, "min_margin": 0.10,
                               "role": "required independent confirmation"},
        },
        "summary": {
            "pixel_false_candidates": len(pixel_candidates),
            "pixel_false_candidate_rate": round(len(pixel_candidates) / len(rows), 4),
            "actual_label_checks": len(actual),
            "actual_label_false_accepts": sum(item["accepted"] for item in actual),
            "proxy_label_checks": len(proxies),
            "proxy_label_false_accepts": sum(item["accepted"] for item in proxies),
        },
        "proxy_warning": (
            "Workbook tokens may include handwriting or document-wide content. "
            "They are diagnostic only, not validation of the structure-model gate."),
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--templates", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--structure-tag", default="canonical_v1_full")
    parser.add_argument("--schema-model", default="gemini-3.5-flash")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.evals, args.corpus, args.templates, args.manifest,
                      args.structure_tag, args.schema_model)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
