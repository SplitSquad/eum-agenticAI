import asyncio
from app.services.agentic.agentic_cover_letter_service import job_cover_letter

async def test_cover_letter():
    # 테스트 데이터
    test_uid = "test@example.com"
    test_token = "test_token"
    
    # 첫 번째 단계 테스트
    print("\n=== 첫 번째 단계 테스트 ===")
    result1 = await job_cover_letter("", test_uid, "first", test_token)
    print(f"응답: {result1['response']}")
    print(f"상태: {result1['state']}")
    
    # 두 번째 단계 테스트
    print("\n=== 두 번째 단계 테스트 ===")
    job_info = "백엔드 개발자, Python, FastAPI, AWS"
    result2 = await job_cover_letter(job_info, test_uid, "second", test_token)
    print(f"응답: {result2['response']}")
    print(f"상태: {result2['state']}")
    
    # 세 번째 단계 테스트
    print("\n=== 세 번째 단계 테스트 ===")
    experience = "3년간의 백엔드 개발 경험, 마이크로서비스 아키텍처 설계 및 구현, AWS 클라우드 인프라 구축"
    result3 = await job_cover_letter(experience, test_uid, "third", test_token)
    print(f"응답: {result3['response']}")
    print(f"상태: {result3['state']}")
    
    # 네 번째 단계 테스트
    print("\n=== 네 번째 단계 테스트 ===")
    motivation = "클라우드 네이티브 애플리케이션 개발에 관심이 있으며, 대규모 시스템 설계 경험을 쌓고 싶습니다."
    result4 = await job_cover_letter(motivation, test_uid, "fourth", test_token)
    print(f"응답: {result4['response']}")
    print(f"상태: {result4['state']}")
    if 'download_url' in result4:
        print(f"다운로드 URL: {result4['download_url']}")

if __name__ == "__main__":
    asyncio.run(test_cover_letter()) 

