#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import review_manifest


def write_run(directory, values, model):
    directory.mkdir()
    payload = {"cells": [
        {"cell_id": cell_id, "value": value, "confidence": confidence,
         "evidence": "pixels"}
        for cell_id, value, confidence in values
    ]}
    (directory / "batch_000.json").write_text(json.dumps(payload))
    (directory / "batch_000.targets.json").write_text(json.dumps([
        {"cell_id": cell_id, "bbox_1000": [0, 0, 100, 100], "context": "field"}
        for cell_id, _value, _confidence in values
    ]))
    (directory / "run.json").write_text(json.dumps(
        {"tag": model, "model": model, "mode": "page", "cost_usd": 0.1,
         "latency_s": 1.0}))


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        primary, peer = root / "primary", root / "peer"
        write_run(primary, [("r0_c0", "literal", 0.9),
                            ("r0_c1", None, 0.95),
                            ("r1_c0", "faint", 0.4)], "primary")
        write_run(peer, [("r0_c0", "alternative", 0.99),
                         ("r0_c1", None, 0.99),
                         ("r1_c0", "faint", 0.9)], "peer")
        manifest = review_manifest.from_template(primary, peer)
        assert review_manifest.validate(manifest) == []
        cells = {cell["id"]: cell for cell in manifest["cells"]}
        assert cells["r0_c0"]["presented_value"] == "literal"
        assert cells["r0_c0"]["status"] == "reader_disagreement"
        assert cells["r0_c0"]["alternatives"] == ["alternative"]
        assert cells["r0_c1"]["status"] == "reader_agreement"
        assert cells["r1_c0"]["status"] == "low_confidence"
        assert manifest["summary"]["transcription_review_cells"] == 2

        cells["r0_c0"]["presented_value"] = "alternative"
        assert "overwrote primary value" in review_manifest.validate(manifest)[0]


if __name__ == "__main__":
    main()
