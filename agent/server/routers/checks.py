import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from config import CHEATSHEET_PATH
from services import excel, fuzzy, llm

router = APIRouter()


def _load_cheatsheet():
    return json.loads(CHEATSHEET_PATH.read_text(encoding="utf-8"))


@router.post("/infer-types")
async def infer_types(file: UploadFile = File(...)):
    xlsx_bytes = await file.read()
    headers = excel.get_headers(xlsx_bytes)
    type_map = fuzzy.infer_types(headers, _load_cheatsheet())
    return {"type_map": type_map, "all_headers": headers}


@router.post("/check-species")
async def check_species(
    file: UploadFile = File(...),
    type_map: str = Form(...),
):
    xlsx_bytes = await file.read()
    tm = json.loads(type_map)
    species_cols = [col for col, info in tm.items() if info["type"] == "species"]
    if not species_cols:
        raise HTTPException(400, "No species columns in type_map")

    unique_values = excel.extract_unique_values(xlsx_bytes, species_cols)
    if not unique_values:
        return {"proposals": []}

    try:
        proposals = llm.propose_species_corrections(unique_values)
    except Exception as e:
        raise HTTPException(500, str(e))

    return {"proposals": proposals}


@router.post("/apply-species")
async def apply_species(
    file: UploadFile = File(...),
    type_map: str = Form(...),
    corrections: str = Form(...),
):
    xlsx_bytes = await file.read()
    tm = json.loads(type_map)
    corr = json.loads(corrections)
    species_cols = [col for col, info in tm.items() if info["type"] == "species"]
    corrected = excel.apply_species_corrections(xlsx_bytes, species_cols, corr)
    return Response(
        content=corrected,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=corrected.xlsx"},
    )


@router.post("/check-serial")
async def check_serial(
    file: UploadFile = File(...),
    type_map: str = Form(...),
):
    xlsx_bytes = await file.read()
    tm = json.loads(type_map)
    serial_cols = [col for col, info in tm.items() if info["type"] == "serial"]
    if not serial_cols:
        raise HTTPException(400, "No serial columns in type_map")
    corrected = excel.apply_serial_numbering(xlsx_bytes, serial_cols)
    return Response(
        content=corrected,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=corrected.xlsx"},
    )
