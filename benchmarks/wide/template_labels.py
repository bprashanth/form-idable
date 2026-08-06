#!/usr/bin/env python3
"""Printed-label confirmation for a pixel-shortlisted blank template."""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

import fitz


TOKEN = re.compile(r"[a-z0-9]+")
STOP = {"a", "an", "and", "at", "by", "for", "in", "no", "of", "on",
        "or", "page", "the", "to", "with"}


def tokens(text):
    return {token for token in TOKEN.findall(str(text).casefold())
            if token not in STOP and (len(token) >= 2 or token.isdigit())}


def template_tokens(path: Path, page: int):
    document = fitz.open(path)
    text = document[page].get_text("text")
    document.close()
    return tokens(text)


def structure_tokens(raw):
    text = []
    for field in raw.get("metadata_fields") or []:
        text.extend((field.get("label"), field.get("id")))
    for table in raw.get("tables") or []:
        text.extend((table.get("title"), table.get("id")))
        for column in table.get("columns") or []:
            text.extend((column.get("parent"), column.get("label"), column.get("id")))
    for region in raw.get("free_text_regions") or []:
        text.extend((region.get("label"), region.get("id")))
    return tokens(" ".join(str(item) for item in text if item))


def idf(registry):
    count = Counter(token for values in registry.values() for token in values)
    total = len(registry)
    return {token: math.log((total + 1) / (frequency + 1)) + 1
            for token, frequency in count.items()}


def score(observed, candidate, weights):
    if not observed or not candidate:
        return 0.0
    intersection = observed & candidate
    observed_weight = sum(weights.get(token, 1.0) for token in observed)
    candidate_weight = sum(weights.get(token, 1.0) for token in candidate)
    overlap = sum(weights.get(token, 1.0) for token in intersection)
    observed_recall = overlap / observed_weight if observed_weight else 0.0
    candidate_recall = overlap / candidate_weight if candidate_weight else 0.0
    return round(0.75 * observed_recall + 0.25 * candidate_recall, 6)


def rank(observed, registry):
    weights = idf(registry)
    return sorted(((score(observed, values, weights), key)
                   for key, values in registry.items()),
                  key=lambda item: (-item[0], item[1]))


def confirm(candidate, raw_structure, registry, *, min_score=0.50, min_margin=0.10):
    observed = structure_tokens(raw_structure)
    ranking = rank(observed, registry)
    if not ranking:
        return {"accepted": False, "reason": "empty template registry"}
    top_score, top = ranking[0]
    runner_score = ranking[1][0] if len(ranking) > 1 else 0.0
    accepted = (top == candidate and top_score >= min_score
                and top_score - runner_score >= min_margin)
    return {
        "accepted": accepted, "candidate": candidate, "top": top,
        "score": top_score, "runner_up_score": runner_score,
        "margin": round(top_score - runner_score, 6),
        "observed_tokens": sorted(observed),
        "thresholds": {"min_score": min_score, "min_margin": min_margin},
        "reason": None if accepted else
        "printed labels did not uniquely confirm the pixel candidate",
    }


def load_registry(manifest: Path, templates: Path):
    registry = {}
    for item in json.loads(manifest.read_text()):
        page = int(item["page"]) - 1
        key = f"{item['template']}#page={page + 1}"
        registry[key] = template_tokens(templates / item["template"], page)
    return registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--templates", type=Path, required=True)
    parser.add_argument("--min-score", type=float, default=0.50)
    parser.add_argument("--min-margin", type=float, default=0.10)
    args = parser.parse_args()
    result = confirm(args.candidate, json.loads(args.structure.read_text()),
                     load_registry(args.manifest, args.templates),
                     min_score=args.min_score, min_margin=args.min_margin)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
