import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from config import CHEATSHEET_PATH, SYSTEM_SERIAL_HEADER
from services import excel, fuzzy, matcher

router = APIRouter()


def _load_cheatsheet():
    return json.loads(CHEATSHEET_PATH.read_text(encoding="utf-8"))


@router.post("/infer-types")
async def infer_types(file: UploadFile = File(...)):
    xlsx_bytes = await file.read()
    headers = excel.get_headers(xlsx_bytes)  # already excludes SYSTEM_SERIAL_HEADER
    type_map = fuzzy.infer_types(headers, _load_cheatsheet())
    type_map.pop(SYSTEM_SERIAL_HEADER, None)
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

    try:
        species_with_serials = excel.extract_species_with_system_serials(xlsx_bytes, species_cols)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not species_with_serials:
        return {"proposals": []}

    unique_values = [e["value"] for e in species_with_serials]
    system_serials_map = {e["value"]: e["system_serials"] for e in species_with_serials}

    try:
        proposals = matcher.propose_species_corrections(unique_values)
    except Exception as e:
        raise HTTPException(500, str(e))

    for p in proposals:
        p["system_serials"] = system_serials_map.get(p["original"], [])

    proposals.sort(key=lambda x: x["system_serials"][0] if x["system_serials"] else 9999)

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
    serial_cols = [
        col for col, info in tm.items()
        if info["type"] == "serial" and col != SYSTEM_SERIAL_HEADER
    ]
    if not serial_cols:
        raise HTTPException(400, "No serial columns in type_map")
    corrected, count = excel.apply_serial_numbering(xlsx_bytes, serial_cols)
    return Response(
        content=corrected,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=corrected.xlsx",
            "X-Row-Count": str(count),
            "Access-Control-Expose-Headers": "X-Row-Count",
        },
    )


class LookupRequest(BaseModel):
    query: str


@router.post("/lookup-species")
async def lookup_species(body: LookupRequest):
    if not body.query.strip():
        raise HTTPException(400, "query must not be empty")
    results = matcher.propose_species_corrections([body.query.strip()])
    if not results:
        raise HTTPException(500, "matcher returned no results")
    return results[0]
