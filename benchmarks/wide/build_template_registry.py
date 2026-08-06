#!/usr/bin/env python3
"""Build an enrolled blank-template page manifest from audited corpus truth."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    entries = {}
    for path in args.corpus.glob("*/ground_truth.json"):
        truth = json.loads(path.read_text())
        key = (truth["template"], int(truth["page"]))
        entries[key] = {"template": key[0], "page": key[1]}
    manifest = sorted(entries.values(), key=lambda item: (item["template"], item["page"]))
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "template_pages": len(manifest)}, indent=2))


if __name__ == "__main__":
    main()
