#!/usr/bin/env python3
"""Resumable authenticated production high sweep over every PDF fixture."""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import run_high_sweep

DEFAULT_STATE = run_high_sweep.REPO / "benchmarks/high_runs/prod_sweep_v1/state.json"


def request_json(url, token, *, method="GET", body=None):
    payload = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def save(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--poll-seconds", type=int, default=15)
    args = parser.parse_args()
    api = os.environ["FORMIDABLE_API_URL"].rstrip("/")
    token = os.environ["FORMIDABLE_ID_TOKEN"]
    fixtures = run_high_sweep.pdf_fixtures()
    state = json.loads(args.state.read_text()) if args.state.exists() else {
        "version": "formidable-production-high-sweep-v1", "jobs": {},
    }

    for fixture in fixtures:
        record = state["jobs"].setdefault(fixture.name, {
            "fixture": fixture.name,
            "source": json.loads((fixture / "source_map.json").read_text())["original_path"],
            "status": "not_started",
        })
        if record["status"] != "not_started":
            continue
        name = f"high-fieldtrip-{fixture.name}-{Path(record['source']).stem}"
        created = request_json(f"{api}/vision/extract", token, method="POST", body={
            "filename": Path(record["source"]).name, "name": name, "effort": "high",
        })
        upload = urllib.request.Request(
            created["upload_url"], data=(fixture / "input.pdf").read_bytes(),
            headers={"Content-Type": "application/octet-stream"}, method="PUT")
        with urllib.request.urlopen(upload, timeout=180):
            pass
        record.update({"job_id": created["job_id"], "status": "uploaded", "name": name})
        save(args.state, state)

    while True:
        active = [item for item in state["jobs"].values()
                  if item["status"] in {"queued", "processing"}]
        waiting = [item for item in state["jobs"].values() if item["status"] == "uploaded"]
        while waiting and len(active) < args.parallel:
            item = waiting.pop(0)
            started = request_json(f"{api}/api/jobs/{item['job_id']}/start", token, method="POST")
            if started.get("effort") != "high" or started.get("task_family") != "formidable-high-worker":
                raise RuntimeError(f"wrong production route for {item['fixture']}: {started}")
            item.update({"status": "queued", "started_at": time.time()})
            active.append(item)
            print(f"started {item['fixture']} job={item['job_id']}", flush=True)
            save(args.state, state)

        if not active and not waiting:
            break
        time.sleep(args.poll_seconds)
        for item in list(active):
            try:
                status = request_json(f"{api}/api/jobs/{item['job_id']}/status", token)
            except urllib.error.HTTPError as error:
                if error.code == 401:
                    raise RuntimeError("Cognito token expired; mint a new token and resume") from error
                raise
            item["status"] = status["status"]
            item["progress"] = status.get("progress")
            if item["status"] in {"complete", "failed"}:
                item["finished_at"] = time.time()
                item["error"] = status.get("error")
                print(f"{item['status']} {item['fixture']} {item.get('progress') or ''}", flush=True)
            save(args.state, state)
        failures = [item for item in state["jobs"].values() if item["status"] == "failed"]
        if failures:
            raise RuntimeError(f"production high failures: {failures}")

    completed = [item for item in state["jobs"].values() if item["status"] == "complete"]
    print(json.dumps({"completed": len(completed), "expected": len(fixtures),
                      "job_ids": [item["job_id"] for item in completed]}, indent=2))
    if len(completed) != len(fixtures):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
