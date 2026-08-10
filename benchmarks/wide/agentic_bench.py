#!/usr/bin/env python3
"""Give ANY vision model the crop/zoom loop that codex uses.

Until now the comparison was unfair: codex got an agentic harness (render a
page, look, crop into a region, look again) while every API model got a single
shot at fixed tiles. That conflates "model quality" with "harness quality".
This runs an arbitrary OpenRouter/Gemini model through the SAME strategy —
same tool, same instructions — so the two can be separated.

The tool is `render_page(page, bbox, zoom)`, identical in contract to the one
codex is given in production (`good-shepherd/agents/formidable/tools/render_page.py`):
bbox is FRACTIONS of the page, output is capped at 1568px on the long edge.

Vision-in-tool-results is not in the OpenAI spec, so the crop comes back as a
short text acknowledgement plus a fresh user message carrying the image — the
standard workaround, and what the model actually needs.

Usage:
  python3 agentic_bench.py --form eval_forms/eval_02 \
      --provider openrouter --model qwen/qwen3-vl-32b-instruct [--max-turns 10]
"""
import argparse, base64, json, subprocess, sys, tempfile, time, urllib.error
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import wide_bench, wide_diff  # noqa: E402

# A TEXT protocol rather than the tools API. Two reasons: provider support for
# images-in-tool-results is inconsistent (OpenRouter returned "Invalid image
# data-url" for a perfectly valid PNG once tool messages were in the history),
# and only ~half the vision roster advertises tool support at all. A text
# directive works with every vision model, which is the point of this harness.
SYSTEM = """You are transcribing a scanned hand-filled paper form into CSV.

You may look closer at any region before answering. To do that, reply with
EXACTLY one line and nothing else:

CROP page=<n> bbox=<x0,y0,x1,y1> zoom=<z>

where bbox is fractions of the page (0-1) and zoom is 1-8. You will be shown
that region and may crop again. Strategy that works: view each page whole
(zoom 2) first to understand the layout, then crop into each table block and
header at zoom 5-8 to read the handwriting. Values illegible at low zoom are
usually readable after a crop.

Notation: a lone dot means 0; a line struck through a cell means no entry;
tally marks sum to an integer; a tick or X means X.

When you have seen enough, reply with the FULL transcription as CSV and nothing
else — one row per line, cells comma-separated, `### PAGE N` before each page.
Never mix a CROP line with transcription. Do not explain what you are doing.
"""

SYSTEM_PAGE = SYSTEM.replace(
    "`### PAGE N` before each page.", "no page marker.").replace(
    "Transcribe this", "Transcribe this page of a")

CROP_RE = __import__("re").compile(
    r"CROP\s+page\s*=\s*(\d+)(?:.*?bbox\s*=\s*([0-9.,\s]+))?(?:.*?zoom\s*=\s*([0-9.]+))?",
    __import__("re").I)


def normalise_bbox(bbox: str | None):
    """Accept the pixel coordinates models keep sending instead of fractions.

    Every model tried so far eventually emits something like
    `bbox=82,175,915,300` despite being told fractions. render_page then clips
    to an empty region and writes a 0-BYTE png, which the provider rejects as
    "Invalid image data-url" — an error that points nowhere near the cause.
    If any component is > 1 we treat the whole box as pixels and rescale by the
    largest value, which recovers the intended region well enough to be useful.
    Returns (bbox_string_or_None, note_for_the_model).
    """
    if not bbox:
        return None, ""
    try:
        v = [float(x) for x in bbox.split(",")]
    except ValueError:
        return None, "bbox unparseable; using whole page"
    if len(v) != 4:
        return None, "bbox needs 4 numbers; using whole page"
    if max(v) > 1.0:
        s = max(v)
        v = [x / s for x in v]
        note = "(your bbox looked like pixels; converted to fractions)"
    else:
        note = ""
    x0, y0, x1, y1 = v
    x0, x1 = sorted((max(0.0, min(1.0, x0)), max(0.0, min(1.0, x1))))
    y0, y1 = sorted((max(0.0, min(1.0, y0)), max(0.0, min(1.0, y1))))
    if x1 - x0 < 0.02 or y1 - y0 < 0.02:            # degenerate -> whole page
        return None, "bbox was empty; showing the whole page"
    return f"{x0:.4f},{y0:.4f},{x1:.4f},{y1:.4f}", note


def render(pdf: Path, page: int, bbox: str | None, zoom: float, out: Path):
    cmd = [sys.executable, str(wide_bench.RENDER), str(pdf), "--out", str(out),
           "--page", str(page), "--zoom", str(zoom)]
    if bbox:
        cmd += ["--bbox", bbox]
    r = subprocess.run(cmd, capture_output=True, text=True)
    # exists() is NOT enough: a clipped-to-nothing region still writes a
    # 0-byte file, which then poisons the request.
    ok = out.exists() and out.stat().st_size > 1024
    return ok, (r.stdout or r.stderr).strip()[:200]


