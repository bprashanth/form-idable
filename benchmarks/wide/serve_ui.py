#!/usr/bin/env python3
"""Quick-and-dirty Formidable UI against the LOCAL tuned model.

No Fargate, no codex, no cloud: upload a form, it renders tiles, calls the
locally-served Qwen3-VL-2B on :8010, and returns the transcription as a table
plus a downloadable .xlsx. Everything stays on this box.

    python3 serve_ui.py [--port 8080] [--model qwen3-vl-2b-v3]

Then from your laptop:
    ssh -N -L 8080:localhost:8080 <user>@<this-host>
    open http://localhost:8080

Uses the same settings the benchmark measured: per-page requests, tiles at the
1568px vision cap, repetition_penalty 1.05, max_tokens 4096.
"""
import argparse, base64, cgi, html, io, json, os, subprocess, sys, tempfile, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import wide_bench  # noqa: E402

ARGS = None
LAST = {}                                    # token -> (xlsx bytes, name)

PAGE = """<!doctype html><meta charset=utf-8>
<title>Formidable · local</title>
<style>
 body{font:15px/1.5 system-ui,sans-serif;margin:0;background:#0f1115;color:#e6e8ee}
 header{padding:18px 24px;border-bottom:1px solid #222634;display:flex;gap:16px;align-items:baseline}
 h1{font-size:17px;margin:0;font-weight:600}
 .sub{color:#8b93a7;font-size:13px}
 main{padding:24px;max-width:1400px}
 .drop{border:1.5px dashed #39405a;border-radius:10px;padding:28px;text-align:center;background:#151823}
 button{background:#3b6fe0;color:#fff;border:0;border-radius:7px;padding:9px 18px;font-size:14px;cursor:pointer}
 button:disabled{opacity:.5}
 .row{display:flex;gap:20px;margin-top:20px;align-items:flex-start;flex-wrap:wrap}
 .col{flex:1;min-width:380px}
 img{max-width:100%;border-radius:8px;border:1px solid #222634}
 table{border-collapse:collapse;font-size:12.5px;width:100%}
 td,th{border:1px solid #262b3a;padding:3px 7px;text-align:left;vertical-align:top}
 th{background:#1b1f2b}
 tr:nth-child(even) td{background:#141824}
 .meta{color:#8b93a7;font-size:13px;margin:10px 0}
 .err{color:#ff8080;white-space:pre-wrap}
 a.dl{color:#7fb0ff}
 pre{background:#151823;padding:10px;border-radius:8px;overflow:auto;max-height:320px;font-size:12px}
</style>
<header><h1>Formidable</h1><span class=sub>local · %MODEL% · nothing leaves this machine</span></header>
<main>
<form class=drop method=post enctype=multipart/form-data action=/extract>
  <p>Upload a scanned or photographed form (pdf / jpg / png)</p>
  <input type=file name=f accept=".pdf,.jpg,.jpeg,.png,.webp" required>
  <p style="margin-top:14px"><button type=submit>Extract</button></p>
  <p class=sub>Multi-page PDFs are processed a page at a time.</p>
</form>
%BODY%
</main>"""


def render(pdf: Path, workdir: Path):
    """Render page overviews + the half-page tiles the model is fed."""
    import fitz
    (workdir / "pages").mkdir(parents=True, exist_ok=True)
    (workdir / "tiles").mkdir(parents=True, exist_ok=True)
    n = fitz.open(str(pdf)).page_count
    for p in range(1, n + 1):
        subprocess.run([sys.executable, str(wide_bench.RENDER), str(pdf),
                        "--out", str(workdir / "pages" / f"page_{p}.png"),
                        "--page", str(p), "--zoom", "3"],
                       check=True, capture_output=True)
        for h, (y0, y1) in enumerate([(0.0, 0.55), (0.45, 1.0)]):
            subprocess.run([sys.executable, str(wide_bench.RENDER), str(pdf),
                            "--out", str(workdir / "tiles" / f"page_{p}_h{h}.png"),
                            "--page", str(p), "--bbox", f"0,{y0},1,{y1}",
                            "--zoom", "6"], check=True, capture_output=True)
    return n


