
# app/api/v1/agentic.py

from fastapi import APIRouter, HTTPException, Request, Body, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from loguru import logger
from app.services.agentic.agentic import Agentic


router = APIRouter(
    prefix="/agentic",
    tags=["Agentic"],
    responses={
        500: {"description": "Internal server error"},
        400: {"description": "Bad request"}
    }
)

class Location(BaseModel):
    latitude: str
    longitude: str

class AgenticRequest(BaseModel):
    """에이전틱 요청 모델"""
    query: str
    uid: str
    state: Optional[str] = None
    location: Optional[Location] = None  # 🔥 선택적 필드

class AgenticResponse(BaseModel):
    """에이전틱 응답 모델"""
    response: str
    metadata: Dict[str, Any]

    state: Optional[str] = None
    url: Optional[str] = None

# 에이전트 인스턴스 생성
agentic = Agentic()

@router.post(
    "",
    response_model=AgenticResponse,
    summary="에이전틱 통합 엔드포인트",
    description="모든 에이전틱 기능을 처리하는 통합 엔드포인트입니다."
)
async def agentic_handler(request: AgenticRequest, authorization: Optional[str] = Header(None)) -> AgenticResponse:
    """
    에이전틱 통합 핸들러
    
    Args:
        request: 에이전틱 요청
        authorization: 인증 토큰
        
    Returns:
        AgenticResponse: 에이전틱 응답
        
    Raises:
        HTTPException: 처리 중 오류가 발생한 경우
    """
    try:
        logger.info(f"[TOKEN] Authorization header: {authorization}")
        
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
        else:
            token = authorization

        logger.info(f"[TOKEN] Extracted token: {token}")
        logger.info(f"[request.location] {request.location}")
        
        # 에이전트 응답 생성
        result = await agentic.get_response(
            query=request.query,
            uid=request.uid,
            token=token,
            state=request.state,
            location=request.location
        )
        
        logger.info(f"[에이전트 응답] : {result}")
        
        # 응답 반환
        return AgenticResponse(
            response=result["response"],
            metadata=result["metadata"],
            state=result.get("state"),
            url=result.get("url")
        )
        
    except Exception as e:
        logger.error(f"에이전틱 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"에이전틱 처리 중 오류가 발생했습니다: {str(e)}"
        )
