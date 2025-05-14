import pytest
from unittest.mock import Mock, patch
import json
from app.services.agentic.agentic_post import AgenticPost

@pytest.fixture
def agentic_post():
    return AgenticPost()

@pytest.mark.asyncio
async def test_category_structure(agentic_post):
    """카테고리 구조가 올바르게 초기화되었는지 테스트"""
    expected_categories = {
        "여행": ["관광/체험", "식도락/맛집", "교통/이동", "숙소/지역", "대사관/응급"],
        "주거": ["부동산/계약", "생활환경/편의", "문화/생활", "주거지 관리/유지"],
        "유학": ["학사/캠퍼스", "학업지원", "행정/비자/서류", "기숙사/주거"],
        "취업": ["이력/채용", "비자/법률/노동", "잡페어/네트워킹", "알바/파트타임"]
    }
    assert agentic_post.categories == expected_categories

@pytest.mark.asyncio
@patch('app.services.agentic.agentic_post.get_langchain_llm')
@patch('requests.post')
async def test_create_post_study_visa(mock_post, mock_get_llm, agentic_post):
    """유학 비자 관련 게시글 생성 테스트"""
    # Mock LLM 응답 설정
    mock_llm = Mock()
    mock_get_llm.return_value = mock_llm
    
    expected_response = {
        "main_category": "유학",
        "sub_category": "행정/비자/서류",
        "content": "한국에서 학생 비자 연장하는 방법에 대한 상세 설명..."
    }
    mock_llm.invoke = Mock(return_value=Mock(content=json.dumps(expected_response)))
    
    # Mock API 응답 설정
    mock_post.return_value = Mock(
        status_code=200,
        text='{"success": true}'
    )
    
    # 테스트 실행
    result = await agentic_post.create_post(
        token="test_token",
        query="한국에서 학생 비자를 연장하는 방법에 대해 알고 싶습니다."
    )
    
    # 검증
    assert result.status_code == 200
    mock_llm.invoke.assert_called_once()
    mock_post.assert_called_once()
    
    # API 호출 데이터 검증
    call_args = mock_post.call_args
    assert call_args[1]['headers'] == {"Authorization": "test_token"}
    files = call_args[1]['files']
    post_data = json.loads(files['post'][1])
    assert post_data['mainCategory'] == "유학"
    assert post_data['tags'] == ["행정/비자/서류"]

@pytest.mark.asyncio
@patch('app.services.agentic.agentic_post.get_langchain_llm')
@patch('requests.post')
async def test_create_post_travel_food(mock_post, mock_get_llm, agentic_post):
    """맛집 관련 게시글 생성 테스트"""
    # Mock LLM 응답 설정
    mock_llm = Mock()
    mock_get_llm.return_value = mock_llm
    
    expected_response = {
        "main_category": "여행",
        "sub_category": "식도락/맛집",
        "content": "서울의 유명한 한식당 추천 리스트..."
    }
    mock_llm.invoke = Mock(return_value=Mock(content=json.dumps(expected_response)))
    
    # Mock API 응답 설정
    mock_post.return_value = Mock(
        status_code=200,
        text='{"success": true}'
    )
    
    # 테스트 실행
    result = await agentic_post.create_post(
        token="test_token",
        query="서울에서 꼭 가봐야 할 한식당을 추천해주세요."
    )
    
    # 검증
    assert result.status_code == 200
    mock_llm.invoke.assert_called_once()
    mock_post.assert_called_once()
    
    # API 호출 데이터 검증
    call_args = mock_post.call_args
    files = call_args[1]['files']
    post_data = json.loads(files['post'][1])
    assert post_data['mainCategory'] == "여행"
    assert post_data['tags'] == ["식도락/맛집"]

@pytest.mark.asyncio
@patch('app.services.agentic.agentic_post.get_langchain_llm')
async def test_create_post_error_handling(mock_get_llm, agentic_post):
    """에러 처리 테스트"""
    # Mock LLM이 예외를 발생시키도록 설정
    mock_llm = Mock()
    mock_get_llm.return_value = mock_llm
    mock_llm.invoke = Mock(side_effect=Exception("LLM 오류"))
    
    # 테스트 실행
    result = await agentic_post.create_post(
        token="test_token",
        query="테스트 쿼리"
    )
    
    # 검증
    assert result is None
    mock_llm.invoke.assert_called_once() 