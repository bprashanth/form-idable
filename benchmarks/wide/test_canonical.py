#!/usr/bin/env python3
"""Primary-reader invariants for canonical disagreement resolution."""
import tempfile
from pathlib import Path

import canonical
import openpyxl


def resolve(readings):
    item = {"readings": readings}
    canonical._resolve_item(item)
    return item


def main():
    blank_primary = resolve([
        {"model": "primary", "value": None, "confidence": 0.9},
        {"model": "peer", "value": "4", "confidence": 0.9},
    ])
    assert blank_primary["status"] == "disagreement"
    assert blank_primary["value"] is None
    assert blank_primary["alternatives"] == ["4"]

    literal_primary = resolve([
        {"model": "primary", "value": "0", "confidence": 0.8},
        {"model": "peer", "value": "O", "confidence": 0.9},
    ])
    assert literal_primary["value"] == "0"
    assert literal_primary["alternatives"] == ["O"]

    outvoted_primary = resolve([
        {"model": "primary", "value": "A", "confidence": 0.7},
        {"model": "peer", "value": "B", "confidence": 0.9},
        {"model": "reread", "value": "B", "confidence": 0.95},
    ])
    assert outvoted_primary["status"] == "majority_after_reread"
    assert outvoted_primary["value"] == "A"
    assert outvoted_primary["alternatives"] == ["B"]

    page = canonical.normalize_structure({
        "metadata_fields": [], "tables": [],
        "free_text_regions": [{"id": "margin_note", "label": "margin note",
                               "bbox": [0.1, 0.1, 0.4, 0.2]}],
    }, 1)
    canonical.attach_extraction(page, {"metadata": [], "tables": [], "free_text": [
        {"region_id": "margin_note", "value": "do not drop me", "confidence": .9},
    ]}, "primary")
    canonical.attach_extraction(page, {"metadata": [], "tables": [], "free_text": [
        {"region_id": "margin_note", "value": "do not drop me", "confidence": .95},
    ]}, "peer")
    canonical.resolve({"pages": [page]})
    assert page["free_text_regions"][0]["value"] == "do not drop me"
    assert page["free_text_regions"][0]["status"] == "agreement"

    peer_only = {"models": ["primary", "peer"], "pages": [{
        "page_number": 1, "metadata_fields": [], "free_text_regions": [],
        "tables": [{"id": "t", "columns": [{"id": "v"}], "rows": [{
            "id": "peer-row", "bbox": [0, 0, 1, .1], "cells": [{
                "column_id": "v", "bbox": [0, 0, 1, .1], "readings": [{
                    "model": "peer", "value": "found", "confidence": .9,
                    "illegible": False,
                }],
            }],
        }]}],
    }]}
    canonical.resolve(peer_only)
    peer_cell = peer_only["pages"][0]["tables"][0]["rows"][0]["cells"][0]
    assert peer_cell["value"] is None
    assert peer_cell["status"] == "disagreement"
    assert peer_cell["alternatives"] == ["found"]
    assert [reading["model"] for reading in peer_cell["readings"]] == ["primary", "peer"]

    aligned = [{"id": "C 21", "bbox": [0, .2, 1, .22], "cells": [{
        "readings": [{"model": "primary"}],
    }]}]
    assert canonical._match_row(aligned, "c21", [0, .201, 1, .221], "peer") is aligned[0]
    assert canonical._match_row(aligned, "C 22", [0, .23, 1, .25], "peer") is None
    assert canonical._match_row(aligned, "C 21", [0, .2, 1, .22], "primary") is None
    assert canonical.row_bbox([.66, .158, .915, .685]) == [.158, .66, .915, .685]
    assert canonical.row_bbox([.173, .082, .194, .884]) == [.082, .173, .884, .194]
    assert canonical.row_bbox([.075, .665, .92, .688]) == [.075, .665, .92, .688]

    with tempfile.TemporaryDirectory() as temporary:
        document = {"pages": [{"page_number": 1, "metadata_fields": [], "tables": [{
            "id": "t", "title": "", "columns": [
                {"id": "red", "label": "Red", "parent": None},
                {"id": "orange", "label": "Orange", "parent": None}],
            "rows": [{"id": "1", "cells": [
                {"column_id": "red", "value": "A", "status": "disagreement",
                 "confidence": 0, "alternatives": ["B"],
                 "ecology_flags": [{"severity": "medium"}]},
                {"column_id": "orange", "value": "150", "status": "agreement",
                 "confidence": 1, "alternatives": [],
                 "ecology_flags": [{"severity": "medium"}]}]}]}]}]}
        path = Path(temporary) / "colors.xlsx"
        canonical.write_xlsx(document, path)
        sheet = openpyxl.load_workbook(path)["page1"]
        assert sheet["A2"].fill.fgColor.rgb.endswith("F4CCCC")
        assert sheet["B2"].fill.fgColor.rgb.endswith("FCE4D6")

        notes = Path(temporary) / "notes.xlsx"
        canonical.write_xlsx({"pages": [page]}, notes)
        note_sheet = openpyxl.load_workbook(notes)["page1"]
        assert note_sheet["A1"].value == "Note"
        assert note_sheet["B1"].value == "do not drop me"


if __name__ == "__main__":
    main()
