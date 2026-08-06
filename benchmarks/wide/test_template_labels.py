#!/usr/bin/env python3
import template_labels


def main():
    registry = {
        "bird.pdf#page=1": template_labels.tokens(
            "grassland bird point count species alpha code heard seen comments"),
        "soil.pdf#page=1": template_labels.tokens(
            "soil submission sample depth texture ph field identifier"),
        "tree.pdf#page=1": template_labels.tokens(
            "tree plot species gbh phenology leaf flower fruit"),
    }
    raw = {
        "metadata_fields": [{"id": "survey", "label": "Grassland survey"}],
        "tables": [{"id": "birds", "title": "Bird point count",
                    "columns": [{"id": "species", "label": "Species alpha code",
                                 "parent": None},
                                {"id": "heard", "label": "Heard", "parent": None},
                                {"id": "comments", "label": "Comments", "parent": None}]}],
        "free_text_regions": [],
    }
    result = template_labels.confirm("bird.pdf#page=1", raw, registry,
                                     min_score=0.5, min_margin=0.1)
    assert result["accepted"]
    assert result["top"] == "bird.pdf#page=1"
    wrong_candidate = template_labels.confirm("soil.pdf#page=1", raw, registry,
                                              min_score=0.5, min_margin=0.1)
    assert not wrong_candidate["accepted"]


if __name__ == "__main__":
    main()
