#!/usr/bin/env python3
"""Synthetic hand-filled form generator for the wide benchmark.

Generates Indian social-sector paper forms: printed structure (title, labelled
header fields, table grids, checkboxes) rendered in a clean font, filled in
with handwriting fonts + per-character jitter, then degraded with a scan-noise
pipeline (rotation, blur, sensor noise, JPEG). Because the fill values are
generated here, the golden xlsx is written from the same values — a perfect
reference with zero human transcription.

Notation conventions (mirrors the benchmark prompt / TreePlots golden rules):
  dot in a cell          -> golden 0
  line struck through    -> golden blank (cell omitted)
  tally marks            -> golden integer
  hand tick / X          -> golden "X"
  empty checkbox         -> golden blank

Usage:  python3 formgen.py <out_root> [seed]
Writes one form dir per spec: <out_root>/<sector>__<name>/{input.pdf,golden.xlsx,provenance.md}
"""
import math, random, sys
from pathlib import Path

import fitz
import openpyxl
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE   = Path(__file__).parent
FONTS  = HERE.parent / "assets/fonts"
PRINT_FONT      = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PRINT_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

HAND_FONTS = [FONTS / f for f in [
    "Kalam-Regular.ttf", "Caveat.ttf", "PatrickHand.ttf", "Mynerve.ttf",
    "GochiHand.ttf", "ShadowsIntoLight.ttf", "Kalam-Light.ttf", "IndieFlower.ttf",
]]

# A4 @ ~180dpi
PORTRAIT, LANDSCAPE = (1488, 2105), (2105, 1488)
INKS = [(20, 24, 84), (16, 16, 40), (28, 24, 120), (10, 10, 10), (40, 30, 90)]


# ── handwriting renderer ──────────────────────────────────────────
class Writer:
    """One 'person': a handwriting font + ink + habits, drawn with per-char jitter."""
    def __init__(self, rng, font_path=None, size=44):
        self.rng = rng
        self.font_path = str(font_path or rng.choice(HAND_FONTS))
        self.size = size
        self.ink = rng.choice(INKS)
        self.slant = rng.uniform(-2.5, 2.5)          # per-writer baseline slant
        self._cache = {}

    def _font(self, size):
        key = int(size)
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(self.font_path, key)
        return self._cache[key]

    def text(self, img, xy, s, size=None, max_w=None):
        """Draw string with per-char jitter; shrink to fit max_w if given."""
        size = size or self.size
        if max_w:
            f = self._font(size)
            w = f.getbbox(s)[2] if s else 0
            while w > max_w and size > 18:
                size = int(size * 0.9)
                f = self._font(size)
                w = f.getbbox(s)[2]
        x, y = xy
        rng = self.rng
        for ch in s:
            f = self._font(int(size * rng.uniform(0.92, 1.08)))
            bbox = f.getbbox(ch)
            cw = max(1, bbox[2] - bbox[0]) if ch.strip() else int(size * 0.30)
            if ch.strip():
                pad = 8
                tile = Image.new("RGBA", (cw + 2 * pad, size * 2 + 2 * pad), (0, 0, 0, 0))
                td = ImageDraw.Draw(tile)
                alpha = rng.randint(190, 245)
                td.text((pad - bbox[0], pad), ch, font=f, fill=(*self.ink, alpha))
                ang = self.slant + rng.uniform(-2.0, 2.0)
                tile = tile.rotate(ang, resample=Image.BICUBIC, expand=True)
                jy = y + rng.uniform(-0.045, 0.045) * size - pad
                img.alpha_composite(tile, (int(x - pad), int(jy)))
            x += cw + rng.uniform(-1, 2.5)
        return x

    def stroke(self, img, pts, width=3):
        """Hand-drawn line through jittered points."""
        d = ImageDraw.Draw(img)
        jpts = [(x + self.rng.uniform(-2, 2), y + self.rng.uniform(-2, 2)) for x, y in pts]
        d.line(jpts, fill=(*self.ink, 230), width=width, joint="curve")

    def tick(self, img, cx, cy, size=18):
        s = size * self.rng.uniform(0.8, 1.3)
        self.stroke(img, [(cx - s * 0.5, cy), (cx - s * 0.1, cy + s * 0.45),
                          (cx + s * 0.7, cy - s * 0.6)], width=3)

    def dot(self, img, cx, cy):
        d = ImageDraw.Draw(img)
        r = self.rng.uniform(3, 5)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*self.ink, 235))

    def strike(self, img, x0, x1, cy):
        n = 6
        pts = [(x0 + (x1 - x0) * i / n, cy + self.rng.uniform(-3, 3)) for i in range(n + 1)]
        self.stroke(img, pts, width=3)

    def tally(self, img, cx, cy, n, h=32, gap=14):
        """Groups of 4 clearly-separated vertical strokes + diagonal for the 5th."""
        x = cx - (min(n, 12) * gap * 0.45)
        i = 0
        while i < n:
            grp = min(4, n - i)
            gx = x
            for k in range(grp):
                jx = self.rng.uniform(-1.5, 1.5)
                self.stroke(img, [(gx + jx, cy - h / 2), (gx + jx + self.rng.uniform(-2, 2), cy + h / 2)], width=3)
                gx += gap
            i += grp
            if grp == 4 and i < n:   # 5th = diagonal across the full group
                self.stroke(img, [(x - 5, cy + h / 2 - 2), (gx - gap + 5, cy - h / 2 + 2)], width=3)
                i += 1
            x = gx + int(gap * 1.6)