def to_pdf(src: Path, dst: Path):
    import fitz
    if src.suffix.lower() == ".pdf":
        dst.write_bytes(src.read_bytes()); return
    img = fitz.open(str(src)); rect = img[0].rect
    doc = fitz.open()
    doc.new_page(width=rect.width, height=rect.height).insert_image(rect, filename=str(src))
    doc.save(str(dst)); doc.close(); img.close()


def extract(upload: Path, name: str):
    work = Path(tempfile.mkdtemp(prefix="formidable_"))
    pdf = work / "input.pdf"
    to_pdf(upload, pdf)
    npages = render(pdf, work)
    t0 = time.time()
    text, meta = wide_bench._send_perpage(wide_bench.local_oneshot, ARGS.model,
                                          work, ARGS.endpoint)
    xlsx = wide_bench.text_to_xlsx(text, work / "output.xlsx")
    page_png = (work / "pages" / "page_1.png").read_bytes()
    return {"text": text, "xlsx": Path(xlsx).read_bytes(), "png": page_png,
            "pages": npages, "secs": round(time.time() - t0, 1),
            "out_tok": meta.get("out_tok"), "name": name}


def table_html(text):
    import csv as _csv
    out = []
    for line in text.splitlines():
        if line.strip().lower().startswith("### page"):
            out.append(f"<tr><th colspan=99>{html.escape(line.strip('# '))}</th></tr>")
            continue
        if not line.strip():
            continue
        cells = next(_csv.reader([line]))
        out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in cells) + "</tr>")
    return "<table>" + "".join(out) + "</table>"


class H(BaseHTTPRequestHandler):
    def _send(self, body, code=200, ctype="text/html; charset=utf-8", extra=None):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/dl/"):
            tok = self.path.split("/")[-1]
            if tok in LAST:
                data, nm = LAST[tok]
                return self._send(data, ctype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                  extra={"Content-Disposition": f'attachment; filename="{nm}.xlsx"'})
            return self._send("not found", 404, "text/plain")
        self._send(PAGE.replace("%BODY%", "").replace("%MODEL%", html.escape(ARGS.model)))

    def do_POST(self):
        try:
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                    environ={"REQUEST_METHOD": "POST",
                                             "CONTENT_TYPE": self.headers["Content-Type"]})
            item = form["f"]
            name = os.path.basename(item.filename or "form")
            tmp = Path(tempfile.mkdtemp()) / name
            tmp.write_bytes(item.file.read())
            r = extract(tmp, name)
        except Exception as e:  # noqa: BLE001
            body = f"<p class=err>{html.escape(type(e).__name__)}: {html.escape(str(e)[:500])}</p>"
            return self._send(PAGE.replace("%BODY%", body).replace("%MODEL%", html.escape(ARGS.model)))
        tok = base64.urlsafe_b64encode(os.urandom(9)).decode()
        LAST[tok] = (r["xlsx"], Path(r["name"]).stem)
        img = base64.b64encode(r["png"]).decode()
        body = (f"<div class=meta>{html.escape(r['name'])} · {r['pages']} page(s) · "
                f"{r['secs']}s · {r['out_tok']} output tokens · "
                f"<a class=dl href='/dl/{tok}'>download .xlsx</a></div>"
                f"<div class=row><div class=col><img src='data:image/png;base64,{img}'></div>"
                f"<div class=col>{table_html(r['text'])}"
                f"<details><summary class=sub>raw model output</summary>"
                f"<pre>{html.escape(r['text'][:20000])}</pre></details></div></div>")
        self._send(PAGE.replace("%BODY%", body).replace("%MODEL%", html.escape(ARGS.model)))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--model", default="qwen3-vl-2b-v3")
    ap.add_argument("--endpoint", default="http://localhost:8010/v1")
    ARGS = ap.parse_args()
    print(f"formidable-local on :{ARGS.port} -> {ARGS.model} @ {ARGS.endpoint}")
    ThreadingHTTPServer(("0.0.0.0", ARGS.port), H).serve_forever()
