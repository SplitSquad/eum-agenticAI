import pytest
from app.services.agentic_classifier import AgentClassifier
from app.models.agentic_response import AgentType, ActionType

@pytest.mark.asyncio
async def test_classify_general_inform():
    """일반적인 정보 제공 질문 테스트"""
    classifier = AgentClassifier()
    result = await classifier.classify("안녕하세요?")
    
    assert result["agent_type"] == AgentType.GENERAL
    assert result["action_type"] == ActionType.INFORM

@pytest.mark.asyncio
async def test_classify_task_execute():
    """작업 수행 질문 테스트"""
    classifier = AgentClassifier()
    result = await classifier.classify("파일을 생성해주세요")
    
    assert result["agent_type"] == AgentType.TASK
    assert result["action_type"] == ActionType.EXECUTE

@pytest.mark.asyncio
async def test_classify_domain_decide():
    """도메인 전문 지식이 필요한 질문 테스트"""
    classifier = AgentClassifier()
    result = await classifier.classify("이 환자의 상태에 대해 어떻게 판단하시나요?")
    
    assert result["agent_type"] == AgentType.DOMAIN
    assert result["action_type"] == ActionType.DECIDE 