# ── page canvas ───────────────────────────────────────────────────
class Page:
    def __init__(self, size):
        self.img = Image.new("RGBA", size, (255, 255, 253, 255))
        self.d = ImageDraw.Draw(self.img)
        self.W, self.H = size

    def ptext(self, xy, s, size=30, bold=False, anchor=None):
        f = ImageFont.truetype(PRINT_FONT_BOLD if bold else PRINT_FONT, size)
        self.d.text(xy, s, font=f, fill=(15, 15, 15), anchor=anchor)

    def line(self, xy0, xy1, w=2):
        self.d.line([xy0, xy1], fill=(60, 60, 60), width=w)

    def rect(self, box, w=2):
        self.d.rectangle(box, outline=(60, 60, 60), width=w)


def scan_noise(img, rng, hard=False):
    """Photocopier/phone-scan degradation. hard=True ~ bad photocopy of a photocopy."""
    img = img.convert("RGB")
    if hard:
        img = img.resize((int(img.width * 0.72), int(img.height * 0.72)), Image.BICUBIC)
    img = img.rotate(rng.uniform(-0.8, 0.8) * (2.2 if hard else 1.0), resample=Image.BICUBIC,
                     expand=False, fillcolor=(250, 250, 248))
    # brightness gradient (uneven lighting)
    grad = Image.new("L", img.size, 0)
    gd = ImageDraw.Draw(grad)
    gx, gy = rng.uniform(0, img.width), rng.uniform(0, img.height)
    maxd = math.hypot(img.width, img.height)
    step = 24
    for yy in range(0, img.height, step):
        for xx in range(0, img.width, step):
            v = int(18 * math.hypot(xx - gx, yy - gy) / maxd)
            gd.rectangle([xx, yy, xx + step, yy + step], fill=v)
    img = Image.composite(Image.new("RGB", img.size, (215, 213, 205)), img,
                          grad.point(lambda v: v))
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.9, 1.3) if hard
                                              else rng.uniform(0.4, 0.8)))
    # sensor noise
    noise = Image.effect_noise(img.size, rng.uniform(9, 16)).convert("L")
    img = Image.blend(img, Image.merge("RGB", (noise, noise, noise)),
                      0.11 if hard else 0.06)
    # JPEG roundtrip
    from io import BytesIO
    buf = BytesIO(); img.save(buf, "JPEG",
                              quality=rng.randint(42, 55) if hard else rng.randint(62, 80))
    return Image.open(BytesIO(buf.getvalue())).convert("RGB")


# ── generic form engine ───────────────────────────────────────────
# cell value specs: ("text",s) ("num",s) ("dot") ("strike") ("tick") ("tally",n) ("blank")
def golden_of(spec):
    kind = spec[0]
    if kind in ("text", "num"): return spec[1]
    if kind == "dot":   return "0"
    if kind == "tick":  return "X"
    if kind == "tally": return str(spec[1])
    return None                                     # strike/blank -> omitted


