# app/main.py

from fastapi import FastAPI
from app.api.v1 import agentic
from app.config.logging_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from py_eureka_client import eureka_client
from os import getenv

# main.py (혹은 uvicorn 실행에 사용되는 시작 파일)
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Setup logging
logger = setup_logging()
logger.info("Application starting up...")

app = FastAPI(
    title="EUM Agentic AI API",
    description="EUM Agentic AI API 서비스",
    version="1.0.0"
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

@app.on_event("startup")
async def startup_event():
    logger.info("[WORKFLOW] Server started successfully")
    await eureka_client.init_async(
        eureka_server=getenv("EUREKA_IP","http://localhost:8761/eureka"),
        app_name=getenv("EUREKA_APP_NAME","eum-classifier"),
        instance_host=getenv("EUREKA_HOST","localhost"),
        instance_port=int(getenv("EUREKA_PORT","8000"))
    )


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("[WORKFLOW] Server shutting down")
    await eureka_client.stop_async()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
