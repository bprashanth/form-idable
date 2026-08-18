import unittest

import unified_pipeline


class UnifiedPipelineTest(unittest.TestCase):
    def test_split_expands_compact_review_flags(self):
        raw = {
            "page": 1,
            "metadata_fields": [{"id": "date", "label": "Date", "bbox": [0, 0, .2, .1],
                                 "value": "1/1", "needs_review": False, "illegible": False}],
            "tables": [{
                "id": "t", "title": "Table", "bbox": [0, .1, 1, .9],
                "estimated_rows": 10,
                "columns": [
                    {"id": "a", "label": "A", "parent": None, "value_kind": "integer",
                     "x0": 0, "x1": .5},
                    {"id": "b", "label": "B", "parent": None, "value_kind": "integer",
                     "x0": .5, "x1": 1},
                ],
                "rows": [{"row_id": "1", "y_center": .25, "values": ["1", None],
                          "review_columns": [1], "illegible_columns": [1]}],
            }],
            "free_text_regions": [],
        }
        structure, extraction = unified_pipeline.split(raw)
        self.assertEqual(structure["tables"][0]["estimated_rows"], 10)
        self.assertEqual(extraction["tables"][0]["rows"][0]["confidences"], [.95, .5])
        self.assertAlmostEqual(extraction["tables"][0]["rows"][0]["bbox"][1], .21363636)

    def test_missing_targeted_peer_is_not_silent(self):
        item = {"id": "date", "label": "Date", "bbox": [0, 0, .2, .1],
                "readings": [{"model": "primary", "value": "1/1", "confidence": .5,
                              "illegible": False, "bbox": [0, 0, .2, .1]}],
                "value": "1/1", "status": "agreement", "confidence": .5,
                "alternatives": []}
        page = {"metadata_fields": [item], "free_text_regions": [], "tables": []}
        target = {"target_id": "metadata:date", "bbox": item["bbox"]}
        audit = unified_pipeline.apply_peer(page, [target], {"readings": []}, "peer")
        self.assertEqual(audit["missing"], 1)
        self.assertEqual(item["status"], "disagreement")

    def test_split_repairs_only_missing_trailing_value(self):
        raw = {
            "page": 1, "metadata_fields": [], "free_text_regions": [],
            "tables": [{"id": "t", "title": "T", "bbox": [0, 0, 1, 1],
                        "estimated_rows": 1,
                        "columns": [{"id": "a", "label": "A", "parent": None,
                                     "value_kind": "integer", "x0": 0, "x1": .5},
                                    {"id": "b", "label": "B", "parent": None,
                                     "value_kind": "integer", "x0": .5, "x1": 1}],
                        "rows": [{"row_id": "1", "y_center": .5, "values": ["1"],
                                  "review_columns": [], "illegible_columns": []}]}],
        }
        _structure, extraction = unified_pipeline.split(raw)
        row = raw["tables"][0]["rows"][0]
        self.assertEqual(row["values"], ["1", None])
        self.assertEqual(row["review_columns"], [1])
        self.assertEqual(extraction["tables"][0]["rows"][0]["illegible_columns"], [1])

    def test_split_rejects_overlong_row(self):
        raw = {
            "page": 1, "metadata_fields": [], "free_text_regions": [],
            "tables": [{"id": "t", "title": "T", "bbox": [0, 0, 1, 1],
                        "estimated_rows": 1,
                        "columns": [{"id": "a", "label": "A", "parent": None,
                                     "value_kind": "integer", "x0": 0, "x1": 1}],
                        "rows": [{"row_id": "1", "y_center": .5,
                                  "values": ["1", "2"], "review_columns": [],
                                  "illegible_columns": []}]}],
        }
        with self.assertRaisesRegex(ValueError, "2 values for 1 columns"):
            unified_pipeline.split(raw)


if __name__ == "__main__":
    unittest.main()
