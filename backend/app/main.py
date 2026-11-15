from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db,ensure_admin
from app.auth import router as auth_router

app = FastAPI(title="轻量工单管理平台")

init_db()

ensure_admin()

app.include_router(auth_router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app.mount("/static",StaticFiles(directory=FRONTEND_DIR),name="static")

@app.get("/health")
def health_check():
    return {"status": "OK"}