def draw_cell_value(writer, img, box, spec, size=40):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    kind = spec[0]
    if kind in ("text", "num"):
        s = spec[1]
        f = writer._font(size)
        w = f.getbbox(s)[2]
        writer.text(img, (max(x0 + 8, cx - w / 2), cy - size * 0.62), s,
                    size=size, max_w=x1 - x0 - 14)
    elif kind == "dot":
        writer.dot(img, cx + writer.rng.uniform(-6, 6), cy + writer.rng.uniform(-4, 4))
    elif kind == "strike":
        writer.strike(img, x0 + 8, x1 - 8, cy)
    elif kind == "tick":
        writer.tick(img, cx, cy)
    elif kind == "tally":
        writer.tally(img, cx, cy, spec[1])


def draw_table(page, writer, top, left, right, col_fracs, header, rows,
               row_h=64, header_h=None, hand_size=40, header_size=26):
    """Grid with printed header + hand-filled cells. Returns (bottom_y, golden_rows)."""
    header_h = header_h or row_h
    W = right - left
    xs = [left]
    for f in col_fracs:
        xs.append(xs[-1] + f * W)
    xs[-1] = right
    y = top
    golden = []
    # header
    page.rect([left, y, right, y + header_h])
    for i, h in enumerate(header):
        page.ptext(((xs[i] + xs[i + 1]) / 2, y + header_h / 2), h,
                   size=header_size, bold=True, anchor="mm")
    golden.append(list(header))
    y += header_h
    for row in rows:
        grow = []
        for i, spec in enumerate(row):
            box = (xs[i], y, xs[i + 1], y + row_h)
            draw_cell_value(writer, page.img, box, spec, size=hand_size)
            grow.append(golden_of(spec))
        golden.append(grow)
        y += row_h
    # grid lines
    for gx in xs:
        page.line((gx, top), (gx, y))
    yy = top + header_h
    page.line((left, top), (right, top))
    while yy <= y:
        page.line((left, yy), (right, yy))
        yy += row_h
    return y, golden


def draw_header_fields(page, writer, top, left, right, fields, per_row=2,
                       row_h=70, hand_size=42, label_size=28):
    """label: handwritten-value pairs on dotted lines. Returns (bottom, golden_rows)."""
    golden = []
    colw = (right - left) / per_row
    y = top
    for i in range(0, len(fields), per_row):
        chunk = fields[i:i + per_row]
        for j, (label, spec) in enumerate(chunk):
            x = left + j * colw
            page.ptext((x, y + row_h / 2 - 14), label + ":", size=label_size)
            lf = ImageFont.truetype(PRINT_FONT, label_size)
            lx = x + lf.getbbox(label + ":")[2] + 12
            page.d.line([(lx, y + row_h - 18), (x + colw - 30, y + row_h - 18)],
                        fill=(120, 120, 120), width=1)
            draw_cell_value(writer, page.img, (lx, y, x + colw - 30, y + row_h - 10),
                            spec, size=hand_size)
            g = golden_of(spec)
            golden.append([label, g if g is not None else None])
        y += row_h
    return y, golden


def draw_checkbox_row(page, writer, y, left, label, options, checked, box_sz=30,
                      label_size=28, gap=None):
    """Printed label + option checkboxes; returns golden row [label, opt, X, ...]."""
    page.ptext((left, y), label + ":", size=label_size)
    lf = ImageFont.truetype(PRINT_FONT, label_size)
    x = left + lf.getbbox(label + ":")[2] + 26
    golden = [label]
    for opt in options:
        page.rect([x, y - 2, x + box_sz, y + box_sz - 2])
        if opt == checked:
            writer.tick(page.img, x + box_sz / 2, y + box_sz / 2, size=box_sz * 0.55)
        page.ptext((x + box_sz + 10, y), opt, size=label_size)
        golden.append(opt)
        if opt == checked:
            golden.append("X")
        x += box_sz + 10 + lf.getbbox(opt)[2] + (gap or 46)
    return golden


# ── shared fake-data pools (fictional) ────────────────────────────
FIRST = ["Ramesh", "Sunita", "Lakshmi", "Arjun", "Priya", "Manoj", "Kavita", "Suresh",
         "Anita", "Vijay", "Meena", "Ravi", "Geeta", "Prakash", "Radha", "Santosh",
         "Deepa", "Mahesh", "Savita", "Ganesh", "Rekha", "Dinesh", "Pooja", "Ashok",
         "Sarita", "Rajesh", "Usha", "Kiran", "Shanta", "Mohan"]
LAST  = ["Kumar", "Devi", "Bai", "Patil", "Naik", "Reddy", "Sharma", "Yadav", "Gowda",
         "Das", "Mandal", "Singh", "Rao", "Nayak", "Pawar", "More", "Shinde", "Kale"]