MAX_LIVE_IMAGES = 3


def prune_images(msgs, keep=MAX_LIVE_IMAGES):
    """Keep only the most recent `keep` images in the history.

    Each crop is ~1-1.5 MB of base64. After a few turns the request exceeds the
    provider's size limit, which OpenRouter reports as the very misleading
    "Invalid image data-url" — the images are fine, the request is too big.
    Older crops are replaced by a text stub so the model still remembers what
    it looked at, and the cost per turn stops growing.
    """
    idx = [i for i, m in enumerate(msgs)
           if isinstance(m.get("content"), list)
           and any(p.get("type") == "image_url" for p in m["content"])]
    for i in idx[:-keep] if len(idx) > keep else []:
        label = next((p.get("text", "") for p in msgs[i]["content"]
                      if p.get("type") == "text"), "region")
        msgs[i] = {"role": "user", "content": f"[earlier crop: {label} — already reviewed]"}
    return msgs


def run_perpage(form_dir: Path, provider: str, model: str, max_turns=4, endpoint=None):
    """Agentic loop scoped to ONE page at a time.

    Whole-document agentic runs stop early: the first model cropped 3 regions of
    page 1, declared itself finished, and never looked at pages 2-3 (recall
    0.276 with precision 0.987). Scoping the loop per page guarantees coverage,
    so what remains measures the thing we actually care about — whether letting
    a model zoom beats handing it fixed tiles.
    """
    import fitz
    pdf = form_dir / "input.pdf"
    npages = fitz.open(str(pdf)).page_count
    work = Path(tempfile.mkdtemp(prefix="agentic_pp_"))
    parts, cost, crops, t0 = [], 0.0, 0, time.time()
    for pg in range(1, npages + 1):
        base = work / f"p{pg}.png"
        render(pdf, pg, None, 3, base)
        msgs = [{"role": "system", "content": SYSTEM_PAGE},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Page {pg} of {npages}. Transcribe it."},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{wide_bench._b64(base)}"}}]}]
        got = ""
        for _ in range(max_turns):
            prune_images(msgs)
            try:
                resp, c = _chat(provider, model, msgs, endpoint)
            except Exception:
                break
            cost += c
            txt = (resp["choices"][0]["message"].get("content") or "").strip()
            msgs.append({"role": "assistant", "content": txt})
            mo = CROP_RE.search(txt)
            if not mo or len(txt) > 400:
                got = txt
                break
            bbox, bnote = normalise_bbox((mo.group(2) or "").strip().rstrip(","))
            out = work / f"p{pg}_c{crops}.png"; crops += 1
            ok, note = render(pdf, pg, bbox, max(1.0, min(8.0, float(mo.group(3) or 5))), out)
            if not ok:
                msgs.append({"role": "user", "content":
                             "that region was empty; bbox must be FRACTIONS 0-1"})
                continue
            msgs.append({"role": "user", "content": [
                {"type": "text", "text": f"zoomed: bbox={bbox or 'full'} {bnote}"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{wide_bench._b64(out)}"}}]})
        if not got:
            msgs.append({"role": "user", "content": "Output the CSV for this page now."})
            prune_images(msgs)
            try:
                resp, c = _chat(provider, model, msgs, endpoint); cost += c
                got = (resp["choices"][0]["message"].get("content") or "").strip()
            except Exception:
                got = ""
        parts.append(f"### PAGE {pg}\n{got}")
    final = "\n".join(parts)
    dt = time.time() - t0
    out_dir = form_dir / "outputs"; out_dir.mkdir(exist_ok=True)
    tag = f"{provider}__{model.replace('/', '_')}__agentic-pp"
    (out_dir / f"{tag}.txt").write_text(final)
    xlsx = wide_bench.text_to_xlsx(final, out_dir / f"{tag}.xlsx")
    res = wide_diff.compare(str(form_dir / "golden.xlsx"), str(xlsx))
    row = {"form": form_dir.name, "provider": provider, "model": model,
           "mode": "agentic-pp", "passed": res["passed"], "crops": crops,
           "cost_usd": round(cost, 5), "latency_s": round(dt, 1), "error": ""}
    row.update({k: v for k, v in res["metrics"].items()
                if k not in ("golden_cells", "candidate_cells")})
    (out_dir / f"{tag}.json").write_text(json.dumps(row, indent=2))
    return row, None


def run(form_dir: Path, provider: str, model: str, max_turns=10, endpoint=None):
    import fitz
    pdf = form_dir / "input.pdf"
    npages = fitz.open(str(pdf)).page_count
    work = Path(tempfile.mkdtemp(prefix="agentic_"))

    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content":
             f"Transcribe this {npages}-page form. Start by rendering page 1."}]
    cost, t0, crops = 0.0, time.time(), 0
    final = ""

    for turn in range(max_turns):
        prune_images(msgs)
        try:
            resp, c = _chat(provider, model, msgs, endpoint)
        except urllib.error.HTTPError as e:
            return None, f"HTTP {e.code}: {e.read().decode()[:200]}"
        cost += c
        content = (resp["choices"][0]["message"].get("content") or "").strip()
        msgs.append({"role": "assistant", "content": content})
        mo = CROP_RE.search(content)
        # a CROP directive only counts if the reply is essentially JUST that —
        # otherwise the model has started transcribing and merely mentioned it
        if not mo or len(content) > 400:
            final = content
            break
        pg = max(1, min(npages, int(mo.group(1))))
        bbox, bnote = normalise_bbox((mo.group(2) or "").strip().rstrip(","))
        zoom = float(mo.group(3) or 2)
        out = work / f"c{crops}.png"
        ok, note = render(pdf, pg, bbox, max(1.0, min(8.0, zoom)), out)
        crops += 1
        if not ok:
            msgs.append({"role": "user",
                         "content": f"that region rendered empty ({note}); bbox must be "
                                    f"FRACTIONS of the page between 0 and 1, e.g. "
                                    f"bbox=0,0.3,1,0.6 . Try again."})
            continue
        msgs.append({"role": "user", "content": [
            {"type": "text", "text": f"page {pg} bbox={bbox or 'full'} zoom={zoom} {bnote}"},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{wide_bench._b64(out)}"}}]})
    if not final:                                   # ran out of turns — ask directly
        msgs.append({"role": "user",
                     "content": "Stop looking. Output the full CSV transcription now."})
        prune_images(msgs)
        try:
            resp, c = _chat(provider, model, msgs, endpoint)
            cost += c
            final = resp["choices"][0]["message"].get("content") or ""
        except Exception:
            pass

    dt = time.time() - t0
    out_dir = form_dir / "outputs"; out_dir.mkdir(exist_ok=True)
    tag = f"{provider}__{model.replace('/', '_')}__agentic"
    (out_dir / f"{tag}.txt").write_text(final)
    xlsx = wide_bench.text_to_xlsx(final, out_dir / f"{tag}.xlsx")
    res = wide_diff.compare(str(form_dir / "golden.xlsx"), str(xlsx))
    row = {"form": form_dir.name, "provider": provider, "model": model,
           "mode": "agentic", "passed": res["passed"], "crops": crops,
           "turns": turn + 1, "cost_usd": round(cost, 5),
           "latency_s": round(dt, 1), "error": ""}
    row.update({k: v for k, v in res["metrics"].items()
                if k not in ("golden_cells", "candidate_cells")})
    (out_dir / f"{tag}.json").write_text(json.dumps(row, indent=2))
    return row, None


def _chat(provider, model, msgs, endpoint=None):
    if provider == "openrouter":
        key = wide_bench._key("openrouter")
        payload = {"model": model, "temperature": 0, "messages": msgs,
                   "usage": {"include": True}, "max_tokens": 6000}
        r = wide_bench._post("https://openrouter.ai/api/v1/chat/completions", payload,
                             {"Authorization": f"Bearer {key}",
                              "HTTP-Referer": "https://formidable.local",
                              "X-Title": "formidable-agentic"}, timeout=600)
        return r, (r.get("usage", {}) or {}).get("cost") or 0.0
    if provider == "local":
        payload = {"model": model, "temperature": 0, "messages": msgs,
                   "max_tokens": 4096}
        r = wide_bench._post(f"{(endpoint or 'http://localhost:8010/v1').rstrip('/')}"
                             f"/chat/completions", payload, {}, timeout=900)
        return r, 0.0
    raise SystemExit(f"provider {provider} not supported for the agentic loop")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--provider", default="openrouter")
    ap.add_argument("--model", required=True)
    ap.add_argument("--max-turns", type=int, default=10)
    ap.add_argument("--endpoint", default=None)
    ap.add_argument("--per-page", action="store_true",
                    help="scope the crop loop to one page at a time (guarantees coverage)")
    a = ap.parse_args()
    fn = run_perpage if a.per_page else run
    r, err = fn(Path(a.form).resolve(), a.provider, a.model, a.max_turns, a.endpoint)
    print(json.dumps(r) if r else f"ERROR: {err}")
