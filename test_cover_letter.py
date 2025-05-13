import asyncio
from app.services.agentic.agentic_cover_letter_service import (
    start_cover_letter_conversation,
    process_cover_letter_response,
    CoverLetterConversationState
)

async def test():
    # 1. 자기소개서 작성 시작
    state = await start_cover_letter_conversation("test@example.com")
    print("1단계 - 자기소개서 작성 시작:", state)
    
    # 2. 직무 정보 입력
    job_info = "백엔드 개발자 (Python, Django, AWS). 서버 개발 및 클라우드 인프라 관리 업무"
    result = await process_cover_letter_response(state, job_info)
    print("2단계 - 경험 정보 요청:", result)
    
    # 3. 경험 정보 입력
    experience = """
    - 대규모 트래픽 처리를 위한 서버 아키텍처 설계 및 구현
    - AWS ECS, Lambda를 활용한 마이크로서비스 아키텍처 구축
    - 실시간 데이터 처리 시스템 개발 (처리량 300% 향상)
    """
    result = await process_cover_letter_response(result["state"], experience)
    print("3단계 - 지원 동기 요청:", result)
    
    # 4. 지원 동기 입력
    motivation = """
    어린 시절부터 기술을 통해 사회 문제를 해결하는 것에 관심이 많았습니다.
    특히 클라우드 기술을 활용한 확장 가능한 시스템 구축에 열정이 있어,
    이 분야에서 전문가로 성장하고 싶습니다.
    """
    result = await process_cover_letter_response(result["state"], motivation)
    print("4단계 - 자기소개서 생성 완료:", result)

if __name__ == "__main__":
    asyncio.run(test()) 