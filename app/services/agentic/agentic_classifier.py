from typing import Dict, Any, Tuple
from enum import Enum
from loguru import logger
from app.core.llm_client import get_llm_client
from app.models.agentic_response import AgentType

from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
from app.core.llm_post_prompt import Prompt
load_dotenv()  # .env 파일 자동 로딩
import os
import json


# ✅ .env 파일의 절대 경로 지정
dotenv_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(dotenv_path)
# ✅ 환경변수 읽기
groq_api_key = os.getenv("GROQ_API_KEY")


class AgenticClassifier:
    """에이전트 분류기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=True)
        logger.info(f"[CLASSIFIER] 경량 모델 사용: {self.llm_client.model}")
    
    async def classify(self, query: str) -> Dict[str, Any]:
        """
        에이전트 유형을 분류합니다.
        
        Args:
            query: 입력 질의
            
        Returns:
            Dict[str, Any]: 분류 결과
        """
        logger.info(f"[CLASSIFIER] 질의 분류 시작: {query}")
        
        # 에이전트 유형 분류
        agent_type = await self._classify_agent_type(query)
        logger.info(f"[CLASSIFIER] 에이전트 유형: {agent_type.value}")
        
        # 도메인 분류(RAG 사용시 활성화)
        # rag_type = await self._classify_rag_type(query)
        # logger.info(f"[분류기] RAG 유형: {rag_type.value}")
        
        # 단순화된 응답 형식
        result = agent_type.value
        
        logger.info(f"[CLASSIFIER] 분류 완료: {result}")
        return result
    
    async def _classify_agent_type(self, query: str) -> AgentType:
        """에이전트 유형을 분류합니다."""
        # JSON 형식 예시를 별도 변수로 분리
        json_format = '''
        {
            "agent_type": "..."
        }
        '''
        
        prompt = f"""
        Determine which type of agent is needed to process the following query.
        query: {query}
        
        Return the result ONLY in this JSON format:
        {json_format}
        
        ## Notes:
        - There is a character called **EUM (or Eum)** in our service.
        - EUM is a character that appears in images, reacts with expressions (like happy, running, jumping), and is often referenced by the user in emotional or interactive contexts.
    
        ## Available agent types:
        - calendar : managing schedule, event, or etc.
        - resume : making resumé which is related to job search. (ex_ 이력서 만들어줘)
        - job_search : Looking for a job. 
        - cover_letter : Write a self-introduction. , (ex_ 자소서 만들어줘)
        - post :  making post in community board.
        - location : find a location.
        - weather : When asking about the weather
        - event : Find an event
        - dog : Find dog
        - cat : Find cat information.
        - eum : When the query is about EUM character (e.g. image, action, emotion)
        - general : Any questions not included above

        """
        
        try:
            logger.info("[CLASSIFIER] 에이전트 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip()
            
            # markdown 스타일의 JSON 응답 처리
            if "```json" in response:
                response = response.split("```json")[-1]
                response = response.split("```")[0]
            
            response = response.strip().lower()
            logger.info(f"[CLASSIFIER] 에이전트 유형 분류 결과: {response}")
            
            # JSON 파싱 시도
            try:
                response_json = json.loads(response)
                agent_type = response_json.get("agent_type", "general").strip()
                
                # 유효한 에이전트 타입인지 확인
                for agentic_type in AgentType:
                    if agentic_type.value == agent_type:
                        return agentic_type
                        
                return AgentType.GENERAL
                
            except json.JSONDecodeError as e:
                logger.error(f"[CLASSIFIER] JSON 파싱 실패: {str(e)}, 텍스트 기반으로 분류 시도")
                # JSON 파싱 실패시 텍스트 기반으로 분류
                for agentic_type in AgentType:
                    if agentic_type.value in response:
                        return agentic_type
                return AgentType.GENERAL
                
        except Exception as e:
            logger.error(f"에이전트 유형 분류 중 오류 발생: {str(e)}")
            return AgentType.GENERAL
