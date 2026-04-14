import json

from fastapi import APIRouter

from config import CHEATSHEET_PATH

router = APIRouter()


@router.get("/cheatsheet")
async def get_cheatsheet():
    return json.loads(CHEATSHEET_PATH.read_text(encoding="utf-8"))


@router.put("/cheatsheet")
async def update_cheatsheet(body: dict):
    CHEATSHEET_PATH.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return {"ok": True}
