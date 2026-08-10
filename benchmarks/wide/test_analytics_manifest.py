#!/usr/bin/env python3
import analytics_manifest
import ecology_review


def main():
    rows = []
    for index, value in enumerate((1, 2, 3, 4, 5, 6, 7, 100), 1):
        rows.append({"id": str(index), "cells": [
            {"column_id": "height", "value": str(value), "status": "agreement"},
            {"column_id": "state", "value": "Y" if index % 2 else "N",
             "status": "disagreement" if index == 2 else "agreement"},
        ]})
    document = {"pages": [{"page_number": 1,
        "metadata_fields": [{"value": "Plot 1", "status": "agreement"}],
        "free_text_regions": [{"value": "margin note", "status": "disagreement"}],
        "tables": [{"id": "trees", "title": "Trees",
        "columns": [{"id": "height", "label": "Height"}, {"id": "state", "label": "State"}],
        "rows": rows}]}]}
    result = analytics_manifest.build(document, {"findings": [
        {"code": "outlier", "severity": "medium"}]})
    assert result["version"] == "formidable-analytics-v1"
    assert result["summary"] == {"pages": 1, "cells": 18, "filled": 18, "blank": 0,
                                 "completeness": 1.0, "disagreements": 2,
                                 "ecology_findings": 1, "ecology_information": 0}
    numeric = next(chart for chart in result["charts"] if chart["type"] == "numeric")
    assert numeric["median"] == 4.5 and numeric["max"] == 100
    categorical = next(chart for chart in result["charts"] if chart["type"] == "categorical")
    assert categorical["values"] == [{"label": "Y", "count": 4}, {"label": "N", "count": 4}]

    coordinates = ecology_review.location_coordinates([
        ecology_review.Record({"page": 1}, "GPS coordinates", "10.30217, 76.84301"),
    ])
    assert coordinates == (10.30217, 76.84301)
    assert ecology_review.location_coordinates([
        ecology_review.Record({"page": 1}, "Latitude", "999"),
    ]) == (None, None)


if __name__ == "__main__":
    main()
