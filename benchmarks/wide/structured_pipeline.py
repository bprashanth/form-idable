#!/usr/bin/env python3
"""API-only canonical extraction: schema, independent readings, disagreement."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

import fitz

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import canonical  # noqa: E402
import wide_bench  # noqa: E402


STRUCTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "page": {"type": "integer"},
        "metadata_fields": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"}, "label": {"type": "string"},
                "bbox": {"type": "array", "items": {"type": "number"},
                         "minItems": 4, "maxItems": 4},
            }, "required": ["id", "label", "bbox"], "additionalProperties": False,
        }},
        "tables": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"}, "title": {"type": "string"},
                "bbox": {"type": "array", "items": {"type": "number"},
                         "minItems": 4, "maxItems": 4},
                "estimated_rows": {"type": "integer"},
                "columns": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"}, "label": {"type": "string"},
                        "parent": {"type": ["string", "null"]},
                        "value_kind": {"type": "string"},
                        "x0": {"type": "number"}, "x1": {"type": "number"},
                    },
                    "required": ["id", "label", "parent", "value_kind", "x0", "x1"],
                    "additionalProperties": False,
                }},
            },
            "required": ["id", "title", "bbox", "estimated_rows", "columns"],
            "additionalProperties": False,
        }},
        "free_text_regions": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"}, "label": {"type": "string"},
                "bbox": {"type": "array", "items": {"type": "number"},
                         "minItems": 4, "maxItems": 4},
            }, "required": ["id", "label", "bbox"], "additionalProperties": False,
        }},
    },
    "required": ["page", "metadata_fields", "tables", "free_text_regions"],
    "additionalProperties": False,
}


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "page": {"type": "integer"},
        "metadata": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "field_id": {"type": "string"},
                "value": {"type": ["string", "null"]},
                "confidence": {"type": "number"}, "illegible": {"type": "boolean"},
                "bbox": {"type": "array", "items": {"type": "number"},
                         "minItems": 4, "maxItems": 4},
            }, "required": ["field_id", "value", "confidence", "illegible", "bbox"],
            "additionalProperties": False,
        }},
        "tables": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "table_id": {"type": "string"},
                "rows": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "row_id": {"type": "string"},
                        "bbox": {"type": "array", "items": {"type": "number"},
                                 "minItems": 4, "maxItems": 4},
                        "values": {"type": "array", "items": {"type": ["string", "null"]}},
                        "confidences": {"type": "array", "items": {"type": "number"}},
                        "illegible_columns": {"type": "array", "items": {"type": "integer"}},
                    },
                    "required": ["row_id", "bbox", "values", "confidences",
                                 "illegible_columns"],
                    "additionalProperties": False,
                }},
            }, "required": ["table_id", "rows"], "additionalProperties": False,
        }},
        "free_text": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "region_id": {"type": "string"},
                "value": {"type": ["string", "null"]},
                "confidence": {"type": "number"},
            }, "required": ["region_id", "value", "confidence"],
            "additionalProperties": False,
        }},
    },
    "required": ["page", "metadata", "tables", "free_text"],
    "additionalProperties": False,
}


STRUCTURE_PROMPT = """You are the structure stage of a general paper-form digitizer.
Inspect this ONE full-page overview. Describe the visible form, but do not
transcribe handwritten values yet.

Return every standalone metadata field and every repeated table/list. A
numbered handwritten list is a table. For a table, preserve every physical
column and every level of a spanning header: put the group header in `parent`
and the leaf header in `label`. Never merge distinct subcolumns. Coordinates
are [x0,y0,x1,y1] fractions of the FULL PAGE, all between 0 and 1. Column x0/x1
are also full-page fractions, not fractions of the table. Estimate the number
of visibly used data rows; do not count unused trailing blank rows.

Use generic value kinds such as identifier, integer, decimal, date, time,
species, local_name, categorical_code, yes_no, free_text, or unknown. This
stage is sector-agnostic: report what is printed, without inventing domains or
values. Include marginal annotations as free-text regions.
"""


EXTRACT_PROMPT = """You are the visual transcription stage of a general paper-form
digitizer. You receive one full-page overview followed by four overlapping
high-resolution tiles (top-left, top-right, bottom-left, bottom-right). They
show the SAME page; do not duplicate rows from overlaps.

The structure stage's schema is below. Populate it exactly. For every table
row with recorded content, return one values array in the declared column
order and with exactly that many entries. Preserve printed identifiers exactly,
including gaps; never renumber or repair a sequence. Preserve dots, ticks,
tallies, ditto marks, struck cells, multi-value notations, and merged annotation
rows according to what the paper means. A lone dot used as a recorded value is
0; a continuous strike-through means blank; tally marks are counted; checked
boxes are X.

