from fastapi import FastAPI
from app.db import init_db,ensure_admin
from app.router.auth import router as auth_router


app = FastAPI(title="轻量工单管理平台")

init_db()

ensure_admin()

app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {"status": "OK"}
