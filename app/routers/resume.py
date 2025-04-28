from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from app.services.agentic.agentic_resume_service import (
    ResumeConversationState,
    start_resume_conversation,
    process_resume_response
)

router = APIRouter(prefix="/resume", tags=["resume"])

# 대화 상태 저장소 (실제 프로덕션에서는 Redis나 DB를 사용해야 함)
conversation_states: Dict[str, ResumeConversationState] = {}

@router.post("/start/{user_id}")
async def start_resume(user_id: str) -> Dict:
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
        
        return {
            "status": "started",
            "question": state.current_question,
            "field": state.current_field
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/respond/{user_id}")
async def respond_to_resume(
    user_id: str,
    response: str
) -> Dict:
    """이력서 생성 대화 응답 처리"""
    try:
        # 대화 상태 확인
        if user_id not in conversation_states:
            raise HTTPException(
                status_code=400,
                detail="진행 중인 이력서 생성 대화가 없습니다."
            )
        
        state = conversation_states[user_id]
        result = await process_resume_response(state, response)
        
        # 대화가 완료된 경우 상태 제거
        if result["status"] == "completed":
            del conversation_states[user_id]
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/status/{user_id}")
async def get_resume_status(user_id: str) -> Dict:
    """이력서 생성 진행 상태 확인"""
    if user_id not in conversation_states:
        raise HTTPException(
            status_code=404,
            detail="진행 중인 이력서 생성 대화가 없습니다."
        )
    
    state = conversation_states[user_id]
    return {
        "status": "in_progress" if not state.is_completed else "completed",
        "current_field": state.current_field,
        "current_question": state.current_question,
        "missing_fields": state.missing_fields
    } 