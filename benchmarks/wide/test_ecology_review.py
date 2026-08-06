from ecology_review import Record, edit_distance, kind_of, numeric_findings


def test_generic_kinds_and_distance():
    assert kind_of("Soil temperature °C") == "temperature"
    assert kind_of("Scientific species name") == "species"
    assert edit_distance("Litsea floribunda", "Litsea floribunda") == 0
    assert edit_distance("Litsea floribnda", "Litsea floribunda") == 1


def test_hard_domains_and_robust_outlier_are_flags_not_edits():
    records = [Record({"row": str(i)}, "Soil temperature °C", value)
               for i, value in enumerate([21, 22, 20, 21, 23, 20, 22, 150])]
    records.append(Record({"row": "ph"}, "pH", 19))
    findings = numeric_findings(records)
    codes = [finding["code"] for finding in findings]
    assert codes.count("physical_domain_violation") == 2
    assert "within_form_numeric_outlier" in codes
    assert all(finding["proposed_value"] is None for finding in findings)
