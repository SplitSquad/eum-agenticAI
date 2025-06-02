from fastapi import FastAPI
from app.api.v1 import agentic
from app.config.logging_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from py_eureka_client import eureka_client
from os import getenv, path
from dotenv import load_dotenv
import asyncio
import sys
from contextlib import asynccontextmanager

# 환경 변수 로드
env_path = path.join(path.dirname(path.dirname(__file__)), '.env')
load_dotenv(env_path)

EUREKA_IP = getenv("EUREKA_IP", "http://localhost:8761/eureka")
EUREKA_APP_NAME = getenv("EUREKA_APP_NAME", "eum-classifier")
EUREKA_HOST = getenv("EUREKA_HOST", "localhost")
EUREKA_PORT = int(getenv("EUREKA_PORT", "8003"))

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Setup logging
logger = setup_logging()
logger.info("Application starting up...")

# Lifespan 이벤트 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[WORKFLOW] Server starting (lifespan)")
    await eureka_client.init_async(
        eureka_server=EUREKA_IP,
        app_name=EUREKA_APP_NAME,
        instance_host=EUREKA_HOST,
        instance_port=EUREKA_PORT
    )
    yield
    logger.info("[WORKFLOW] Server shutting down (lifespan)")
    await eureka_client.stop_async()

# FastAPI 앱 생성
app = FastAPI(
    title="EUM Agentic AI API",
    description="EUM Agentic AI API 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# API 라우터 등록
app.include_router(agentic.router, prefix="/api/v1")

# 로컬 실행 시
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)