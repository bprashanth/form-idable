def infer_types(headers: list, cheatsheet: dict) -> dict:
    """
    Fuzzy-match column headers against cheatsheet keywords.
    Returns {col_name: {type, confidence, matched_keyword}} for matched headers only.
    """
    type_map = {}
    for header in headers:
        if not header:
            continue
        normalized = str(header).lower().strip()

        for type_name, type_config in cheatsheet["types"].items():
            if header in type_config.get("ignore_headers", []):
                break

            for keyword in type_config["keywords"]:
                kw = keyword.lower()
                if kw in normalized or normalized in kw:
                    type_map[str(header)] = {
                        "type": type_name,
                        "confidence": "high" if kw == normalized else "medium",
                        "matched_keyword": keyword,
                    }
                    break

            if str(header) in type_map:
                break

    return type_map
