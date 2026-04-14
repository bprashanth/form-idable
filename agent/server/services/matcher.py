import csv

from rapidfuzz import fuzz, process

from config import SPECIES_CSV_PATH


_FIELD_LABELS = {
    "Species name Abbr": "abbr",
    "Species name expanded": "expanded",
    "Toda name": "toda_name",
}


def _load_choices() -> list:
    """Returns list of {key, display, expanded, field} across all three DB columns."""
    choices = []
    with open(SPECIES_CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            expanded = row["Species name expanded"].strip()
            for col, field in _FIELD_LABELS.items():
                val = row[col].strip()
                if val and val != "NA":
                    choices.append({
                        "key": val.lower(),
                        "display": val,
                        "expanded": expanded,
                        "field": field,
                    })
    return choices


def propose_species_corrections(unique_values: list) -> list:
    """
    Fuzzy-match each value against the species DB.
    Returns [{original, corrected, matched_display, match_field, score}]
    sorted by score descending. corrected is None when no match found.
    """
    choices = _load_choices()
    keys = [c["key"] for c in choices]
    proposals = []
    for v in unique_values:
        match = process.extractOne(v.lower(), keys, scorer=fuzz.ratio)
        if match:
            _, score, idx = match
            entry = choices[idx]
            proposals.append({
                "original": v,
                "corrected": entry["expanded"],
                "matched_display": entry["display"],
                "match_field": entry["field"],
                "score": round(score, 1),
            })
        else:
            proposals.append({
                "original": v,
                "corrected": None,
                "matched_display": None,
                "match_field": None,
                "score": 0.0,
            })

    proposals.sort(key=lambda x: -x["score"])
    return proposals
