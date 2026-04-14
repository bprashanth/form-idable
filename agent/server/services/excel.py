from io import BytesIO
from openpyxl import load_workbook


def _find_header_row(ws):
    """Return (row_idx, {col_int: col_name}) for the first row with 2+ bold cells."""
    for row in ws.iter_rows():
        bold = [(c.column, c.value) for c in row if c.value is not None and c.font and c.font.bold]
        if len(bold) >= 2:
            return row[0].row, {col: val for col, val in bold}
    return None, {}


def get_headers(xlsx_bytes: bytes) -> list:
    wb = load_workbook(BytesIO(xlsx_bytes))
    _, header_map = _find_header_row(wb.active)
    return [str(v) for v in header_map.values()]


def extract_species_with_serial(
    xlsx_bytes: bytes, species_cols: list, serial_cols: list
) -> list:
    """
    Walk rows once and collect unique species values alongside the serial number
    of the first row they appear in (post serial-correction, serial values are
    clean integers 1-N).  Falls back to row index when no serial column exists.

    Returns [{"value": str, "first_serial": int}] in insertion order.
    """
    wb = load_workbook(BytesIO(xlsx_bytes))
    ws = wb.active
    header_row_idx, header_map = _find_header_row(ws)
    if header_row_idx is None:
        return []

    name_to_col = {str(v): k for k, v in header_map.items()}
    species_col_idxs = {name_to_col[n] for n in species_cols if n in name_to_col}
    serial_col_idx = next(
        (name_to_col[n] for n in serial_cols if n in name_to_col), None
    )

    seen: dict = {}
    row_num = 1
    for row in ws.iter_rows(min_row=header_row_idx + 1):
        row_by_col = {c.column: c for c in row}

        serial = row_num  # fallback when no serial column or bad value
        if serial_col_idx and serial_col_idx in row_by_col:
            sv = row_by_col[serial_col_idx].value
            if sv is not None:
                try:
                    serial = int(sv)
                except (ValueError, TypeError):
                    pass

        for cell in row:
            if cell.column in species_col_idxs and cell.value is not None:
                v = str(cell.value).strip()
                if v and v not in seen:
                    seen[v] = serial

        row_num += 1

    return [{"value": v, "first_serial": s} for v, s in seen.items()]


def apply_species_corrections(xlsx_bytes: bytes, col_names: list, corrections: list) -> bytes:
    """corrections: [{original, corrected}] — only the confirmed ones."""
    correction_map = {c["original"]: c["corrected"] for c in corrections if c.get("corrected")}

    wb = load_workbook(BytesIO(xlsx_bytes))
    ws = wb.active
    header_row_idx, header_map = _find_header_row(ws)
    if header_row_idx is None:
        out = BytesIO()
        wb.save(out)
        return out.getvalue()

    name_to_col = {str(v): k for k, v in header_map.items()}
    target_cols = {name_to_col[n] for n in col_names if n in name_to_col}

    for row in ws.iter_rows(min_row=header_row_idx + 1):
        for cell in row:
            if cell.column in target_cols and cell.value is not None:
                v = str(cell.value).strip()
                if v in correction_map:
                    cell.value = correction_map[v]

    out = BytesIO()
    wb.save(out)
    return out.getvalue()


def apply_serial_numbering(xlsx_bytes: bytes, col_names: list) -> tuple:
    """Returns (corrected_bytes, row_count) where row_count is the number of
    data rows renumbered (same across all serial columns)."""
    wb = load_workbook(BytesIO(xlsx_bytes))
    ws = wb.active
    header_row_idx, header_map = _find_header_row(ws)
    if header_row_idx is None:
        out = BytesIO()
        wb.save(out)
        return out.getvalue(), 0

    name_to_col = {str(v): k for k, v in header_map.items()}
    target_cols = {name_to_col[n] for n in col_names if n in name_to_col}

    count = 0
    for col_idx in target_cols:
        n = 1
        for row in ws.iter_rows(min_row=header_row_idx + 1):
            cell = next((c for c in row if c.column == col_idx), None)
            if cell and cell.value is not None:
                cell.value = n
                n += 1
        count = n - 1

    out = BytesIO()
    wb.save(out)
    return out.getvalue(), count
