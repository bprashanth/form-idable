from pathlib import Path

from PIL import Image, ImageDraw

import canonical
import structured_pipeline


def test_geometry_restores_blank_rows_without_reducing_model_count(tmp_path: Path):
    image = Image.new("L", (1000, 1000), "white")
    draw = ImageDraw.Draw(image)
    # One header row plus 12 physical data rows.
    for index in range(14):
        y = 200 + index * 30
        draw.line((100, y, 900, y), fill=40, width=2)
    for x in (100, 300, 600, 900):
        draw.line((x, 200, x, 590), fill=40, width=2)
    path = tmp_path / "page.png"
    image.save(path)
    raw = {"tables": [{
        "id": "observations", "bbox": [0.1, 0.2, 0.9, 0.59],
        "estimated_rows": 4,
        "columns": [{"id": "species", "parent": None}],
    }, {
        "id": "model_knows_more", "bbox": [0.1, 0.2, 0.9, 0.59],
        "estimated_rows": 15,
        "columns": [{"id": "species", "parent": None}],
    }]}

    changes = structured_pipeline.refine_structure_geometry(raw, path)

    assert raw["tables"][0]["estimated_rows"] == 12
    assert raw["tables"][1]["estimated_rows"] == 15
    assert changes == [{
        "table_id": "observations", "declared_rows": 4,
        "physical_rows": 12, "rules": 14,
    }]

    page = canonical.normalize_structure({
        "metadata_fields": [], "free_text_regions": [],
        "tables": [raw["tables"][0]],
    }, 1)
    table = page["tables"][0]
    # Simulate both readers returning only the two occupied leading rows.
    for model in ("primary", "peer"):
        canonical.attach_extraction(page, {"tables": [{
            "table_id": "observations", "rows": [
                {"row_id": "1", "bbox": [0.1, 0.23, 0.9, 0.25],
                 "values": ["1"], "confidences": [1], "illegible_columns": []},
                {"row_id": "2", "bbox": [0.1, 0.26, 0.9, 0.28],
                 "values": ["2"], "confidences": [1], "illegible_columns": []},
            ],
        }]}, model)
    document = canonical.new_document("test.pdf", [page], ["primary", "peer"])
    canonical.resolve(document)

    assert len(table["rows"]) == 12
    assert table["rows"][-1]["cells"][0]["value"] == "12"
    assert table["rows"][-1]["cells"][0]["status"] == "agreement"


def test_tall_table_bands_repeat_header_and_overlap():
    table = {
        "bbox": [0.1, 0.2, 0.9, 0.8], "estimated_rows": 49,
        "columns": [{"parent": "Measurements"}, {"parent": "Measurements"}],
    }
    bands = structured_pipeline._table_band_boxes(table)

    assert len(bands) == 5
    assert all(header == bands[0][0] for header, _data in bands)
    # Two header intervals precede 49 equal physical data intervals.
    expected_data_top = 0.2 + 2 * (0.6 / 51)
    assert abs(bands[0][1][1] - expected_data_top) < 1e-9
    # 12-row bands advance by 11 rows, producing one-row overlap.
    row_height = 0.6 / 51
    assert abs(bands[1][1][1] - (expected_data_top + 11 * row_height)) < 1e-9
    assert abs(bands[-1][1][3] - 0.8) < 1e-9
