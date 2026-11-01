from fastapi import FastAPI

from app.db import init_db

app = FastAPI(title="轻量工单管理平台")

init_db()


@app.get("/health")
def health_check():
    return {"status": "OK"}
