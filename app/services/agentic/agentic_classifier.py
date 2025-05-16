from typing import Dict, Any, Tuple
from enum import Enum
from loguru import logger
from app.core.llm_client import get_llm_client,get_langchain_llm
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
    CALENDAR = "calendar"  # 캘린더 관리
    RESUME = "resume" # 이력서 기능
    JOB_SEARCH = "job_search" # 구직 정보 검색 기능
    COVER_LETTER = "cover_letter" # 자기소개서 기능
    POST = "post" # 게시판 기능


class AgenticClassifier:
    """에이전트 분류기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=True)
        logger.info(f"[분류기] 경량 모델 사용: {self.llm_client.model}")
    
    async def classify(self, query: str) -> Dict[str, Any]:
        """
        에이전트 유형을 분류합니다.
        
        Args:
            query: 입력 질의
            
        Returns:
            Dict[str, Any]: 분류 결과
        """
        logger.info(f"[분류기] 질의 분류 시작: {query}")
        
        # 에이전트 유형 분류
        agent_type = await self._classify_agent_type(query)
        logger.info(f"[분류기] 에이전트 유형: {agent_type.value}")
        
        # 도메인 분류(RAG 사용시 활성화)
        # rag_type = await self._classify_rag_type(query)
        # logger.info(f"[분류기] RAG 유형: {rag_type.value}")
        
        
        result = {
            "agent_type": agent_type,
            # "rag_type": rag_type
        }
        
        logger.info(f"[분류기] 분류 완료: {result}")
        return result
    
    async def _classify_agent_type(self, query: str) -> AgentType:
        """에이전트 유형을 분류합니다."""
        prompt = f"""
        다음 질문을 처리하기 위해 어떤 유형의 에이전트가 필요한지 판단해주세요.
        질문: {query}
        
        다음 중 하나만 답변해주세요:
        - general
        - task
        - domain
        """
        
        try:
            logger.info(f"[분류기] 에이전트 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip().lower()
            logger.info(f"[분류기] 에이전트 유형 분류 결과: {response}")
            
            # 응답에서 키워드 추출
            if "task" in response:
                return AgentType.TASK
            elif "domain" in response:
                return AgentType.DOMAIN
            else:
                return AgentType.GENERAL
                
        except Exception as e:
            logger.error(f"에이전트 유형 분류 중 오류 발생: {str(e)}")
            return AgentType.GENERAL
    

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
            logger.info(f"[분류기] RAG 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip().lower()
            logger.info(f"[분류기] RAG 유형 분류 결과: {response}")
            
            # 응답에서 도메인 추출
            for rag_type in RAGType:
                if rag_type.value in response:
                    return rag_type
            
            # 기본값으로 일상생활 도메인 반환
            return RAGType.DAILY_LIFE
                
        except Exception as e:
            logger.error(f"RAG 유형 분류 중 오류 발생: {str(e)}")
            return RAGType.DAILY_LIFE
      