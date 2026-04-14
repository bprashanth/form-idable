import csv

from fastapi import APIRouter
from pydantic import BaseModel

from config import SPECIES_CSV_PATH

router = APIRouter()


class SpeciesEntry(BaseModel):
    abbr: str
    expanded: str
    toda_name: str = "NA"


@router.get("/species-db")
async def get_species_db():
    rows = []
    with open(SPECIES_CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({
                "abbr": row["Species name Abbr"],
                "expanded": row["Species name expanded"],
                "toda_name": row["Toda name"],
            })
    return rows


@router.post("/species-db/entry")
async def add_species_entry(entry: SpeciesEntry):
    with open(SPECIES_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([entry.abbr, entry.expanded, entry.toda_name])
    return {"ok": True}
