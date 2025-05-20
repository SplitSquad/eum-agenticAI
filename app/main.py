# app/main.py

import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from py_eureka_client import eureka_client
from os import getenv

from app.api.v1 import agentic
from app.config.logging_config import setup_logging

# 윈도우 플랫폼 처리 (asyncio 루프 정책 설정)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 로깅 설정
logger = setup_logging()
logger.info("Application starting up...")

# ✅ lifespan 이벤트 핸들러 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[WORKFLOW] Server started successfully")
    await eureka_client.init_async(
        eureka_server=getenv("EUREKA_IP", "http://localhost:8761/eureka"),
        app_name=getenv("EUREKA_APP_NAME", "eum-agentic"),
        instance_host=getenv("EUREKA_HOST", "localhost"),
        instance_port=int(getenv("EUREKA_PORT", "8000"))
    )
    yield
    logger.info("[WORKFLOW] Server shutting down")
    await eureka_client.stop_async()

# FastAPI 인스턴스 생성
app = FastAPI(
    title="EUM Agentic AI API",
    description="EUM Agentic AI API 서비스",
    version="1.0.0",
    lifespan=lifespan  # ✅ lifespan 등록
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(agentic.router, prefix="/api/v1")

# uvicorn 실행 시 직접 시작
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
