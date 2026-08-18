#!/usr/bin/env python3
"""Compact unified extraction with a budgeted independent targeted peer."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
WIDE = HERE.parent / "wide"
sys.path.insert(0, str(WIDE))
import canonical  # noqa: E402
import structured_pipeline  # noqa: E402

from openai_responses import responses_json  # noqa: E402


COLUMN_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"}, "label": {"type": "string"},
        "parent": {"type": ["string", "null"]}, "value_kind": {"type": "string"},
        "x0": {"type": "number"}, "x1": {"type": "number"},
    },
    "required": ["id", "label", "parent", "value_kind", "x0", "x1"],
    "additionalProperties": False,
}

ROW_SCHEMA = {
    "type": "object",
    "properties": {
        "row_id": {"type": "string"},
        "y_center": {"type": "number"},
        "values": {"type": "array", "items": {"type": ["string", "null"]}},
        "review_columns": {"type": "array", "items": {"type": "integer"}},
        "illegible_columns": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["row_id", "y_center", "values", "review_columns", "illegible_columns"],
    "additionalProperties": False,
}

UNIFIED_SCHEMA = {
    "type": "object",
    "properties": {
        "page": {"type": "integer"},
        "metadata_fields": {"type": "array", "items": {
            "type": "object", "properties": {
                "id": {"type": "string"}, "label": {"type": "string"},
                "bbox": {"type": "array", "items": {"type": "number"},
                         "minItems": 4, "maxItems": 4},
                "value": {"type": ["string", "null"]},
                "needs_review": {"type": "boolean"}, "illegible": {"type": "boolean"},
            },
            "required": ["id", "label", "bbox", "value", "needs_review", "illegible"],
            "additionalProperties": False,
        }},
        "tables": {"type": "array", "items": {
            "type": "object", "properties": {
                "id": {"type": "string"}, "title": {"type": "string"},
                "bbox": {"type": "array", "items": {"type": "number"},
                         "minItems": 4, "maxItems": 4},
                "estimated_rows": {"type": "integer"},
                "columns": {"type": "array", "items": COLUMN_SCHEMA},
                "rows": {"type": "array", "items": ROW_SCHEMA},
            },
            "required": ["id", "title", "bbox", "estimated_rows", "columns", "rows"],
            "additionalProperties": False,
        }},
        "free_text_regions": {"type": "array", "items": {
            "type": "object", "properties": {
                "id": {"type": "string"}, "label": {"type": "string"},
                "bbox": {"type": "array", "items": {"type": "number"},
                         "minItems": 4, "maxItems": 4},
                "value": {"type": ["string", "null"]},
                "needs_review": {"type": "boolean"}, "illegible": {"type": "boolean"},
            },
            "required": ["id", "label", "bbox", "value", "needs_review", "illegible"],
            "additionalProperties": False,
        }},
    },
    "required": ["page", "metadata_fields", "tables", "free_text_regions"],
    "additionalProperties": False,
}

TARGET_SCHEMA = {
    "type": "object",
    "properties": {
        "readings": {"type": "array", "items": {
            "type": "object", "properties": {
                "target_id": {"type": "string"},
                "value": {"type": ["string", "null"]},
                "confidence": {"type": "number"}, "illegible": {"type": "boolean"},
            },
            "required": ["target_id", "value", "confidence", "illegible"],
            "additionalProperties": False,
        }},
    }, "required": ["readings"], "additionalProperties": False,
}

UNIFIED_PROMPT = """You are a literal visual paper-form digitizer. The images are
one full-page overview followed by four overlapping high-resolution quadrants of
that same page. In ONE response, preserve the generic printed structure and
transcribe the handwriting.

Return every metadata field, table/list, physical table column, spanning header
level, and free-text region. Coordinates are full-page [x0,y0,x1,y1] fractions.
estimated_rows is every physically visible data row including unused trailing
blank rows, but `rows` contains only rows with recorded ink. `y_center` is the
row's vertical page center from 0 to 1. Values arrays must
exactly match column order and length. Preserve printed row IDs, gaps, dots as
zero, tallies as counts, check/tick marks as X, and strike-through as blank.

Never fill a blank from a neighbour or common column value. If ink is unreadable,
use null and mark the column illegible. `review_columns` includes every zero-based
column whose visual reading is uncertain enough to merit a second look, including
every illegible column. Use visible legends but no outside domain knowledge. A row
Check the first and last recorded rows before returning. Keep JSON compact; do
not explain it.
"""

TARGET_PROMPT = """You are an independent literal visual peer. Inspect the page
overview and only the supplied risky targets. Return exactly one reading for each
target_id. Use null for blank; use null plus illegible=true for unreadable ink.
Do not copy neighbours, correct ecology, or infer missing values. The target bbox
is a full-page [x0,y0,x1,y1] fraction.

