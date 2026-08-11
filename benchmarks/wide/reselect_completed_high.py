#!/usr/bin/env python3
"""Replay deterministic High route selection from saved production evidence.

This never calls a transcription model. It is intended for a routing-only
release: rebuild the literal workbook, ecology suggestions, review manifest
and Analytics from the raw per-cell readings already saved by completed test
jobs. Use ``--upload`` only for explicitly disposable benchmark jobs.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
from pathlib import Path

import boto3

import analytics_manifest
import canonical
import ecology_review
import review_manifest

TERRA = "codex:gpt-5.6-terra"
LUNA = "codex:gpt-5.6-luna"
PEERS = [TERRA, LUNA]


def items(document):
    for page in document.get("pages") or []:
        yield from page.get("metadata_fields") or []
        yield from page.get("free_text_regions") or []
        for table in page.get("tables") or []:
            for row in table.get("rows") or []:
                yield from row.get("cells") or []


def routing_evidence(document):
    counts = {model: 0 for model in document.get("models") or []}
    conflicts = total = 0
    for item in items(document):
        total += 1
        conflicts += item.get("status") == "peer_consensus_disagreement"
        for reading in item.get("readings") or []:
            if reading.get("value") is not None and str(reading["value"]).strip():
                counts[reading.get("model")] = counts.get(reading.get("model"), 0) + 1
    primary = counts.get("codex:agentic-low", 0)
    ordered = sorted((counts.get(model, 0) for model in PEERS), reverse=True)
    strongest = ordered[0] if ordered else 0
    second = ordered[1] if len(ordered) > 1 else 0
    return {
        "nonblank_by_model": counts,
        "primary_literal_coverage": round(primary / strongest, 4) if strongest else 1.0,
        "strongest_peer_recovery_fraction": round(strongest / primary - 1, 4)
        if primary else (1.0 if strongest else 0.0),
        "strongest_peer_lead_fraction": round(strongest / second - 1, 4)
        if second else (1.0 if strongest else 0.0),
        "peer_consensus_conflicts": conflicts,
        "peer_consensus_conflict_fraction": round(conflicts / total, 4) if total else 0.0,
        "target_items": total,
    }


def peer_document(source):
    document = copy.deepcopy(source)
    document["models"] = list(PEERS)
    for item in items(document):
        item["readings"] = [reading for reading in item.get("readings") or []
                            if reading.get("model") in PEERS]
        item.pop("ecology_flags", None)
    return document


def select_reader(document):
    coverage = {model: 0 for model in PEERS}
    for item in items(document):
        by_model = {reading.get("model"): reading.get("value")
                    for reading in item.get("readings") or []}
        for model in PEERS:
            value = by_model.get(model)
            coverage[model] += value is not None and bool(str(value).strip())
    selected = TERRA
    leader = max(PEERS, key=lambda model: coverage[model])
    if coverage[leader] >= max(1, coverage[selected]) * 1.10:
        selected = leader
    document["models"] = [selected, *(model for model in PEERS if model != selected)]
    canonical.resolve(document)
    canonical.assign_xlsx_coordinates(document)
    return selected, coverage


def ecology_artifact(document, root):
    records = ecology_review.canonical_records(document)
    findings = ecology_review.numeric_findings(records)
    latitude, longitude = ecology_review.location_coordinates(records)
    findings += ecology_review.taxonomy_findings(
        records, ecology_review.GBIFClient(root / "gbif-cache"), latitude, longitude)
    ecology = {
        "version": "formidable-ecology-review-v1",
        "policy": "flags and suggestions only; literal values are never changed",
        "records": len(records), "findings": findings,
    }
    ecology_review.apply_findings(
        document, [item for item in findings
                   if item.get("severity") in {"medium", "high"}])
    return ecology


def repair_fallback_coordinates(run_dir, run, document):
    """Repair old fallback provenance without changing its selected values."""
    canonical.assign_xlsx_coordinates(document)
    ecology = json.loads((run_dir / "ecology_review.json").read_text())
    review = review_manifest.from_canonical(document, ecology)
    review["route"] = {
        "status": "structured_reader_fallback", "path": "high_v1",
        "reason": "agentic workbook failed a sector-agnostic literal-coverage or peer-conflict gate",
    }
    errors = review_manifest.validate(review)
    if errors:
        raise RuntimeError("invalid repaired review manifest: " + "; ".join(errors))
    analytics = analytics_manifest.build(document, ecology)
    canonical.dump(document, run_dir / "canonical.json")
    (run_dir / "review_manifest.json").write_text(
        json.dumps(review, indent=2, ensure_ascii=False) + "\n")
    (run_dir / "analytics.json").write_text(
        json.dumps(analytics, indent=2, ensure_ascii=False) + "\n")
    run.update({"review": review["summary"], "analytics": analytics["summary"]})
    (run_dir / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    return True, run.get("content", {}).get("selected_reader"), \
        run.get("routing_evidence") or {}


def replay(run_dir, *, force=False):
    run = json.loads((run_dir / "run.json").read_text())
    document = json.loads((run_dir / "canonical.json").read_text())
    if run.get("route") == "structured_reader_fallback":
        if force:
            return repair_fallback_coordinates(run_dir, run, document)
        return False, run.get("route"), run.get("routing_evidence") or {}
    evidence = routing_evidence(document)
    geometry = (run.get("bridge") or {}).get("peer_nonblank_coverage", 0)
    healthy = (geometry >= 0.80
               and evidence["primary_literal_coverage"] >= 0.75
               and evidence["peer_consensus_conflict_fraction"] <= 0.20
               and not (evidence["strongest_peer_recovery_fraction"] >= 0.15
                        and evidence["strongest_peer_lead_fraction"] >= 0.10))
    if (run.get("route") != "agentic_primary" and not force) or healthy:
        return False, run.get("route"), evidence

    document = peer_document(document)
    selected, coverage = select_reader(document)
    ecology = ecology_artifact(document, run_dir)

    content = run_dir / "content_output.xlsx"
    canonical.write_xlsx(document, content)
    output = run_dir / "output.xlsx"
    shutil.copy2(content, output)
    ecology_review.add_review_sheet(output, ecology["findings"])
    canonical.dump(document, run_dir / "canonical.json")
    (run_dir / "ecology_review.json").write_text(
        json.dumps(ecology, indent=2, ensure_ascii=False) + "\n")

    review = review_manifest.from_canonical(document, ecology)
    review["route"] = {
        "status": "structured_reader_fallback", "path": "high_v1",
        "reason": "agentic workbook failed a sector-agnostic literal-coverage or peer-conflict gate",
    }
    errors = review_manifest.validate(review)
    if errors:
        raise RuntimeError("invalid replayed review manifest: " + "; ".join(errors))
    (run_dir / "review_manifest.json").write_text(
        json.dumps(review, indent=2, ensure_ascii=False) + "\n")
    analytics = analytics_manifest.build(document, ecology)
    (run_dir / "analytics.json").write_text(
        json.dumps(analytics, indent=2, ensure_ascii=False) + "\n")

    run.update({
        "route": "structured_reader_fallback",
        "content": {"workbook": "content.xlsx", "route": "structured_reader_fallback",
                    "selected_reader": selected,
                    "reader_nonblank_coverage": coverage},
        "routing_evidence": evidence,
        "routing_thresholds": {"minimum_geometry_coverage": 0.80,
                               "minimum_literal_coverage": 0.75,
                               "maximum_consensus_conflict_fraction": 0.20,
                               "peer_recovery_trigger": 0.15,
                               "peer_lead_margin": 0.10},
        "review": review["summary"], "analytics": analytics["summary"],
    })
    (run_dir / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    return True, selected, evidence


def upload(s3, bucket, prefix, job_id, run_dir):
    types = {
        "output.xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "canonical.json": "application/json", "review_manifest.json": "application/json",
        "ecology_review.json": "application/json", "analytics.json": "application/json",
        "run.json": "application/json",
    }
    for name, content_type in types.items():
        s3.upload_file(str(run_dir / name), bucket, f"{prefix}/jobs/{job_id}/{name}",
                       ExtraArgs={"ContentType": content_type})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--force-fixture", action="append", default=[])
    parser.add_argument("--bucket", default="formidable-storage")
    parser.add_argument("--prefix", default="formidable")
    args = parser.parse_args()
    state = json.loads(args.state.read_text())
    s3 = boto3.client("s3", region_name="ap-south-1") if args.upload else None
    changed = []
    for fixture, job in sorted(state["jobs"].items()):
        if args.force_fixture and fixture not in args.force_fixture:
            continue
        run_dir = args.state.parent / fixture
        did_change, route, evidence = replay(
            run_dir, force=fixture in args.force_fixture)
        print(json.dumps({"fixture": fixture, "changed": did_change, "route": route,
                          "routing_evidence": evidence}, sort_keys=True))
        if did_change:
            changed.append(fixture)
            if s3:
                upload(s3, args.bucket, args.prefix, job["job_id"], run_dir)
    print(json.dumps({"changed": changed, "uploaded": bool(args.upload)}))


if __name__ == "__main__":
    main()
