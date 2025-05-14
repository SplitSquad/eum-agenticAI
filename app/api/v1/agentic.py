# app/api/v1/agentic.py

from fastapi import Header
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger
from app.services.agentic.agentic import Agentic
# from app.services.agentic.agentic_resume_service import (
#     ResumeConversationState,
#     start_resume_conversation,
# )

router = APIRouter(
    prefix="/agentic",
    tags=["Agentic"],
    responses={
        500: {"description": "Internal server error"},
        400: {"description": "Bad request"}
    }
)

class AgenticRequest(BaseModel):
    """에이전틱 요청 모델"""
    query: str
    uid: str   
    state : str

class AgenticResponse(BaseModel):
    """에이전틱 응답 모델"""
    response: str
    metadata: Dict[str, Any]
    state : Optional[str] = None  # ✅ None 허용
    url: Optional[str] = None  # ✅ None 허용

class ResumeResponse(BaseModel):
    """이력서 생성 응답 모델"""
    status: str
    message: Optional[str] = None
    question: Optional[str] = None
    field: Optional[str] = None
    pdf_path: Optional[str] = None

class ResumeRequest(BaseModel):
    """이력서 생성 요청 모델"""
    response: str

# 에이전트 인스턴스 생성 (애플리케이션 시작 시 한 번만 초기화)
agentic = Agentic()

# # 대화 상태 저장소 (실제 프로덕션에서는 Redis나 DB를 사용해야 함)
# conversation_states: Dict[str, ResumeConversationState] = {}

@router.post(
    "",
    response_model=AgenticResponse,
    summary="에이전틱 응답 생성",
    description="사용자 질의에 대한 에이전틱 응답을 생성합니다."
)
async def agentic_handler(request: AgenticRequest, authorization: Optional[str] = Header(None)) -> AgenticResponse:
    """
    에이전틱 핸들러
    
    Args:
        request: 에이전틱 요청
        
    Returns:
        AgenticResponse: 에이전틱 응답
        
    Raises:
        HTTPException: 처리 중 오류가 발생한 경우
    """
    try:
        logger.info(f"[TOKEN] Authorization header: {authorization}")  # 로그 확인용
        
        if authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
        else:
            token = authorization

        logger.info(f"[TOKEN] Extracted token: {token}")
        

        # 에이전트 응답 생성
        result = await agentic.get_response(request.query, request.uid, token, request.state)

        logger.info(f"[에이전트 응답] : {result}")

    
        # 응답 반환
        return AgenticResponse(
            response=result["response"],
            metadata=result["metadata"],
            state=result["state"],
            url=result["url"]
        )
    
    except Exception as e:
        logger.error(f"에이전틱 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"에이전틱 처리 중 오류가 발생했습니다: {str(e)}"
        )

