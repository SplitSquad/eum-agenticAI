# app/main.py

from fastapi import FastAPI
from app.api.v1 import agentic
from app.config.logging_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# main.py (혹은 uvicorn 실행에 사용되는 시작 파일)
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Setup logging
logger = setup_logging()
logger.info("Application starting up...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[WORKFLOW] Server started successfully")
    yield
    # Shutdown
    logger.info("[WORKFLOW] Server shutting down")

app = FastAPI(
    title="EUM Agentic AI API",
    description="EUM Agentic AI API 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# API 라우터 등록
app.include_router(agentic.router, prefix="/api/v1")
