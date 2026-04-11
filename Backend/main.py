import sys
import os
from contextlib import asynccontextmanager

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.routers import area, person, appointment, recharge, balance, audit
from Backend.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="驾驶陪练小龙虾 API", 
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(area.router)
app.include_router(person.router)
app.include_router(appointment.router)
app.include_router(recharge.router)
app.include_router(balance.router)
app.include_router(audit.router)

@app.get("/")
def root():
    return {"message": "欢迎使用驾驶陪练小龙虾 API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)
