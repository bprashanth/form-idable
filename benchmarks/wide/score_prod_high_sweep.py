#!/usr/bin/env python3
"""Download and independently score every completed production high job."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import run_high_sweep
import wide_diff
from openpyxl import load_workbook

STATE = run_high_sweep.REPO / "benchmarks/high_runs/prod_sweep_v1/state.json"
OUTPUT = run_high_sweep.REPO / "benchmarks/high_runs/prod_sweep_v1"


def request_json(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=180) as response:
        target.write_bytes(response.read())


def literal_page_workbook(source: Path, target: Path) -> None:
    """Exclude high-only audit sheets from literal transcription scoring."""
    workbook = load_workbook(source)
    for sheet in list(workbook.worksheets):
        if not sheet.title.lower().startswith("page"):
            workbook.remove(sheet)
    if not workbook.worksheets:
        raise RuntimeError(f"no literal page sheets in {source}")
    workbook.save(target)


def extend_tokens(bucket: dict, workbook: Path) -> None:
    cells = wide_diff.xlsx_diff._cells(str(workbook))
    nums, words = wide_diff.xlsx_diff._atoms(cells)
    bucket["nums"].extend(nums)
    bucket["words"].extend(words)
    bucket["codes"].extend(wide_diff._semantic_codes(cells))


def main() -> None:
    api = os.environ["FORMIDABLE_API_URL"].rstrip("/")
    token = os.environ["FORMIDABLE_ID_TOKEN"]
    state = json.loads(STATE.read_text())
    records = []
    token_sets = {name: {side: {kind: [] for kind in ("nums", "words", "codes")}
                         for side in ("golden", "candidate")}
                  for name in ("low", "high")}
    for name, job in sorted(state["jobs"].items()):
        if job["status"] != "complete":
            raise RuntimeError(f"production job is not complete: {name}={job['status']}")
        run = OUTPUT / name
        xlsx = request_json(f"{api}/api/jobs/{job['job_id']}/xlsx", token)
        download(xlsx["url"], run / "output.xlsx")
        for endpoint, filename in (
            ("manifest", "crops_manifest.json"),
            ("review-manifest", "review_manifest.json"),
            ("analytics", "analytics.json"),
        ):
            payload = request_json(f"{api}/api/jobs/{job['job_id']}/{endpoint}", token)
            (run / filename).write_text(json.dumps(payload, indent=2) + "\n")

        fixture = run_high_sweep.FORMS / name
        literal_page_workbook(run / "output.xlsx", run / "content_output.xlsx")
        high = run_high_sweep.score(fixture, run / "content_output.xlsx")
        low_path = fixture / "codex_work/output.xlsx"
        low = run_high_sweep.score(fixture, low_path) if low_path.exists() else None
        review = json.loads((run / "review_manifest.json").read_text())
        analytics = json.loads((run / "analytics.json").read_text())
        manifest = json.loads((run / "crops_manifest.json").read_text())
        if review.get("version") != "formidable-review-v1":
            raise RuntimeError(f"bad review manifest for {name}")
        if analytics.get("version") != "formidable-analytics-v1":
            raise RuntimeError(f"bad analytics for {name}")
        if analytics["summary"]["pages"] != len(manifest["pages"]):
            raise RuntimeError(f"page count mismatch for {name}")
        records.append({
            "fixture": name,
            "job_id": job["job_id"],
            "pages": len(manifest["pages"]),
            "low": run_high_sweep.compact(low) if low else None,
            "high": run_high_sweep.compact(high),
            "review": review["summary"],
            "analytics": analytics["summary"],
        })
        for variant, candidate in (("low", low_path),
                                   ("high", run / "content_output.xlsx")):
            extend_tokens(token_sets[variant]["golden"], fixture / "golden.xlsx")
            extend_tokens(token_sets[variant]["candidate"], candidate)
        print(f"scored {name}: low={low['semantic_all_f1']:.3f} "
              f"high={high['semantic_all_f1']:.3f}", flush=True)

    aggregate = {}
    for variant, sides in token_sets.items():
        aggregate[variant] = {
            "semantic_all": wide_diff._prf(
                [str(value) for value in sides["golden"]["nums"]]
                + sides["golden"]["words"] + sides["golden"]["codes"],
                [str(value) for value in sides["candidate"]["nums"]]
                + sides["candidate"]["words"] + sides["candidate"]["codes"]),
            "numeric": wide_diff._prf(sides["golden"]["nums"], sides["candidate"]["nums"]),
            "word": wide_diff._prf(sides["golden"]["words"], sides["candidate"]["words"]),
            "semantic_code": wide_diff._prf(
                sides["golden"]["codes"], sides["candidate"]["codes"]),
        }
    report = {"version": "formidable-production-high-audit-v1", "forms": records,
              "aggregate": aggregate}
    (OUTPUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    low_f1 = sum(item["low"]["semantic_all_f1"] for item in records) / len(records)
    high_f1 = sum(item["high"]["semantic_all_f1"] for item in records) / len(records)
    print(json.dumps({"forms": len(records), "low_mean_f1": low_f1,
                      "production_high_mean_f1": high_f1,
                      "delta": high_f1 - low_f1,
                      "aggregate": aggregate}, indent=2))


if __name__ == "__main__":
    main()