TARGETS:
{targets}
"""


def split(raw: dict) -> tuple[dict, dict]:
    """Separate one compact response into the existing canonical contracts."""
    valid_tables = []
    for table in raw.get("tables") or []:
        width = len(table.get("columns") or [])
        if width <= 0:
            if table.get("rows"):
                raise ValueError(f"table {table.get('id')!r} has rows but no columns")
            # A label-only footer is a region, not a table. Preserve its
            # geometry and visible title instead of dropping the content.
            raw.setdefault("free_text_regions", []).append({
                "id": table.get("id") or "label_only_region",
                "label": table.get("title") or "Label-only region",
                "bbox": table.get("bbox") or [0, 0, 1, 1],
                "value": table.get("title") or None,
                "needs_review": True,
                "illegible": False,
                "contract_repairs": ["zero_column_table_to_text_region"],
            })
            continue
        valid_tables.append(table)
        for row in table.get("rows") or []:
            values = row.get("values") or []
            if len(values) < width:
                missing = list(range(len(values), width))
                row["values"] = [*values, *([None] * len(missing))]
                row["review_columns"] = sorted(
                    set(row.get("review_columns") or []) | set(missing))
                row["illegible_columns"] = sorted(
                    set(row.get("illegible_columns") or []) | set(missing))
                row.setdefault("contract_repairs", []).append("missing_trailing_values")
            elif len(values) > width:
                raise ValueError(
                    f"table {table.get('id')!r} row {row.get('row_id')!r} has "
                    f"{len(values)} values for {width} columns")
            review = set(row.get("review_columns") or [])
            illegible = set(row.get("illegible_columns") or [])
            # This repair changes attention metadata only, never content.  A
            # model cannot claim ink is illegible while hiding it from review.
            if not illegible <= review:
                review |= illegible
                row["review_columns"] = sorted(review)
                row["contract_repairs"] = ["illegible_implies_review"]
            if any(not isinstance(index, int) or not 0 <= index < width
                   for index in review | illegible):
                raise ValueError("review/illegible column index is outside the table")
            y_center = row.get("y_center")
            if not isinstance(y_center, (int, float)):
                raise ValueError("row y_center must be between 0 and 1")
            if not 0 <= y_center <= 1:
                table_bbox = table.get("bbox") or [0, 0, 1, 1]
                row["y_center"] = min(max(float(y_center), max(0, table_bbox[1])),
                                      min(1, table_bbox[3]))
                row.setdefault("contract_repairs", []).append("row_center_clamped")
    raw["tables"] = valid_tables
    structure = {
        "page": raw["page"],
        "metadata_fields": [{key: item[key] for key in ("id", "label", "bbox")}
                            for item in raw.get("metadata_fields") or []],
        "tables": [{key: item[key] for key in
                    ("id", "title", "bbox", "estimated_rows", "columns")}
                   for item in raw.get("tables") or []],
        "free_text_regions": [{key: item[key] for key in ("id", "label", "bbox")}
                              for item in raw.get("free_text_regions") or []],
    }
    extraction = {
        "page": raw["page"],
        "metadata": [{"field_id": item["id"], "value": item["value"],
                      "confidence": .5 if item["needs_review"] else .95,
                      "illegible": item["illegible"],
                      "bbox": item["bbox"]}
                     for item in raw.get("metadata_fields") or []],
        "tables": [{"table_id": item["id"], "rows": [{
            "row_id": row["row_id"],
            "bbox": [item["bbox"][0], max(item["bbox"][1], row["y_center"] -
                     (item["bbox"][3] - item["bbox"][1]) /
                     max(2, 2 * (item["estimated_rows"] + 1))),
                     item["bbox"][2], min(item["bbox"][3], row["y_center"] +
                     (item["bbox"][3] - item["bbox"][1]) /
                     max(2, 2 * (item["estimated_rows"] + 1)))],
            "values": row["values"], "illegible_columns": row["illegible_columns"],
            "confidences": [.5 if index in set(row["review_columns"]) else .95
                            for index in range(len(row["values"]))],
        } for row in item.get("rows") or []]} for item in raw.get("tables") or []],
        "free_text": [{"region_id": item["id"], "value": item["value"],
                       "confidence": .5 if item["needs_review"] else .95}
                      for item in raw.get("free_text_regions") or []],
    }
    return structure, extraction


def page_items(page: dict):
    for item in page.get("metadata_fields") or []:
        yield f"metadata:{item['id']}", item, item.get("label")
    for item in page.get("free_text_regions") or []:
        yield f"text:{item['id']}", item, item.get("label")
    for table in page.get("tables") or []:
        labels = {column["id"]: column["label"] for column in table.get("columns") or []}
        for row in table.get("rows") or []:
            for cell in row.get("cells") or []:
                target = f"table:{table['id']}:row:{row['id']}:column:{cell['column_id']}"
                label = f"{table.get('title')}; row {row['id']}; {labels[cell['column_id']]}"
                yield target, cell, label


def select_targets(page: dict, *, threshold: float, cap_fraction: float,
                   cap_count: int) -> list[dict]:
    candidates = []
    all_items = list(page_items(page))
    for target_id, item, label in all_items:
        reading = (item.get("readings") or [{}])[0]
        confidence = float(reading.get("confidence") or 0)
        if reading.get("illegible") or confidence <= threshold:
            candidates.append({
                "target_id": target_id, "label": label, "bbox": item.get("bbox"),
                "primary_value": reading.get("value"), "primary_confidence": confidence,
                "_priority": (not reading.get("illegible"), confidence),
            })
    limit = min(cap_count, max(1, int(len(all_items) * cap_fraction))) if all_items else 0
    selected = sorted(candidates, key=lambda item: item["_priority"])[:limit]
    for item in selected:
        item.pop("_priority", None)
    return selected


def apply_peer(page: dict, targets: list[dict], raw: dict, peer_model: str) -> dict:
    item_map = {target_id: item for target_id, item, _label in page_items(page)}
    requested_ids = {target["target_id"] for target in targets}
    seen = set()
    for reading in raw.get("readings") or []:
        target_id = reading.get("target_id")
        item = item_map.get(target_id)
        if item is None or target_id not in requested_ids or target_id in seen:
            continue
        seen.add(target_id)
        item.setdefault("readings", []).append({
            "model": peer_model, "value": reading.get("value"),
            "confidence": reading.get("confidence", 0),
            "illegible": bool(reading.get("illegible")), "bbox": item.get("bbox"),
        })
        # Resolve only peer-audited cells. Non-targets remain one-reader
        # agreements rather than being falsely marked as missing-peer errors.
        canonical._resolve_item(item)
        item["targeted_peer"] = True
    for target_id in requested_ids - seen:
        item = item_map.get(target_id)
        if item is None:
            continue
        item.setdefault("readings", []).append({
            "model": peer_model, "value": None, "confidence": 0.0,
            "illegible": True, "missing": True, "bbox": item.get("bbox"),
        })
        canonical._resolve_item(item)
        item["targeted_peer"] = True
    return {"requested": len(requested_ids), "returned": len(seen),
            "missing": len(requested_ids - seen)}


def run(form_dir: Path, model: str, peer_model: str | None, tag: str,
        *, pages: list[int] | None = None, threshold: float = .8,
        cap_fraction: float = .1, cap_count: int = 80,
        provider: str = "openai", reasoning: str | None = "minimal",
        peer_reasoning: str | None = None, reuse_existing: bool = False) -> dict:
    output = form_dir / "canonical_outputs" / tag
    output.mkdir(parents=True, exist_ok=True)
    page_count = fitz.open(form_dir / "input.pdf").page_count
    selected_pages = pages or list(range(1, page_count + 1))
    document_pages, calls = [], []
    for number in selected_pages:
        overview, tiles = structured_pipeline.render_page_inputs(form_dir, number)
        model_file = structured_pipeline.model_filename(model)
        raw_path = output / f"page_{number}__unified__{model_file}.json"
        meta_path = output / f"page_{number}__unified__{model_file}.meta.json"
        if reuse_existing and raw_path.exists() and meta_path.exists():
            raw, meta = json.loads(raw_path.read_text()), json.loads(meta_path.read_text())
        else:
            raw, meta = responses_json(model, UNIFIED_PROMPT, [overview, *tiles],
                                       UNIFIED_SCHEMA, thinking=reasoning)
            raw_path.write_text(json.dumps(raw, indent=2))
            meta_path.write_text(json.dumps(meta, indent=2))
        structure, extraction = split(raw)
        geometry = structured_pipeline.refine_structure_geometry(structure, overview)
        page = canonical.normalize_structure(structure, number)
        canonical.attach_extraction(page, extraction, f"{provider}:{model}")
        one_page = canonical.new_document(str(form_dir / "input.pdf"), [page],
                                          [f"{provider}:{model}"])
        canonical.resolve(one_page)
        calls.append({"stage": "unified", "page": number,
                      "geometry_refinements": geometry,
                      "contract_repairs": sum(
                          len(row.get("contract_repairs") or [])
                          for table in raw.get("tables") or []
                          for row in table.get("rows") or []) + sum(
                              len(item.get("contract_repairs") or [])
                              for item in raw.get("free_text_regions") or []), **meta})

        targets = select_targets(page, threshold=threshold,
                                 cap_fraction=cap_fraction, cap_count=cap_count)
        if peer_model and targets:
            # Send only quadrants intersecting at least one target, plus overview.
            chosen_tiles = []
            regions = [(0, 0, .56, .56), (.44, 0, 1, .56),
                       (0, .44, .56, 1), (.44, .44, 1, 1)]
            for tile, region in zip(tiles, regions):
                if any(not (target["bbox"][2] < region[0]
                            or target["bbox"][0] > region[2]
                            or target["bbox"][3] < region[1]
                            or target["bbox"][1] > region[3])
                       for target in targets if target.get("bbox")):
                    chosen_tiles.append(tile)
            prompt = TARGET_PROMPT.format(targets=json.dumps(targets, separators=(",", ":")))
            peer_thinking = (peer_reasoning if peer_reasoning is not None else
                             (None if peer_model.startswith(("gpt-4", "o")) else "minimal"))
            peer, peer_meta = responses_json(peer_model, prompt, [overview, *chosen_tiles],
                                             TARGET_SCHEMA, thinking=peer_thinking)
            audit = apply_peer(page, targets, peer, f"{provider}:{peer_model}")
            peer_file = structured_pipeline.model_filename(peer_model)
            peer_path = output / f"page_{number}__peer__{peer_file}.json"
            peer_meta_path = output / f"page_{number}__peer__{peer_file}.meta.json"
            peer_path.write_text(json.dumps(peer, indent=2))
            peer_meta_path.write_text(json.dumps(peer_meta, indent=2))
            calls.append({"stage": "targeted_peer", "page": number,
                          "requested_targets": len(targets), **audit, **peer_meta})
        document_pages.append(page)
        print(f"page {number}/{page_count}: {len(page['tables'])} tables, "
              f"{len(targets)} targeted peer candidates", flush=True)

    models = [f"{provider}:{model}"] + (
        [f"targeted:{provider}:{peer_model}"] if peer_model else [])
    document = canonical.new_document(str(form_dir / "input.pdf"), document_pages, models)
    errors = canonical.validate(document)
    stats = structured_pipeline.disagreement_stats(document)
    report = {
        "version": "formidable-api-mid-unified-v1", "form": form_dir.name,
        "tag": tag, "provider": provider, "model": model,
        "targeted_peer_model": peer_model,
        "peer_policy": {"confidence_lte": threshold, "cap_fraction": cap_fraction,
                        "cap_count_per_page": cap_count},
        "calls": calls, "cost_usd": round(sum(x.get("cost_usd") or 0 for x in calls), 8),
        "latency_s": round(sum(x.get("latency_s") or 0 for x in calls), 1),
        "validation_errors": errors, "disagreement": stats,
    }
    document["run"] = report
    canonical.write_xlsx(document, output / "output.xlsx")
    canonical.dump(document, output / "canonical.json")
    (output / "run.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--form", type=Path, default=WIDE / "eval_forms" / "eval_09")
    parser.add_argument("--model", default="gpt-5-nano")
    parser.add_argument("--peer-model", default="gpt-4.1-nano")
    parser.add_argument("--no-peer", action="store_true")
    parser.add_argument("--tag", default="api_mid_unified_targeted_v1")
    parser.add_argument("--pages", default="")
    parser.add_argument("--confidence", type=float, default=.8)
    parser.add_argument("--peer-cap-fraction", type=float, default=.1)
    parser.add_argument("--peer-cap-count", type=int, default=80)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    pages = [int(value) for value in args.pages.split(",") if value.strip()]
    declaration = vars(args) | {"form": str(args.form.resolve()),
                                "authentication": "OPENAI_API_KEY only"}
    print(json.dumps(declaration, indent=2), flush=True)
    if args.dry_run:
        return 0
    result = run(args.form.resolve(), args.model,
                 None if args.no_peer else args.peer_model, args.tag,
                 pages=pages or None, threshold=args.confidence,
                 cap_fraction=args.peer_cap_fraction, cap_count=args.peer_cap_count)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