VILLAGES = ["Kotagiri", "Devanhalli", "Sirsi", "Hunsur", "Madikeri", "Puttur",
            "Wayanad", "Bhadravati", "Tumkur", "Hosur", "Palghar", "Karjat"]
CROPS = ["Paddy", "Ragi", "Maize", "Groundnut", "Cotton", "Tur dal", "Jowar",
         "Sugarcane", "Bajra", "Mustard", "Sunflower", "Green gram"]

def _name(rng):  return f"{rng.choice(FIRST)} {rng.choice(LAST)}"
def _date(rng, y=2025):  return f"{rng.randint(1,28):02d}/{rng.randint(1,12):02d}/{y}"
def _mix(rng, p_dot=0.06, p_strike=0.06):
    r = rng.random()
    if r < p_dot: return ("dot",)
    if r < p_dot + p_strike: return ("strike",)
    return None


# ── form specs ────────────────────────────────────────────────────
def form_attendance(rng, writer):
    """Education: monthly attendance register — landscape dense tick grid."""
    pg = Page(LANDSCAPE)
    pg.ptext((pg.W / 2, 60), "GOVERNMENT PRIMARY SCHOOL - MONTHLY ATTENDANCE REGISTER",
             size=40, bold=True, anchor="mm")
    golden = {"header": [], "table": []}
    y, gh = draw_header_fields(pg, writer, 110, 90, pg.W - 90, [
        ("School", ("text", f"GPS {rng.choice(VILLAGES)}")),
        ("Month", ("text", "March 2025")),
        ("Class", ("text", f"Std {rng.randint(1,7)}")),
        ("Teacher", ("text", _name(rng))),
    ])
    golden["header"] = gh
    days = [str(d) for d in range(1, 13)]
    header = ["Roll", "Student Name"] + days + ["Total"]
    col_fracs = [0.05, 0.22] + [0.048] * 12 + [0.075]
    rows = []
    for r in range(1, 15):
        present = [rng.random() > 0.15 for _ in days]
        row = [("num", str(r)), ("text", _name(rng))]
        for pres in present:
            row.append(("tick",) if pres else ("text", "A"))
        row.append(("num", str(sum(present))))
        rows.append(row)
    _, gt = draw_table(pg, writer, y + 20, 90, pg.W - 90, col_fracs, header, rows,
                       row_h=72, hand_size=36, header_size=24)
    golden["table"] = gt
    note = "3 students absent for harvest week"
    writer.text(pg.img, (120, pg.H - 90), note, size=40)
    golden["notes"] = [[note]]
    return [pg], golden


