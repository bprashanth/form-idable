from ecology_review import (
    Record, canonical_records, edit_distance, kind_of, numeric_findings,
    taxon_query, taxonomy_findings,
)


class FakeGBIF:
    def match(self, name):
        if name == "Litsea floribnda":
            return ({"canonicalName": "Litsea floribunda", "confidence": 100},
                    "https://example.test/match")
        if name == "White-cheeked barbet":
            return ({"canonicalName": "Psilopogon viridis", "confidence": 100},
                    "https://example.test/match")
        return ({"confidence": 0}, "https://example.test/match")

    def nearby_count(self, *_args, **_kwargs):
        raise AssertionError("No coordinates were supplied")


def test_generic_kinds_and_distance():
    assert kind_of("Soil temperature °C") == "temperature"
    assert kind_of("Scientific species name") == "species"
    assert edit_distance("Litsea floribunda", "Litsea floribunda") == 0
    assert edit_distance("Litsea floribnda", "Litsea floribunda") == 1
    assert taxon_query("WHITE-CHEEKED BARBET\nPsilopogon viridis") == "Psilopogon viridis"
    assert taxon_query("White-cheeked barbet") == "White-cheeked barbet"


def test_hard_domains_and_robust_outlier_are_flags_not_edits():
    records = [Record({"row": str(i)}, "Soil temperature °C", value)
               for i, value in enumerate([21, 22, 20, 21, 23, 20, 22, 150])]
    records.append(Record({"row": "ph"}, "pH", 19))
    findings = numeric_findings(records)
    codes = [finding["code"] for finding in findings]
    assert codes.count("physical_domain_violation") == 2
    assert "within_form_numeric_outlier" in codes
    assert all(finding["proposed_value"] is None for finding in findings)


def test_taxonomy_queue_only_contains_a_defensible_specific_suggestion():
    records = [
        Record({"page": 1, "table": "trees"}, "Species", "Litsea floribnda"),
        Record({"page": 1, "table": "trees"}, "Species",
               "LITSEA TREE\nLitsea floribnda"),
        Record({"page": 1, "table": "trees"}, "Species", "Vast mal"),
        Record({"page": 1, "table": "trees"}, "Species", "White-cheeked barbet"),
        Record({"page": 1, "field": "legend", "kind": "free_text"},
               "Other species", "1) Polygonum\n2) Grasses"),
    ]
    findings = taxonomy_findings(records, FakeGBIF())
    assert [(item["code"], item["severity"], item["observed"])
            for item in findings] == [
        ("taxonomy_spelling_suggestion", "medium", "Litsea floribnda"),
        ("taxonomy_spelling_suggestion", "medium", "LITSEA TREE\nLitsea floribnda"),
        ("taxonomy_unmatched", "info", "Vast mal"),
    ]
    assert findings[0]["proposed_value"] == "Litsea floribunda"
    assert findings[1]["proposed_value"] == "LITSEA TREE Litsea floribunda"
    assert findings[2]["proposed_value"] is None


def test_free_text_records_are_marked_as_prose_not_single_taxa():
    records = canonical_records({"pages": [{
        "page_number": 1, "metadata_fields": [], "tables": [],
        "free_text_regions": [{"id": "legend", "label": "Other species",
                               "value": "1) Polygonum\n2) Grasses"}],
    }]})
    assert records[0].location["kind"] == "free_text"
