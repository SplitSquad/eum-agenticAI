# import asyncio
# from app.services.agentic.agentic_resume_service import job_resume

# async def test():
#     # 1단계 - 학력/자격사항 입력
#     response = await job_resume(
#         "2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격",
#         "test@example.com",
#         "second",
#         "test_token"
#     )
#     print("1단계 응답:", response)
    
#     # 2단계 - 경력사항 입력
#     response = await job_resume(
#         "2016-2018 네이버 소프트웨어 엔지니어(검색 엔진 개발), 2018-2020 카카오 시니어 개발자(메시징 플랫폼 개발)",
#         "test@example.com",
#         "third",
#         "test_token"
#     )
#     print("2단계 응답:", response)

# if __name__ == "__main__":
#     asyncio.run(test()) 