def form_growth(rng, writer):
    """Health: anganwadi child growth monitoring — portrait, decimals."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 70), "ANGANWADI CENTRE - GROWTH MONITORING REGISTER",
             size=34, bold=True, anchor="mm")
    pg.ptext((pg.W / 2, 115), "(Under 5 years - weigh monthly)", size=22, anchor="mm")
    y, gh = draw_header_fields(pg, writer, 150, 80, pg.W - 80, [
        ("AWC Name", ("text", f"AWC {rng.choice(VILLAGES)}")),
        ("Sector", ("text", rng.choice(VILLAGES))),
        ("Worker", ("text", _name(rng))),
        ("Date", ("text", _date(rng))),
    ])
    header = ["S.No", "Child Name", "Age (m)", "Weight kg", "MUAC cm", "Grade", "Referred"]
    col_fracs = [0.07, 0.28, 0.10, 0.14, 0.14, 0.12, 0.15]
    rows = []
    for r in range(1, 13):
        w = round(rng.uniform(6.0, 16.5), 1)
        grade = rng.choices(["N", "MUW", "SUW"], [0.7, 0.2, 0.1])[0]
        rows.append([
            ("num", str(r)), ("text", _name(rng)), ("num", str(rng.randint(6, 59))),
            _mix(rng) or ("num", f"{w:.1f}"),
            _mix(rng) or ("num", f"{round(rng.uniform(10.5,15.9),1):.1f}"),
            ("text", grade),
            ("tick",) if grade == "SUW" else ("strike",),
        ])
    yb, gt = draw_table(pg, writer, y + 30, 80, pg.W - 80, col_fracs, header, rows,
                        row_h=88, hand_size=42)
    cnt = sum(1 for r in rows if r[5][1] == "SUW")
    note = f"{cnt} SUW children referred to PHC"
    writer.text(pg.img, (110, yb + 40), note, size=42)
    return [pg], {"header": gh, "table": gt, "notes": [[note]]}


def form_immunization(rng, writer):
    """Health: immunization session — checkboxes + batch numbers + tallies."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 70), "PHC IMMUNIZATION SESSION RECORD", size=36, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, writer, 130, 80, pg.W - 80, [
        ("PHC", ("text", f"PHC {rng.choice(VILLAGES)}")),
        ("Session Date", ("text", _date(rng))),
        ("ANM Name", ("text", _name(rng))),
        ("Village", ("text", rng.choice(VILLAGES))),
    ])
    golden_cb = []
    y += 30
    pg.ptext((80, y), "Vaccines available this session (tick):", size=28, bold=True)
    y += 56
    for vac, avail in [("BCG", True), ("OPV", True), ("Pentavalent", rng.random() > 0.3),
                       ("Measles-Rubella", rng.random() > 0.3), ("Rotavirus", rng.random() > 0.5)]:
        g = draw_checkbox_row(pg, writer, y, 110, vac, ["Yes", "No"],
                              "Yes" if avail else "No")
        golden_cb.append(g)
        y += 62
    header = ["Vaccine", "Batch No", "Doses given", "Open vials"]
    col_fracs = [0.28, 0.30, 0.24, 0.18]
    rows = []
    for vac in ["BCG", "OPV", "Penta-1", "Penta-3", "MR-1"]:
        rows.append([("text", vac),
                     ("text", f"{rng.choice('ABCDM')}{rng.randint(1000,9999)}"),
                     ("tally", rng.randint(2, 12)),
                     _mix(rng, 0.3, 0.1) or ("num", str(rng.randint(1, 3)))])
    yb, gt = draw_table(pg, writer, y + 30, 80, pg.W - 80, col_fracs, header, rows,
                        row_h=92, hand_size=42)
    note = "cold box temp 4 C checked at 9 am"
    writer.text(pg.img, (110, yb + 40), note, size=40)
    return [pg], {"header": gh, "checkboxes": golden_cb, "table": gt, "notes": [[note]]}


