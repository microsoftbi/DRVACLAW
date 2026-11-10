import sys
import os
from contextlib import asynccontextmanager

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.routers import area, student, coach, vehicle, appointment, recharge, balance, audit
from Backend.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 建表与索引幂等执行，保证已有数据库也能补上索引
    init_db()
    yield


app = FastAPI(
    title="驾驶智陪工作台 API",
    version="1.0.0",
    lifespan=lifespan
)

# 仅放行本地/内网开发源，避免 "*" 与 allow_credentials=True 的非法组合
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(area.router)
app.include_router(student.router)
app.include_router(coach.router)
app.include_router(vehicle.router)
app.include_router(appointment.router)
app.include_router(recharge.router)
app.include_router(balance.router)
app.include_router(audit.router)

@app.get("/")
def root():
    return {"message": "欢迎使用驾驶智陪工作台 API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
