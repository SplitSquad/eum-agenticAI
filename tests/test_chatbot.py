import pytest
from app.services.chatbot import Chatbot
from app.models.agentic_response import AgentType, ActionType

@pytest.mark.asyncio
async def test_chatbot_general_response():
    """일반적인 대화 응답 테스트"""
    chatbot = Chatbot()
    response = await chatbot.get_response("안녕하세요?")
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_chatbot_task_response():
    """작업 관련 응답 테스트"""
    chatbot = Chatbot()
    response = await chatbot.get_response("파일을 생성해주세요")
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_chatbot_domain_response():
    """도메인 전문 지식 응답 테스트"""
    chatbot = Chatbot()
    response = await chatbot.get_response("이 환자의 상태에 대해 어떻게 판단하시나요?")
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0 