def form_shg_ledger(rng, writer):
    """Livelihoods: SHG savings & loan ledger — dense rupee numeric grid."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 70), "SELF HELP GROUP - MONTHLY SAVINGS & LOAN LEDGER",
             size=32, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, writer, 130, 80, pg.W - 80, [
        ("SHG Name", ("text", f"{rng.choice(['Lakshmi','Durga','Annapurna','Savitri'])} SHG")),
        ("Village", ("text", rng.choice(VILLAGES))),
        ("Meeting Date", ("text", _date(rng))),
        ("President", ("text", _name(rng))),
    ])
    header = ["No", "Member Name", "Savings Rs", "Loan Taken", "Repaid Rs", "Balance Rs"]
    col_fracs = [0.06, 0.30, 0.15, 0.17, 0.15, 0.17]
    rows = []
    for r in range(1, 15):
        sav = rng.choice([50, 100, 100, 150, 200])
        loan = rng.choice([0, 0, 0, 2000, 5000, 10000])
        rep = 0 if loan == 0 else rng.choice([200, 500, 1000])
        bal = loan - rep if loan else 0
        rows.append([
            ("num", str(r)), ("text", _name(rng)), ("num", str(sav)),
            ("dot",) if loan == 0 else ("num", str(loan)),
            ("strike",) if loan == 0 else ("num", str(rep)),
            ("dot",) if loan == 0 else ("num", str(bal)),
        ])
    yb, gt = draw_table(pg, writer, y + 30, 80, pg.W - 80, col_fracs, header, rows,
                        row_h=84, hand_size=42)
    tot = sum(int(r[2][1]) for r in rows)
    note = f"Total savings collected Rs {tot}"
    writer.text(pg.img, (110, yb + 40), note, size=44)
    return [pg], {"header": gh, "table": gt, "notes": [[note.replace('Rs', 'Rs')]]}


def form_muster(rng, writer):
    """Livelihoods: MGNREGA muster roll — landscape, job-card IDs + day grid + wages."""
    pg = Page(LANDSCAPE)
    pg.ptext((pg.W / 2, 60), "MGNREGA MUSTER ROLL - WEEKLY", size=40, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, writer, 110, 90, pg.W - 90, [
        ("Gram Panchayat", ("text", rng.choice(VILLAGES))),
        ("Work", ("text", rng.choice(["Pond desilting", "Road repair", "Bund construction"]))),
        ("Muster No", ("text", f"MR-{rng.randint(100,999)}")),
        ("Week", ("text", "10/03/2025 - 15/03/2025")),
    ])
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    header = ["No", "Job Card No", "Worker Name"] + days + ["Days", "Wage Rs"]
    col_fracs = [0.045, 0.16, 0.20] + [0.055] * 6 + [0.07, 0.115]
    rows = []
    for r in range(1, 13):
        present = [rng.random() > 0.2 for _ in days]
        nd = sum(present)
        row = [("num", str(r)),
               ("text", f"KA-{rng.randint(10,99)}-{rng.randint(1000,9999)}"),
               ("text", _name(rng))]
        row += [("tick",) if p else ("dot",) for p in present]
        row += [("num", str(nd)), ("num", str(nd * 309))]
        rows.append(row)
    _, gt = draw_table(pg, writer, y + 20, 90, pg.W - 90, col_fracs, header, rows,
                       row_h=76, hand_size=36, header_size=24)
    note = "wage rate Rs 309 per day"
    writer.text(pg.img, (120, pg.H - 80), note, size=40)
    return [pg], {"header": gh, "table": gt, "notes": [[note]]}


def form_crop(rng, writer):
    """Agriculture: field crop survey — mixed text + numbers + remark sentences."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 70), "KHARIF CROP SURVEY - FIELD RECORD", size=36, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, writer, 130, 80, pg.W - 80, [
        ("District", ("text", rng.choice(["Mysuru", "Hassan", "Shivamogga", "Belagavi"]))),
        ("Taluk", ("text", rng.choice(VILLAGES))),
        ("Surveyor", ("text", _name(rng))),
        ("Date", ("text", _date(rng))),
    ])
    header = ["Plot No", "Farmer", "Crop", "Area ac", "Irrigated", "Yield q", "Remarks"]
    col_fracs = [0.09, 0.20, 0.14, 0.10, 0.11, 0.10, 0.26]
    remarks = ["pest attack seen", "good crop", "needs urea", "late sowing",
               "borewell dry", "lodging in patches", ""]
    rows = []
    for r in range(1, 11):
        rem = rng.choice(remarks)
        rows.append([
            ("text", f"{rng.randint(1,99)}/{rng.choice('AB')}"),
            ("text", _name(rng)), ("text", rng.choice(CROPS)),
            ("num", f"{round(rng.uniform(0.5, 5.0), 1)}"),
            ("tick",) if rng.random() > 0.4 else ("strike",),
            _mix(rng, 0.08, 0.1) or ("num", str(rng.randint(2, 28))),
            ("text", rem) if rem else ("strike",),
        ])
    yb, gt = draw_table(pg, writer, y + 30, 80, pg.W - 80, col_fracs, header, rows,
                        row_h=96, hand_size=38)
    note = "rain damaged 2 plots in low area"
    writer.text(pg.img, (110, yb + 40), note, size=42)
    return [pg], {"header": gh, "table": gt, "notes": [[note]]}


def form_grades(rng, writer):
    """Education: exam grade sheet — dense numeric grid + totals + letter grades."""
    pg = Page(PORTRAIT)
    pg.ptext((pg.W / 2, 70), "ANNUAL EXAMINATION - MARKS REGISTER", size=36, bold=True, anchor="mm")
    y, gh = draw_header_fields(pg, writer, 130, 80, pg.W - 80, [
        ("School", ("text", f"GHS {rng.choice(VILLAGES)}")),
        ("Class", ("text", f"Std {rng.randint(5,10)}")),
        ("Year", ("text", "2024-25")),
        ("Class Teacher", ("text", _name(rng))),
    ])
    subs = ["Kan", "Eng", "Math", "Sci", "SS"]
    header = ["Roll", "Student Name"] + subs + ["Total", "Grade"]
    col_fracs = [0.07, 0.27] + [0.09] * 5 + [0.11, 0.10]
    rows = []
    for r in range(1, 15):
        marks = [rng.randint(18, 98) for _ in subs]
        tot = sum(marks)
        pct = tot / (len(subs) * 100)
        grade = "A" if pct > 0.85 else "B" if pct > 0.7 else "C" if pct > 0.5 else "D"
        row = [("num", str(r)), ("text", _name(rng))]
        row += [("num", str(m)) for m in marks]
        row += [("num", str(tot)), ("text", grade)]
        rows.append(row)
    yb, gt = draw_table(pg, writer, y + 30, 80, pg.W - 80, col_fracs, header, rows,
                        row_h=80, hand_size=40)
    note = "2 students absent - marks pending"
    writer.text(pg.img, (110, yb + 40), note, size=42)
    return [pg], {"header": gh, "table": gt, "notes": [[note]]}


