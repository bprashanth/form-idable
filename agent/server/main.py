from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import checks, cheatsheet, species_db

app = FastAPI(title="Form Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Row-Count"],
)

app.include_router(checks.router, prefix="/agent")
app.include_router(cheatsheet.router, prefix="/agent")
app.include_router(species_db.router, prefix="/agent")


@app.get("/agent/health")
def health():
    return {"status": "ok"}
