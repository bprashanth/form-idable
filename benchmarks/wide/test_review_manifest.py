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
                            ("r1_c0", "faint", 0.4),
                            ("r1_c1", 0, 0.95)], "primary")
        write_run(peer, [("r0_c0", "alternative", 0.99),
                         ("r0_c1", None, 0.99),
                         ("r1_c0", "faint", 0.9),
                         ("r1_c1", "0", 0.99)], "peer")
        manifest = review_manifest.from_template(primary, peer)
        assert review_manifest.validate(manifest) == []
        cells = {cell["id"]: cell for cell in manifest["cells"]}
        assert cells["r0_c0"]["presented_value"] == "literal"
        assert cells["r0_c0"]["status"] == "reader_disagreement"
        assert cells["r0_c0"]["alternatives"] == ["alternative"]
        assert cells["r0_c1"]["status"] == "reader_agreement"
        assert cells["r1_c0"]["status"] == "low_confidence"
        assert cells["r1_c1"]["status"] == "reader_agreement"
        assert manifest["summary"]["transcription_review_cells"] == 2

        cells["r0_c0"]["presented_value"] = "alternative"
        assert "overwrote primary value" in review_manifest.validate(manifest)[0]

        canonical_manifest = review_manifest.from_canonical({"pages": [{
            "page_number": 1,
            "metadata_fields": [{"id": "site", "label": "Site", "bbox": [0, 0, .2, .1],
                                 "xlsx_row": 1, "xlsx_column": 2, "value": "A",
                                 "status": "agreement", "confidence": .9}],
            "free_text_regions": [{"id": "note", "label": "Note", "bbox": [0, .9, .5, 1],
                                   "xlsx_row": 2, "xlsx_column": 2, "value": "faint",
                                   "status": "disagreement", "confidence": 0,
                                   "alternatives": ["paint"]}],
            "tables": [{"id": "table", "columns": [{"id": "value", "label": "Value"}],
                        "rows": [{"id": "1", "cells": [{
                            "column_id": "value", "bbox": [0, 0, 1, 1],
                            "xlsx_row": 4, "xlsx_column": 2,
                            "value": "01", "status": "structural_anomaly", "confidence": 0,
                            "structural_reason": "measurement after an empty descriptor",
                            "alternatives": ["0", "01"],
                        }]}]}],
        }]})
        attention = canonical_manifest["views"]["transcription_attention"]
        assert {item["presented_value"] for item in attention} == {"faint", "01"}
        table_attention = next(item for item in attention if item["presented_value"] == "01")
        assert table_attention["alternatives"] == ["0"]
        assert table_attention["bbox"] == [0, 0, 1, 1]
        assert table_attention["reason"] == "measurement after an empty descriptor"
        assert len(canonical_manifest["cells"]) == 3
        assert canonical_manifest["cells"][0]["xlsx_row"] == 1

        ecology_filtered = review_manifest.from_canonical({"pages": []}, {"findings": [
            {"severity": "info", "code": "context", "location": {"page": 1}},
            {"severity": "medium", "code": "review", "location": {"page": 1}},
        ]})
        assert [item["code"] for item in ecology_filtered["views"]["ecology_anomalies"]] == ["review"]


if __name__ == "__main__":
    main()
