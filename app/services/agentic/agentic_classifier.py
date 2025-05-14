from typing import Dict, Any, Tuple
from enum import Enum
from loguru import logger
from app.core.llm_client import get_llm_client, get_langchain_llm
from app.config.app_config import settings, LLMProvider
from app.models.agentic_response import AgentType, ActionType

from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
from app.core.llm_post_prompt import Prompt
load_dotenv()  # .env 파일 자동 로딩
import os


# ✅ .env 파일의 절대 경로 지정
dotenv_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(dotenv_path)
# ✅ 환경변수 읽기
groq_api_key = os.getenv("GROQ_API_KEY")
import json

class RAGType(str, Enum):
    """RAG 도메인 유형"""
    VISA_LAW = "visa_law"  # 비자/법률
    SOCIAL_SECURITY = "social_security"  # 사회보장제도
    TAX_FINANCE = "tax_finance"  # 세금/금융
    MEDICAL_HEALTH = "medical_health"  # 의료/건강
    EMPLOYMENT = "employment"  # 취업
    DAILY_LIFE = "daily_life"  # 일상생활

class AgenticType(str, Enum):
    """에이전틱 기능 유형"""
    GENERAL = "general"  # 일반 대화
    SCHEDULE = "schedule"  # 일정 관리
    TODO = "todo"  # 할 일 관리
    MEMO = "memo"  # 메모 관리
    CALENDAR = "calendar"  # 캘린더 관리
    REMINDER = "reminder"  # 알림 관리
    RESUME = "resume" # 이력서 기능
    POST = "post" # 게시판 기능

class AgenticClassifier:
    """에이전틱 분류기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=True)
        logger.info(f"[분류기] 경량 모델 사용: {self.llm_client.model}")
    
    async def classify(self, query: str) -> Dict[str, Any]:
        """
        질의를 분류합니다.
        
        Args:
            query: 사용자 질의
            
        Returns:
            AgenticType: 에이전틱 기능 유형
        """
        try:
            logger.info(f"[에이전틱 분류] 질의 분류 시작: {query}")
            
            # 질의 유형 분류
            agentic_type = await self._classify_agentic_type(query)
            logger.info(f"[에이전틱 분류] 기능 유형: {agentic_type.value}")
            
            # 필요한 액션 분류
            action_type = await self._classify_action_type(query)
            logger.info(f"[에이전틱 분류] 액션 유형: {action_type.value}")
            
            # 도메인 분류
            rag_type = await self._classify_rag_type(query)
            logger.info(f"[에이전틱 분류] RAG 유형: {rag_type.value}")
            
            result = {
                "agent_type": agentic_type,
                "action_type": action_type,
                "rag_type": rag_type
            }
            
            logger.info(f"[에이전틱 분류] 분류 완료: {result}")
            return agentic_type  # 기존 코드와의 호환성을 위해 agentic_type만 반환
            
        except Exception as e:
            logger.error(f"[에이전틱 분류] 오류 발생: {str(e)}")
            return AgenticType.GENERAL
    
    async def _classify_agentic_type(self, query: str) -> AgenticType:
        """에이전틱 기능 유형을 분류합니다."""
        prompt = f"""
        다음 질문을 처리하기 위해 어떤 유형의 기능이 필요한지 판단해주세요.
        질문: {query}
        
        다음 중 하나만 답변해주세요:
        - general: 일반 대화나 질문
        - schedule: 일정 관리 (약속 잡기, 일정 확인 등)
        - todo: 할 일 관리 (할 일 추가, 삭제, 확인 등)
        - memo: 메모 관리 (메모 작성, 조회 등)
        - calendar: 캘린더 관리 (일정 등록, 조회 등)
        - reminder: 알림 관리 (알림 설정, 확인 등)
        - resume: 이력서 관련 (이력서 작성, 수정 등)
        - post: 게시글 관련 (게시글 작성, 조회, 모임/스터디 구하기 등)

        주의사항:
        - 모임이나 스터디를 구하는 내용은 'post'로 분류하세요
        - 게시글 작성 요청은 'post'로 분류하세요
        - 단순 일정 관리는 'schedule'로 분류하세요
        """
        
        try:
            logger.info(f"[에이전틱 분류] 기능 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip().lower()
            logger.info(f"[에이전틱 분류] 기능 유형 분류 결과: {response}")

            # 응답에서 기능 유형 추출
            for agentic_type in AgenticType:
                if agentic_type.value in response:
                    return agentic_type
            
            # 기본값으로 일반 대화 반환
            return AgenticType.GENERAL
                
        except Exception as e:
            logger.error(f"[에이전틱 분류] 기능 유형 분류 중 오류 발생: {str(e)}")
            return AgenticType.GENERAL
    
    async def _classify_action_type(self, query: str) -> ActionType:
        """필요한 액션 유형을 분류합니다."""
        prompt = f"""
        다음 질문을 처리하기 위해 어떤 유형의 액션이 필요한지 판단해주세요.
        질문: {query}
        
        다음 중 하나만 답변해주세요:
        - inform: 정보 제공이나 응답
        - execute: 실제 작업 수행 (작성, 수정, 삭제 등)
        - decide: 의사 결정이나 판단
        """
        
        try:
            logger.info(f"[에이전틱 분류] 액션 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip().lower()
            logger.info(f"[에이전틱 분류] 액션 유형 분류 결과: {response}")
            
            # 응답에서 키워드 추출
            if "execute" in response:
                return ActionType.EXECUTE
            elif "decide" in response:
                return ActionType.DECIDE
            else:
                return ActionType.INFORM
                
        except Exception as e:
            logger.error(f"액션 유형 분류 중 오류 발생: {str(e)}")
            return ActionType.INFORM
    
    async def _classify_rag_type(self, query: str) -> RAGType:
        """RAG 유형을 분류합니다."""
        prompt = f"""
        다음 질문이 어떤 도메인에 속하는지 판단해주세요.
        질문: {query}
        
        다음 중 하나만 답변해주세요:
        - visa_law: 비자/법률 관련 질문
        - social_security: 사회보장제도 관련 질문
        - tax_finance: 세금/금융 관련 질문
        - medical_health: 의료/건강 관련 질문
        - employment: 취업 관련 질문
        - daily_life: 일상생활 관련 질문
        """
        
        try:
            logger.info(f"[에이전틱 분류] RAG 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip().lower()
            logger.info(f"[에이전틱 분류] RAG 유형 분류 결과: {response}")
            
            # 응답에서 도메인 추출
            for rag_type in RAGType:
                if rag_type.value in response:
                    return rag_type
            
            # 기본값으로 일상생활 도메인 반환
            return RAGType.DAILY_LIFE
                
        except Exception as e:
            logger.error(f"RAG 유형 분류 중 오류 발생: {str(e)}")
            return RAGType.DAILY_LIFE