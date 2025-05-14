# app/api/v1/agentic.py

from fastapi import APIRouter, HTTPException, Request, Body, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from loguru import logger
from app.services.agentic.agentic import Agentic

from app.services.agentic.agentic_resume_service import (
    ResumeConversationState,
    start_resume_conversation,
    process_resume_response
)
from app.services.agentic.agentic_job_search import (
    JobSearchState,
    process_job_search_response,
    start_job_search
)
from app.services.agentic.agentic_cover_letter_service import (
    start_cover_letter_conversation,
    process_cover_letter_response,
    CoverLetterConversationState
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
    state: Optional[str] = None

class AgenticResponse(BaseModel):
    """에이전틱 응답 모델"""
    response: str
    metadata: Dict[str, Any]
    state: Optional[str] = None
    url: Optional[str] = None

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
    cover_letter: Optional[str] = None  # ← 선택적으로 포함

class JobSearchResponse(BaseModel):
    """구직 정보 검색 응답 모델"""
    status: str
    message: Optional[str] = None
    results: Optional[List[Dict[str, str]]] = None

class JobSearchRequest(BaseModel):
    """구직 정보 검색 요청 모델"""
    response: str

class CoverLetterStartRequest(BaseModel):
    """자기소개서 생성 시작 요청 모델"""
    user_id: str

class CoverLetterResponseRequest(BaseModel):
    """자기소개서 응답 요청 모델"""
    response: str
    state: CoverLetterConversationState

class CoverLetterResponse(BaseModel):
    """자기소개서 생성 응답 모델"""
    message: str
    state: CoverLetterConversationState
    cover_letter: Optional[str] = None
    pdf_path: Optional[str] = None

# 에이전트 인스턴스 생성
agentic = Agentic()

# # 대화 상태 저장소 (실제 프로덕션에서는 Redis나 DB를 사용해야 함)
# conversation_states: Dict[str, ResumeConversationState] = {}

# 구직 정보 검색 상태 저장소
job_search_states: Dict[str, JobSearchState] = {}

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
        
        # 에이전트 응답 생성
        result = await agentic.get_response(
            query=request.query,
            uid=request.uid,
            token=token
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
        question=state.current_question,
        field=state.current_field
    )

@router.post(
    "/job-search/start/{user_id}",
    response_model=JobSearchResponse,
    summary="구직 정보 검색 시작",
    description="구직 정보 검색을 시작합니다."
)
async def start_job_search(user_id: str) -> JobSearchResponse:
    """구직 정보 검색 시작"""
    try:
        # 이미 진행 중인 검색이 있는지 확인
        if user_id in job_search_states:
            raise HTTPException(
                status_code=400,
                detail="이미 진행 중인 구직 정보 검색이 있습니다."
            )
        
        # 새로운 검색 상태 생성
        state = JobSearchState(is_active=True)
        job_search_states[user_id] = state
        
        return JobSearchResponse(
            status="started",
            message="구직 정보를 제공 받으시겠습니까? 어떤 분야에서 일하고 싶으십니까?"
        )
        
    except Exception as e:
        logger.error(f"구직 정보 검색 시작 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post(
    "/job-search/respond/{user_id}",
    response_model=JobSearchResponse,
    summary="구직 정보 검색 응답",
    description="구직 정보 검색에 대한 응답을 처리합니다."
)
async def respond_to_job_search(
    user_id: str,
    request: JobSearchRequest
) -> JobSearchResponse:
    """구직 정보 검색 응답 처리"""
    try:
        # 검색 상태 확인
        if user_id not in job_search_states:
            raise HTTPException(
                status_code=400,
                detail="진행 중인 구직 정보 검색이 없습니다."
            )
        
        # 응답 처리
        result = await process_job_search_response(request.response)
        
        # 검색이 완료되거나 취소된 경우 상태 제거
        if result["status"] in ["search_completed", "search_cancelled"]:
            del job_search_states[user_id]
        
        return JobSearchResponse(**result)
        
    except Exception as e:
        logger.error(f"구직 정보 검색 응답 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get(
    "/job-search/status/{user_id}",
    response_model=JobSearchResponse,
    summary="구직 정보 검색 상태",
    description="구직 정보 검색 진행 상태를 확인합니다."
)
async def get_job_search_status(user_id: str) -> JobSearchResponse:
    """구직 정보 검색 진행 상태 확인"""
    if user_id not in job_search_states:
        raise HTTPException(
            status_code=404,
            detail="진행 중인 구직 정보 검색이 없습니다."
        )
    
    state = job_search_states[user_id]
    return JobSearchResponse(
        status="in_progress" if state.is_active else "completed",
        message="구직 정보 검색이 진행 중입니다."
    )

@router.post(
    "/cover-letter/start/{user_id}",
    response_model=CoverLetterResponse,
    summary="자기소개서 생성 시작",
    description="자기소개서 생성을 시작합니다."
)
async def start_cover_letter(user_id: str) -> CoverLetterResponse:
    """자기소개서 생성 시작"""
    try:
        # 대화 상태 초기화
        state = await start_cover_letter_conversation(user_id)
        
        return CoverLetterResponse(
            message="자기소개서 생성을 시작합니다. 지원하시려는 직무에 대해 말씀해 주세요.",
            state=state
        )
    except Exception as e:
        logger.error(f"자기소개서 생성 시작 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post(
    "/cover-letter/response",
    response_model=CoverLetterResponse,
    summary="자기소개서 응답 처리",
    description="자기소개서 생성에 대한 응답을 처리합니다."
)
async def process_cover_letter(
    request: CoverLetterResponseRequest
) -> CoverLetterResponse:
    """자기소개서 응답 처리"""
    try:
        # 응답 처리
        result = await process_cover_letter_response(request.state, request.response)
        
        return CoverLetterResponse(
            message=result["message"],
            state=result["state"],
            cover_letter=result.get("cover_letter"),
            pdf_path=result.get("pdf_path")
        )
    except Exception as e:
        logger.error(f"자기소개서 응답 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
