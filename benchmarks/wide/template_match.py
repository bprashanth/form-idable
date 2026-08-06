#!/usr/bin/env python3
"""Conservative blank-template matcher with an explicit abstain outcome.

The matcher asks whether printed pixels from a candidate blank are supported by
the filled page. Handwriting is treated as extra ink, not evidence against a
match. It is intentionally only one channel: production routing should also
confirm printed-label overlap from the generic structure pass.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageFilter


@dataclass(frozen=True)
class TemplatePage:
    template: str
    page: int  # zero based

    @property
    def key(self) -> str:
        return f"{self.template}#page={self.page + 1}"


def render(path: Path, page: int, max_dim: int = 512) -> Image.Image:
    document = fitz.open(path)
    source = document[page]
    scale = max_dim / max(source.rect.width, source.rect.height)
    pixmap = source.get_pixmap(matrix=fitz.Matrix(scale, scale),
                               colorspace=fitz.csGRAY, alpha=False)
    image = Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)
    document.close()
    return image


def pixel_support(filled: Image.Image, blank: Image.Image) -> float:
    """Score blank-print recall plus filled-ink support, tolerant by two pixels."""
    filled_aspect = filled.width / filled.height
    blank_aspect = blank.width / blank.height
    if min(filled_aspect, blank_aspect) / max(filled_aspect, blank_aspect) < 0.75:
        return 0.0
    candidate = filled.resize(blank.size, Image.Resampling.BILINEAR)
    filled_mask = np.asarray(candidate) < 205
    blank_mask = np.asarray(blank) < 205
    filled_dilated = np.asarray(Image.fromarray((filled_mask * 255).astype("uint8"))
                                 .filter(ImageFilter.MaxFilter(5))) > 0
    blank_dilated = np.asarray(Image.fromarray((blank_mask * 255).astype("uint8"))
                                .filter(ImageFilter.MaxFilter(5))) > 0
    printed_recall = (blank_mask & filled_dilated).sum() / max(1, blank_mask.sum())
    filled_support = (filled_mask & blank_dilated).sum() / max(1, filled_mask.sum())
    return round(float(0.75 * printed_recall + 0.25 * filled_support), 6)


def rank(filled: Image.Image, registry: dict[TemplatePage, Image.Image]):
    return sorted(((pixel_support(filled, blank), descriptor)
                   for descriptor, blank in registry.items()),
                  key=lambda item: (-item[0], item[1].key))


def verdict(ranking, *, min_score=0.50, min_margin=0.02):
    if not ranking:
        return {"status": "unknown_template", "reason": "empty registry"}
    score, descriptor = ranking[0]
    runner_up = ranking[1][0] if len(ranking) > 1 else 0.0
    margin = score - runner_up
    accepted = score >= min_score and margin >= min_margin
    return {
        "status": "known_template" if accepted else "unknown_template",
        "template": descriptor.template if accepted else None,
        "page": descriptor.page + 1 if accepted else None,
        "candidate": descriptor.key,
        "score": round(score, 6),
        "runner_up_score": round(runner_up, 6),
        "margin": round(margin, 6),
        "thresholds": {"min_score": min_score, "min_margin": min_margin},
        "reason": None if accepted else "pixel match did not clear both safety thresholds",
    }


def corpus_registry(corpus: Path, templates: Path):
    descriptors = set()
    for truth_path in corpus.glob("*/ground_truth.json"):
        truth = json.loads(truth_path.read_text())
        descriptors.add(TemplatePage(truth["template"], int(truth["page"]) - 1))
    return {descriptor: render(templates / descriptor.template, descriptor.page)
            for descriptor in sorted(descriptors, key=lambda item: item.key)}


def _metrics(rows, split, min_score, min_margin):
    selected = [row for row in rows if row["split"] == split]
    accepted = [row for row in selected
                if row["top_score"] >= min_score and row["margin"] >= min_margin]
    correct = sum(row["correct_top1"] for row in accepted)
    return {
        "forms": len(selected), "accepted": len(accepted), "correct": correct,
        "wrong_routes": len(accepted) - correct,
        "coverage": round(len(accepted) / len(selected), 4) if selected else None,
        "accepted_precision": round(correct / len(accepted), 4) if accepted else None,
    }


def evaluate(corpus: Path, templates: Path, min_score=0.50, min_margin=0.02):
    registry = corpus_registry(corpus, templates)
    rows = []
    for form_dir in sorted(path for path in corpus.iterdir()
                           if (path / "input.pdf").exists()):
        truth = json.loads((form_dir / "ground_truth.json").read_text())
        expected = TemplatePage(truth["template"], int(truth["page"]) - 1)
        ranking = rank(render(form_dir / "input.pdf", 0), registry)
        expected_rank = next(index + 1 for index, (_, descriptor) in enumerate(ranking)
                             if descriptor == expected)
        top_score, top = ranking[0]
        runner_up = ranking[1][0] if len(ranking) > 1 else 0.0
        rows.append({
            "form": form_dir.name,
            "split": form_dir.name.split("__", 1)[0],
            "variant": form_dir.name.rsplit("__v", 1)[-1],
            "expected": expected.key,
            "top": top.key,
            "expected_rank": expected_rank,
            "correct_top1": top == expected,
            "top_score": round(top_score, 6),
            "margin": round(top_score - runner_up, 6),
        })
    policies = []
    for score in (0.40, 0.45, 0.50, 0.55, 0.60, 0.70):
        for margin in (0.005, 0.01, 0.02, 0.03, 0.05, 0.10):
            policies.append({
                "min_score": score, "min_margin": margin,
                "dev": _metrics(rows, "dev", score, margin),
                "test": _metrics(rows, "test", score, margin),
            })
    return {
        "version": "formidable-template-match-eval-v1",
        "policy": {
            "role": "routing candidate only; printed-label confirmation still required",
            "min_score": min_score, "min_margin": min_margin,
        },
        "registry_pages": len(registry),
        "top1": {
            "all": sum(row["correct_top1"] for row in rows),
            "forms": len(rows),
            "top2": sum(row["expected_rank"] <= 2 for row in rows),
        },
        "selected_policy": {
            "dev": _metrics(rows, "dev", min_score, min_margin),
            "test": _metrics(rows, "test", min_score, min_margin),
        },
        "policy_grid": policies,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--templates", type=Path, required=True)
    parser.add_argument("--manifest", type=Path,
                        help="JSON list of {template,page}; page is 1-based")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-score", type=float, default=0.50)
    parser.add_argument("--min-margin", type=float, default=0.02)
    args = parser.parse_args()
    if args.corpus:
        report = evaluate(args.corpus, args.templates, args.min_score, args.min_margin)
    else:
        if not args.input or not args.manifest:
            parser.error("single-page matching requires input and --manifest")
        manifest = json.loads(args.manifest.read_text())
        registry = {}
        for item in manifest:
            descriptor = TemplatePage(item["template"], int(item["page"]) - 1)
            registry[descriptor] = render(args.templates / descriptor.template, descriptor.page)
        report = verdict(rank(render(args.input, 0), registry),
                         min_score=args.min_score, min_margin=args.min_margin)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
