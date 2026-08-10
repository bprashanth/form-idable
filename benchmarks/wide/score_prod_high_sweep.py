#!/usr/bin/env python3
"""Download and independently score every completed production high job."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import run_high_sweep

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


def main() -> None:
    api = os.environ["FORMIDABLE_API_URL"].rstrip("/")
    token = os.environ["FORMIDABLE_ID_TOKEN"]
    state = json.loads(STATE.read_text())
    records = []
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
        high = run_high_sweep.score(fixture, run / "output.xlsx")
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
        print(f"scored {name}: low={low['semantic_all_f1']:.3f} "
              f"high={high['semantic_all_f1']:.3f}", flush=True)

    report = {"version": "formidable-production-high-audit-v1", "forms": records}
    (OUTPUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    low_f1 = sum(item["low"]["semantic_all_f1"] for item in records) / len(records)
    high_f1 = sum(item["high"]["semantic_all_f1"] for item in records) / len(records)
    print(json.dumps({"forms": len(records), "low_mean_f1": low_f1,
                      "production_high_mean_f1": high_f1,
                      "delta": high_f1 - low_f1}, indent=2))


if __name__ == "__main__":
    main()
