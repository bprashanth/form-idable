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


def extract_unique_values(xlsx_bytes: bytes, col_names: list) -> list:
    wb = load_workbook(BytesIO(xlsx_bytes))
    ws = wb.active
    header_row_idx, header_map = _find_header_row(ws)
    if header_row_idx is None:
        return []

    # col_name -> col_int
    name_to_col = {str(v): k for k, v in header_map.items()}
    target_cols = {name_to_col[n] for n in col_names if n in name_to_col}

    values = set()
    for row in ws.iter_rows(min_row=header_row_idx + 1):
        for cell in row:
            if cell.column in target_cols and cell.value is not None:
                v = str(cell.value).strip()
                if v:
                    values.add(v)

    return sorted(values)


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


def apply_serial_numbering(xlsx_bytes: bytes, col_names: list) -> bytes:
    wb = load_workbook(BytesIO(xlsx_bytes))
    ws = wb.active
    header_row_idx, header_map = _find_header_row(ws)
    if header_row_idx is None:
        out = BytesIO()
        wb.save(out)
        return out.getvalue()

    name_to_col = {str(v): k for k, v in header_map.items()}
    target_cols = {name_to_col[n] for n in col_names if n in name_to_col}

    for col_idx in target_cols:
        n = 1
        for row in ws.iter_rows(min_row=header_row_idx + 1):
            cell = next((c for c in row if c.column == col_idx), None)
            if cell and cell.value is not None:
                cell.value = n
                n += 1

    out = BytesIO()
    wb.save(out)
    return out.getvalue()