Critical anti-fabrication rule: never copy a neighbouring value or a column's
common value merely to make the table complete. Use null for a visibly blank
cell. If ink is present but unreadable, also use null and list that zero-based
column index in illegible_columns. A low-confidence guess is worse than an
explicit unreadable cell. Printed legends are context for interpreting marks,
not permission to snap ambiguous ink onto a legal value.

Row and field bboxes are full-page fractions. Every row bbox is strictly
`[left, top, right, bottom]`: first/third are horizontal x coordinates and
second/fourth are vertical y coordinates. A table row bbox must be wide and
short, never a tall column or a large page block. row_id is the literal printed or
written row key when one exists; otherwise use a stable y-based label such as
y_0.372. Confidence is visual confidence from 0 to 1, not ecological
plausibility. Do not apply species dictionaries or ecological corrections in
this stage.

DECLARED PAGE SCHEMA:
{schema}
"""


def render_page_inputs(form_dir: Path, page: int) -> tuple[Path, list[Path]]:
    output = form_dir / "canonical_tiles"
    output.mkdir(exist_ok=True)
    pdf = form_dir / "input.pdf"
    overview = output / f"page_{page}_overview.png"
    if not overview.exists():
        subprocess.run([sys.executable, str(wide_bench.RENDER), str(pdf), "--page", str(page),
                        "--zoom", "3", "--out", str(overview)], check=True, capture_output=True)
    tiles = []
    regions = [(0, 0, .56, .56), (.44, 0, 1, .56),
               (0, .44, .56, 1), (.44, .44, 1, 1)]
    for index, region in enumerate(regions):
        path = output / f"page_{page}_q{index}.png"
        if not path.exists():
            box = ",".join(str(value) for value in region)
            subprocess.run([sys.executable, str(wide_bench.RENDER), str(pdf), "--page", str(page),
                            "--bbox", box, "--zoom", "8", "--out", str(path)],
                           check=True, capture_output=True)
        tiles.append(path)
    return overview, tiles


def gemini_json(model: str, prompt: str, images: list[Path], schema: dict,
                *, thinking: str = "minimal") -> tuple[dict, dict]:
    parts = [{"text": prompt}]
    for image in images:
        parts.append({"inline_data": {"mime_type": "image/png", "data": wide_bench._b64(image)}})
    generation = {
        "temperature": 0,
        "thinkingConfig": {"thinkingLevel": thinking},
        "responseMimeType": "application/json",
        "responseJsonSchema": schema,
        "maxOutputTokens": 32768,
    }
    payload = {"contents": [{"role": "user", "parts": parts}],
               "generationConfig": generation}
    key = wide_bench._key("gemini")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    t0 = time.time()
    try:
        response = wide_bench._post(url, payload, {}, timeout=900)
    except urllib.error.HTTPError as error:
        body = error.read()
        # Some generateContent revisions use responseSchema rather than the
        # JSON-Schema field. Retry once without weakening JSON enforcement.
        if error.code != 400:
            raise
        generation["responseSchema"] = generation.pop("responseJsonSchema")
        try:
            response = wide_bench._post(url, payload, {}, timeout=900)
        except urllib.error.HTTPError as second:
            raise RuntimeError(f"Gemini structured output rejected: {body[:300]!r}; "
                               f"fallback: {second.read()[:300]!r}") from second
    text = "".join(part.get("text", "")
                   for part in response["candidates"][0]["content"]["parts"])
    usage = response.get("usageMetadata", {})
    meta = {
        "model": model,
        "in_tok": usage.get("promptTokenCount"),
        "out_tok": usage.get("candidatesTokenCount"),
        "thinking_tok": usage.get("thoughtsTokenCount", 0),
        "cost_usd": wide_bench._gemini_cost(model, usage),
        "latency_s": round(time.time() - t0, 1),
    }
    return json.loads(text), meta


def openrouter_json(model: str, prompt: str, images: list[Path], schema: dict,
                    *, thinking: str = "minimal") -> tuple[dict, dict]:
    """Structured vision through OpenRouter, preserving the same JSON contract."""
    content = [{"type": "text", "text": prompt}]
    for image in images:
        content.append({"type": "image_url", "image_url": {
            "url": f"data:image/png;base64,{wide_bench._b64(image)}"}})
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 32768,
        "messages": [{"role": "user", "content": content}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "formidable_extraction", "strict": True, "schema": schema}},
        "reasoning": {"effort": thinking},
        "usage": {"include": True},
    }
    headers = {"Authorization": f"Bearer {wide_bench._key('openrouter')}",
               "HTTP-Referer": "https://fomoscribe.netlify.app",
               "X-Title": "Formidable high extraction"}
    started = time.time()
    retry_delays = (0, 2, 5, 10)
    for attempt, delay in enumerate(retry_delays, start=1):
        if delay:
            time.sleep(delay)
        try:
            response = wide_bench._post(
                "https://openrouter.ai/api/v1/chat/completions", payload, headers, timeout=900)
            message = response["choices"][0]["message"]["content"]
            if isinstance(message, list):
                message = "".join(part.get("text", "") for part in message
                                  if isinstance(part, dict))
            parsed = json.loads(message)
        except urllib.error.HTTPError as error:
            body = error.read()[:500]
            retryable = error.code in {408, 409, 429} or error.code >= 500
            if retryable and attempt < len(retry_delays):
                continue
            raise RuntimeError(
                f"OpenRouter {model} failed with HTTP {error.code}: {body!r}") from error
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            if attempt < len(retry_delays):
                continue
            raise RuntimeError(
                f"OpenRouter {model} returned invalid structured output after "
                f"{attempt} attempts: {error}") from error

        usage = response.get("usage") or {}
        return parsed, {
            "provider": "openrouter", "model": model,
            "in_tok": usage.get("prompt_tokens"), "out_tok": usage.get("completion_tokens"),
            "thinking_tok": usage.get("reasoning_tokens", 0),
            "cost_usd": usage.get("cost"), "latency_s": round(time.time() - started, 1),
            "attempts": attempt,
        }
    raise AssertionError("unreachable")


def provider_json(model_spec: str, prompt: str, images: list[Path], schema: dict,
                  *, thinking: str = "minimal") -> tuple[dict, dict]:
    if model_spec.startswith("openrouter:"):
        return openrouter_json(model_spec.split(":", 1)[1], prompt, images, schema,
                               thinking=thinking)
    return gemini_json(model_spec, prompt, images, schema, thinking=thinking)


def model_filename(model_spec: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", model_spec).strip("_")


def _read_structure(form_dir, output, page_number, schema_model, *, reuse=False):
    overview, tiles = render_page_inputs(form_dir, page_number)
    model_file = model_filename(schema_model)
    raw_path = output / f"page_{page_number}__structure__{model_file}.json"
    meta_path = output / f"page_{page_number}__structure__{model_file}.meta.json"
    if reuse and raw_path.exists() and meta_path.exists():
        return overview, tiles, json.loads(raw_path.read_text()), json.loads(meta_path.read_text())
    raw, meta = provider_json(schema_model, STRUCTURE_PROMPT, [overview], STRUCTURE_SCHEMA)
    raw_path.write_text(json.dumps(raw, indent=2))
    meta_path.write_text(json.dumps(meta, indent=2))
    return overview, tiles, raw, meta


def prepare_structures(form_dir: Path, schema_model: str, tag: str,
                       page_numbers: list[int] | None = None, *, reuse=False) -> dict:
    """Run/cache only the sector-agnostic page-structure stage for routing."""
    output = form_dir / "canonical_outputs" / tag
    output.mkdir(parents=True, exist_ok=True)
    page_count = fitz.open(form_dir / "input.pdf").page_count
    selected_pages = page_numbers or list(range(1, page_count + 1))
    calls = []
    for page_number in selected_pages:
        if not 1 <= page_number <= page_count:
            raise ValueError(f"page {page_number} outside 1..{page_count}")
        _overview, _tiles, raw, meta = _read_structure(
            form_dir, output, page_number, schema_model, reuse=reuse)
        calls.append({"stage": "structure", "page": page_number, **meta})
        print(f"page {page_number}/{page_count}: structure has "
              f"{len(raw.get('tables') or [])} tables", flush=True)
    report = {
        "form": form_dir.name, "tag": tag, "schema_model": schema_model,
        "pages": selected_pages, "calls": calls,
        "cost_usd": round(sum(call.get("cost_usd") or 0 for call in calls), 5),
        "latency_s": round(sum(call.get("latency_s") or 0 for call in calls), 1),
    }
    (output / "structure_run.json").write_text(json.dumps(report, indent=2))
    return report


def run(form_dir: Path, schema_model: str, models: list[str], tag: str,
        page_numbers: list[int] | None = None, *, reuse_structure=False,
        progress_callback=None) -> dict:
    output = form_dir / "canonical_outputs" / tag
    output.mkdir(parents=True, exist_ok=True)
    page_count = fitz.open(form_dir / "input.pdf").page_count
    pages, calls = [], []
    selected_pages = page_numbers or list(range(1, page_count + 1))
    for page_number in selected_pages:
        if not 1 <= page_number <= page_count:
            raise ValueError(f"page {page_number} outside 1..{page_count}")
        overview, tiles, raw_structure, meta = _read_structure(
            form_dir, output, page_number, schema_model, reuse=reuse_structure)
        calls.append({"stage": "structure", "page": page_number, **meta})
        page = canonical.normalize_structure(raw_structure, page_number)
        declared = {key: value for key, value in page.items() if key != "rows"}
        prompt = EXTRACT_PROMPT.format(schema=json.dumps(declared, ensure_ascii=False))
        for model in models:
            raw, meta = provider_json(model, prompt, [overview, *tiles], EXTRACTION_SCHEMA)
            calls.append({"stage": "extract", "page": page_number, **meta})
            (output / f"page_{page_number}__extract__{model_filename(model)}.json").write_text(
                json.dumps(raw, indent=2))
            canonical.attach_extraction(page, raw, model)
        pages.append(page)
        print(f"page {page_number}/{page_count}: {len(page['tables'])} tables, "
              f"{sum(len(t['rows']) for t in page['tables'])} aligned rows", flush=True)
        if progress_callback:
            progress_callback(page_number, len(selected_pages))

    document = canonical.new_document(str(form_dir / "input.pdf"), pages, models)
    canonical.resolve(document)
    errors = canonical.validate(document)
    stats = disagreement_stats(document)
    report = {
        "form": form_dir.name,
        "tag": tag,
        "schema_model": schema_model,
        "models": models,
        "calls": calls,
        "cost_usd": round(sum(call.get("cost_usd") or 0 for call in calls), 5),
        "latency_s": round(sum(call.get("latency_s") or 0 for call in calls), 1),
        "validation_errors": errors,
        "disagreement": stats,
    }
    document["run"] = report
    canonical.write_xlsx(document, output / "output.xlsx")
    canonical.dump(document, output / "canonical.json")
    (output / "run.json").write_text(json.dumps(report, indent=2))
    return report


def rebuild(form_dir: Path, tag: str) -> dict:
    """Reassemble saved provider JSON after local canonicalization changes."""
    output = form_dir / "canonical_outputs" / tag
    report = json.loads((output / "run.json").read_text())
    pages = []
    structure_files = sorted(
        (path for path in output.glob("page_*__structure__*.json")
         if not path.name.endswith(".meta.json")),
        key=lambda path: int(path.name.split("_")[1]))
    for structure_file in structure_files:
        page_number = int(structure_file.name.split("_")[1])
        page = canonical.normalize_structure(json.loads(structure_file.read_text()), page_number)
        for model in report["models"]:
            raw = json.loads((output / f"page_{page_number}__extract__{model_filename(model)}.json").read_text())
            canonical.attach_extraction(page, raw, model)
        pages.append(page)
    document = canonical.new_document(str(form_dir / "input.pdf"), pages, report["models"])
    canonical.resolve(document)
    report["validation_errors"] = canonical.validate(document)
    report["disagreement"] = disagreement_stats(document)
    document["run"] = report
    canonical.write_xlsx(document, output / "output.xlsx")
    canonical.dump(document, output / "canonical.json")
    (output / "run.json").write_text(json.dumps(report, indent=2))
    return report


def disagreement_stats(document):
    cells = []
    for page in document["pages"]:
        cells.extend(page["metadata_fields"])
        cells.extend(page["free_text_regions"])
        for table in page["tables"]:
            for row in table["rows"]:
                cells.extend(row["cells"])
    statuses = ("agreement", "majority_after_reread", "disagreement",
                "unresolved_after_reread", "blank_or_illegible")
    counts = {status: sum(cell.get("status") == status for cell in cells)
              for status in statuses}
    counts["total"] = len(cells)
    counts["review_fraction"] = round(
        (counts["majority_after_reread"] + counts["disagreement"]
         + counts["unresolved_after_reread"]
         + counts["blank_or_illegible"]) / len(cells), 4
    ) if cells else 0.0
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--form", required=True)
    parser.add_argument("--schema-model", default="gemini-3.5-flash")
    parser.add_argument("--models", default="gemini-3.6-flash,gemini-3.5-flash",
                        help="comma-separated readers; first is the immutable primary")
    parser.add_argument("--tag", default="canonical_v1")
    parser.add_argument("--pages", default="", help="comma-separated 1-based pages; default all")
    parser.add_argument("--rebuild", action="store_true",
                        help="reassemble saved raw JSON without new API calls")
    parser.add_argument("--structure-only", action="store_true",
                        help="cache generic structure for routing; do not transcribe values")
    parser.add_argument("--reuse-structure", action="store_true",
                        help="reuse structure JSON+metadata cached by --structure-only")
    args = parser.parse_args()
    pages = [int(value) for value in args.pages.split(",") if value.strip()]
    form_dir = Path(args.form).resolve()
    if args.rebuild:
        result = rebuild(form_dir, args.tag)
    elif args.structure_only:
        result = prepare_structures(form_dir, args.schema_model, args.tag,
                                    pages or None, reuse=args.reuse_structure)
    else:
        result = run(form_dir, args.schema_model,
                     [model.strip() for model in args.models.split(",") if model.strip()],
                     args.tag, pages or None, reuse_structure=args.reuse_structure)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
