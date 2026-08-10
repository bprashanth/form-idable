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

    key_columns = [
        {"value_kind": "categorical_code"}, {"value_kind": "integer"},
        {"value_kind": "integer"}, {"value_kind": "identifier"},
        {"value_kind": "categorical_code"}, {"value_kind": "species"},
    ]
    assert canonical._row_key_fingerprint(
        key_columns, ["MAN", "9", "6", "85", "A", "PALELL"]
    ) == canonical._row_key_fingerprint(
        key_columns, ["MAN", "9", "6", "85A", None, "PALELL"]
    )
    keyed_row = {"id": "1", "bbox": [0, .1, 1, .12], "key_fingerprint": "man9685a",
                 "cells": [{"readings": [{"model": "primary"}]}]}
    assert canonical._match_row(
        [keyed_row], "y_0.8", [0, .8, 1, .82], "peer", "man9685a"
    ) is keyed_row

    short_rows = [{"values": ["MAN", "9", "6", f"{number}A", "PALELL", "5.2"]}
                  for number in range(85, 93)]
    assert canonical._omitted_compound_identifier_column(
        key_columns + [{"value_kind": "decimal"}], short_rows
    ) == (3, 4)

    shifted_page = canonical.normalize_structure({
        "metadata_fields": [], "free_text_regions": [], "tables": [{
            "id": "trees", "bbox": [0, 0, 1, 1], "columns": [
                {"id": f"c{i}", "label": f"c{i}", "value_kind": column["value_kind"],
                 "x0": i / 7, "x1": (i + 1) / 7}
                for i, column in enumerate(key_columns + [{"value_kind": "decimal"}])
            ],
        }],
    }, 1)
    canonical.attach_extraction(shifted_page, {"tables": [{
        "table_id": "trees", "rows": [dict(
            row, row_id=str(index), bbox=[0, index / 20, 1, (index + 1) / 20],
            confidences=[.9] * 6)
            for index, row in enumerate(short_rows, 1)]
    }]}, "peer")
    first_shifted = shifted_page["tables"][0]["rows"][0]
    assert [cell["readings"][0]["value"] for cell in first_shifted["cells"]] == [
        "MAN", "9", "6", "85", "A", "PALELL", "5.2"]
    assert first_shifted["key_fingerprint"] == "man9685a"

    sparse_table = {"columns": [
        {"id": "species", "value_kind": "species"},
        {"id": "height", "value_kind": "decimal"},
    ], "rows": [{"cells": [
        {"column_id": "species", "value": None, "status": "blank_or_illegible"},
        {"column_id": "height", "value": "16.0", "status": "agreement"},
    ]}]}
    canonical._flag_sparse_structural_rows(sparse_table)
    assert sparse_table["rows"][0]["cells"][1]["status"] == "structural_anomaly"
    assert "literal value retained" in sparse_table["rows"][0]["cells"][1]["structural_reason"]

    compound_table = {"columns": [
        {"id": "plant", "label": "PlantId", "value_kind": "identifier"},
        {"id": "stem", "label": "StemId", "value_kind": "categorical_code"},
    ], "rows": []}
    for number in range(1, 9):
        compound_table["rows"].append({"cells": [
            {"column_id": "plant", "bbox": [0, 0, .5, 1], "value": f"{number}A",
             "readings": [{"model": "primary", "value": f"{number}A", "confidence": .9},
                          {"model": "peer", "value": f"{number}A", "confidence": .9}]},
            {"column_id": "stem", "bbox": [.5, 0, 1, 1], "value": None,
             "readings": [{"model": "primary", "value": None, "confidence": .9},
                          {"model": "peer", "value": None, "confidence": .9}]},
        ]})
    canonical._repair_compound_identifier_columns(compound_table)
    assert compound_table["rows"][0]["cells"][0]["value"] == "1"
    assert compound_table["rows"][0]["cells"][1]["value"] == "A"
    assert "model-wide empty-column check" in compound_table["rows"][0]["cells"][1]["layout_repair"]

    # A merged peer is normalized against an already-correct primary instead
    # of creating two false disagreements.
    for row in compound_table["rows"]:
        source, target = row["cells"]
        source["readings"][0]["value"] = source["value"]
        target["readings"][0]["value"] = "A"
        source["readings"][1]["value"] = f"{source['value']}A"
        target["readings"][1]["value"] = None
        canonical._resolve_item(source)
        canonical._resolve_item(target)
    canonical._repair_compound_identifier_columns(compound_table)
    assert compound_table["rows"][0]["cells"][0]["status"] == "agreement"
    assert compound_table["rows"][0]["cells"][1]["status"] == "agreement"

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
