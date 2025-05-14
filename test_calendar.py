from app.services.agentic.agentic_calendar import AgenticCalendar
import asyncio
import json
from loguru import logger

async def test_calendar():
    logger.info("=== Calendar Functionality Test Start ===")
    
    calendar = AgenticCalendar()
    test_token = "Bearer test_token"  # 테스트용 토큰
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "일정 추가 테스트",
            "query": "내일 오후 2시에 팀 미팅 잡아줘",
            "intention": "general",
            "expected_type": "add"
        },
        {
            "name": "일정 삭제 테스트",
            "query": "오늘 저녁 약속 취소해줘",
            "intention": "general",
            "expected_type": "delete"
        },
        {
            "name": "일정 수정 테스트",
            "query": "3시 회의를 4시로 바꿔줘",
            "intention": "general",
            "expected_type": "edit"
        },
        {
            "name": "일정 조회 테스트",
            "query": "이번 주 일정 좀 알려줘",
            "intention": "general",
            "expected_type": "check"
        }
    ]
    
    for test_case in test_cases:
        logger.info(f"\n=== {test_case['name']} ===")
        logger.info(f"Query: {test_case['query']}")
        
        try:
            # 입력 분류 테스트
            action_type = calendar._classify_input(test_case["query"], test_case["intention"])
            logger.info(f"Classified as: {action_type}")
            assert action_type == test_case["expected_type"], f"Expected {test_case['expected_type']}, but got {action_type}"
            
            # 전체 기능 테스트
            result = await calendar.Calendar_function(
                test_case["query"],
                test_token,
                test_case["intention"]
            )
            logger.info(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 응답 형식 검증
            assert "response" in result, "Response missing 'response' field"
            assert "metadata" in result, "Response missing 'metadata' field"
            assert "state" in result, "Response missing 'state' field"
            
            logger.info("✅ Test passed")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            raise
    
    logger.info("\n=== All Tests Completed ===")

if __name__ == "__main__":
    asyncio.run(test_calendar()) 