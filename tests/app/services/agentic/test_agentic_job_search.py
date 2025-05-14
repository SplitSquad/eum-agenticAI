import pytest
from app.services.agentic.agentic_job_search import (
    start_job_search,
    process_job_search_response,
    search_job_listings,
    JobSearchState
)

@pytest.mark.asyncio
async def test_start_job_search():
    """구직 검색 시작 테스트"""
    user_id = "test_user"
    result = await start_job_search(user_id)
    
    assert isinstance(result, JobSearchState)
    assert result.is_active is True
    assert result.search_keyword is None
    assert result.search_results == []

@pytest.mark.asyncio
async def test_process_job_search_response_yes():
    """구직 검색 응답 처리 테스트 - 긍정 응답"""
    response = "네, 개발자로 일하고 싶어요"
    result = await process_job_search_response(response)
    
    assert result["status"] == "search_completed"
    assert "개발자" in result["message"]
    assert isinstance(result["results"], list)

@pytest.mark.asyncio
async def test_process_job_search_response_no():
    """구직 검색 응답 처리 테스트 - 부정 응답"""
    response = "아니요"
    result = await process_job_search_response(response)
    
    assert result["status"] == "search_cancelled"
    assert "종료" in result["message"]

@pytest.mark.asyncio
async def test_search_job_listings():
    """구직 정보 검색 테스트"""
    keyword = "개발자"
    results = await search_job_listings(keyword)
    
    assert isinstance(results, list)
    if results:  # 결과가 있는 경우
        for result in results:
            assert "title" in result
            assert "link" in result
            assert "snippet" in result 