def form_opd(rng, writer):
    """Health: OPD register — two-page portrait, short diagnosis sentences."""
    pages, golden = [], {"header": [], "table": [], "notes": []}
    header = ["No", "Patient Name", "Age", "M/F", "Complaint", "Diagnosis", "Treatment"]
    col_fracs = [0.06, 0.20, 0.07, 0.07, 0.20, 0.20, 0.20]
    complaints = ["fever 3 days", "cough", "body pain", "loose motion", "headache",
                  "wound on leg", "weakness", "stomach pain", "back pain", "cold"]
    dx = ["viral fever", "URTI", "myalgia", "AGE", "migraine", "cellulitis",
          "anaemia", "gastritis", "lumbago", "common cold"]
    rx = ["PCM 500", "cough syrup", "PCM + rest", "ORS + zinc", "PCM 650",
          "dressing + amox", "IFA tabs", "antacid", "diclofenac", "CPM"]
    n = 1
    for pgno in range(2):
        pg = Page(PORTRAIT)
        if pgno == 0:
            pg.ptext((pg.W / 2, 70), "PRIMARY HEALTH CENTRE - OPD REGISTER",
                     size=36, bold=True, anchor="mm")
            y, gh = draw_header_fields(pg, writer, 130, 80, pg.W - 80, [
                ("PHC", ("text", f"PHC {rng.choice(VILLAGES)}")),
                ("Date", ("text", _date(rng))),
                ("Doctor", ("text", f"Dr {_name(rng)}")),
                ("OPD Total", ("num", "23")),
            ])
            golden["header"] = gh
        else:
            pg.ptext((pg.W / 2, 70), "OPD REGISTER (contd)", size=32, bold=True, anchor="mm")
            y = 110
        rows = []
        for _ in range(11 if pgno == 0 else 12):
            i = rng.randrange(len(complaints))
            rows.append([
                ("num", str(n)), ("text", _name(rng)), ("num", str(rng.randint(1, 80))),
                ("text", rng.choice(["M", "F"])),
                ("text", complaints[i]), ("text", dx[i]),
                _mix(rng, 0.05, 0.08) or ("text", rx[i]),
            ])
            n += 1
        yb, gt = draw_table(pg, writer, y + 30, 80, pg.W - 80, col_fracs, header, rows,
                            row_h=92, hand_size=36)
        golden["table"] += gt if pgno == 0 else gt[1:]   # skip repeated header once
        pages.append(pg)
    note = "2 referred to taluk hospital"
    writer.text(pages[-1].img, (110, yb + 40), note, size=42)
    golden["notes"] = [[note]]
    return pages, golden


