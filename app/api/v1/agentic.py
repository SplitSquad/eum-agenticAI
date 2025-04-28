# app/api/v1/agentic.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from loguru import logger
from app.services.agentic.agentic import Agentic
from app.services.agentic.agentic_resume_service import (
    ResumeConversationState,
    start_resume_conversation,
    process_resume_response
)

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

class AgenticResponse(BaseModel):
    """에이전틱 응답 모델"""
    response: str
    metadata: Dict[str, Any]

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

# 대화 상태 저장소 (실제 프로덕션에서는 Redis나 DB를 사용해야 함)
conversation_states: Dict[str, ResumeConversationState] = {}

@router.post(
    "",
    response_model=AgenticResponse,
    summary="에이전틱 응답 생성",
    description="사용자 질의에 대한 에이전틱 응답을 생성합니다."
)
async def agentic_handler(request: AgenticRequest) -> AgenticResponse:
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
        # 에이전트 응답 생성
        result = await agentic.get_response(request.query, request.uid)
        
        # 응답 반환
        return AgenticResponse(
            response=result["response"],
            metadata=result["metadata"]
        )
    except Exception as e:
        logger.error(f"에이전틱 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"에이전틱 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.post(
    "/resume/start/{user_id}",
    response_model=ResumeResponse,
    summary="이력서 생성 시작",
    description="이력서 생성 대화를 시작합니다."
)
async def start_resume(user_id: str) -> ResumeResponse:
    """이력서 생성 대화 시작"""
    try:
        # 이미 진행 중인 대화가 있는지 확인
        if user_id in conversation_states:
            raise HTTPException(
                status_code=400,
                detail="이미 진행 중인 이력서 생성 대화가 있습니다."
            )
        
        # 새로운 대화 상태 생성
        state = await start_resume_conversation(user_id)
        conversation_states[user_id] = state
        
        return ResumeResponse(
            status="started",
            question=state.current_question,
            field=state.current_field
        )
        
    except Exception as e:
        logger.error(f"이력서 생성 시작 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post(
    "/resume/respond/{user_id}",
    response_model=ResumeResponse,
    summary="이력서 생성 응답",
    description="이력서 생성 대화에 대한 응답을 처리합니다."
)
async def respond_to_resume(
    user_id: str,
    request: ResumeRequest
) -> ResumeResponse:
    """이력서 생성 대화 응답 처리"""
    try:
        # 대화 상태 확인
        if user_id not in conversation_states:
            raise HTTPException(
                status_code=400,
                detail="진행 중인 이력서 생성 대화가 없습니다."
            )
        
        state = conversation_states[user_id]
        result = await process_resume_response(state, request.response)
        
        # 대화가 완료된 경우 상태 제거
        if result["status"] == "completed":
            del conversation_states[user_id]
        
        return ResumeResponse(**result)
        
    except Exception as e:
        logger.error(f"이력서 생성 응답 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get(
    "/resume/status/{user_id}",
    response_model=ResumeResponse,
    summary="이력서 생성 상태",
    description="이력서 생성 진행 상태를 확인합니다."
)
async def get_resume_status(user_id: str) -> ResumeResponse:
    """이력서 생성 진행 상태 확인"""
    if user_id not in conversation_states:
        raise HTTPException(
            status_code=404,
            detail="진행 중인 이력서 생성 대화가 없습니다."
        )
    
    state = conversation_states[user_id]
    return ResumeResponse(
        status="in_progress" if not state.is_completed else "completed",
        current_field=state.current_field,
        current_question=state.current_question,
        missing_fields=state.missing_fields
    )