def form_vaccination_cards(rng, writer):
    """Multi-form-per-page stress: two child vaccination cards on one page."""
    pg = Page(PORTRAIT)
    golden = {"header": [], "table": [], "notes": []}
    vaccines = ["BCG", "OPV-0", "Penta-1", "Penta-2", "Penta-3", "MR-1"]
    for half in range(2):
        top = 60 + half * (PORTRAIT[1] // 2)
        left, right = 80, pg.W - 80
        pg.rect([left - 20, top - 20, right + 20, top + PORTRAIT[1] // 2 - 60], w=3)
        pg.ptext((pg.W / 2, top + 10), "CHILD VACCINATION CARD", size=32, bold=True, anchor="mm")
        y, gh = draw_header_fields(pg, writer, top + 40, left, right, [
            ("Child Name", ("text", _name(rng))),
            ("DOB", ("text", _date(rng, y=2024))),
            ("Mother", ("text", _name(rng))),
            ("Reg No", ("text", f"RCH{rng.randint(10000,99999)}")),
        ])
        golden["header"] += gh
        header = ["Vaccine", "Due Date", "Given Date", "Given"]
        col_fracs = [0.28, 0.26, 0.26, 0.20]
        rows = []
        for v in vaccines:
            given = rng.random() > 0.3
            rows.append([("text", v), ("text", _date(rng, y=2024)),
                         ("text", _date(rng, y=2024)) if given else ("strike",),
                         ("tick",) if given else ("strike",)])
        _, gt = draw_table(pg, writer, y + 16, left, right, col_fracs, header, rows,
                           row_h=64, hand_size=34, header_size=24)
        golden["table"] += gt if half == 0 else gt[1:]
    return [pg], golden


FORMS = {
    "education__attendance":   (form_attendance, "Monthly school attendance register (landscape tick grid, A=absent)"),
    "education__grades":       (form_grades, "Annual exam marks register (dense numeric grid)"),
    "health__growth":          (form_growth, "Anganwadi growth monitoring (decimals, strike-through, referral ticks)"),
    "health__immunization":    (form_immunization, "PHC immunization session (checkboxes, batch codes, tally marks)"),
    "health__opd":             (form_opd, "PHC OPD register, 2 pages (short clinical phrases)"),
    "health__vaccination_cards": (form_vaccination_cards, "Two vaccination cards on one page (multi-form stress)"),
    "livelihoods__shg_ledger": (form_shg_ledger, "SHG savings & loan ledger (rupee amounts, dots=0, strikes)"),
    "livelihoods__muster_roll": (form_muster, "MGNREGA muster roll (landscape, job-card IDs, tick/dot day grid)"),
    "agriculture__crop_survey": (form_crop, "Kharif crop survey (mixed text/number, remark phrases)"),
}


# ── golden writer ─────────────────────────────────────────────────
def write_golden(golden, dst):
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    for sheet in ["header", "checkboxes", "table", "notes"]:
        rows = golden.get(sheet)
        if not rows: continue
        ws = wb.create_sheet(sheet)
        for r in rows:
            ws.append([c for c in r] if isinstance(r, list) else [r])
    wb.save(dst)


MESSY_FONTS = [FONTS / f for f in
               ["HomemadeApple.ttf", "ReenieBeanie.ttf", "Caveat.ttf", "Mynerve.ttf"]]


def generate(out_root: Path, seed=7, only=None, hard=False):
    # Per-form font overrides where the default rng pick proved illegible in QA
    # (vaccination_cards' cursive capital G read as digit 6 -> "BC6").
    FONT_OVERRIDE = {"health__vaccination_cards": FONTS / "PatrickHand.ttf"}
    for name, (fn, desc) in FORMS.items():
        if only and name != only: continue
        rng = random.Random(f"{seed}:{name}:hard" if hard else f"{seed}:{name}")
        writer = Writer(rng, font_path=rng.choice(MESSY_FONTS) if hard
                        else FONT_OVERRIDE.get(name))
        pages, golden = fn(rng, writer)
        d = out_root / (f"{name}_hard" if hard else name)
        d.mkdir(parents=True, exist_ok=True)
        doc = fitz.open()
        for pg in pages:
            img = scan_noise(pg.img, rng, hard=hard)
            tmp = d / "_tmp_page.jpg"
            img.save(tmp, "JPEG", quality=88)
            rect = fitz.Rect(0, 0, img.width * 72 / 180, img.height * 72 / 180)
            page = doc.new_page(width=rect.width, height=rect.height)
            page.insert_image(rect, filename=str(tmp))
        doc.save(d / "input.pdf"); doc.close()
        (d / "_tmp_page.jpg").unlink(missing_ok=True)
        write_golden(golden, d / "golden.xlsx")
        (d / "provenance.md").write_text(
            f"# {name}{' (HARD variant)' if hard else ''}\n\nSYNTHETIC form, generated "
            f"by benchmarks/wide/gen/formgen.py (seed {seed}"
            f"{', hard mode: messy cursive font, 0.72x resolution, heavy blur/noise/JPEG' if hard else ''}).\n"
            f"{desc}.\n\nPrinted structure: DejaVu Sans. Handwriting: "
            f"{Path(writer.font_path).name} with per-char jitter, ink {writer.ink}, "
            f"scan-noise pipeline (rotation/blur/noise/JPEG).\nGolden built "
            f"programmatically from the generated fill values — exact by construction.\n"
            f"All names/values fictional. Licence: generated, no restrictions.\n")
        print(f"generated {name}: {len(pages)} page(s), "
              f"{sum(len(v) for v in golden.values())} golden rows")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--hard"]
    hard = "--hard" in sys.argv
    out = Path(args[0]) if args else HERE.parent / "forms"
    seed = int(args[1]) if len(args) > 1 else 7
    only = args[2] if len(args) > 2 else None
    generate(out, seed, only, hard=hard)
