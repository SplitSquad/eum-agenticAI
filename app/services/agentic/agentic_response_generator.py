from typing import Dict, Any
from loguru import logger
from app.core.llm_client import get_llm_client
from app.services.agentic.agentic_classifier import AgentType
from app.services.agentic.agentic_calendar import AgenticCalendar
from app.services.agentic.agentic_post import AgenticPost
from app.services.agentic.agentic_find_foodstore import foodstore
from app.services.agentic.agentic_resume_service import AgenticResume
import json

class AgenticResponseGenerator:
    """에이전틱 응답 생성기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=False)
        self.calendar_agent = AgenticCalendar()
        self.post_agent = AgenticPost()
        self.agentic_resume = AgenticResume()
        # 사용자별 상태 관리
        self.user_states = {}
        logger.info(f"[에이전틱 응답] 고성능 모델 사용: {self.llm_client.model}")
    
    async def generate_response(self, original_query:str, query: str, agentic_type: AgentType, uid: str, token: str, state: str, source_lang: str) -> Dict[str, Any]:
        """응답을 생성합니다."""
        try:
            # 캘린더 응답 > 수정 완료
            if agentic_type == AgentType.CALENDAR:
                logger.info(f"[CALENDAR 기능 초기화중] : CALENDAR")
                agentic_calendar = self._generate_calendar_response(original_query,uid,token)
                return await agentic_calendar
                
            # 게시판 응답
            elif agentic_type == AgentType.POST:
                logger.info("[1. 사용자 질문 받음]")  
                Post_Response = await self._generate_post_response(token, original_query, query)
                Post_Response = json.loads(Post_Response)
                return {
                    "response": f""" 제목 : {Post_Response['title']} 
                    카테고리 : {Post_Response['category']} 
                    내용 : {Post_Response['content']}  
                    게시글이 생성되었습니다. """,
                    "state": "first",
                    "metadata": {
                        "query": query,
                        "agentic_type": "POST",
                        "error": ""
                    },
                    "url": None  # null → None (Python 문법)
                }
                
            # 이력서 응답
            elif agentic_type == AgentType.RESUME:
                # 1. 질문 & 이력서 생성
                result = await self.agentic_resume.first_query(query, uid, token, state, source_lang)
                return result  # ✅ 응답값 리턴
                        
                
            # 자소서 응답 
            elif agentic_type == AgentType.RESUME:
                return await {
                "response": "이력서 기능은 개발중입니다.",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "RESUME",
                    "error": ""
                 },
                "url":agentic_resume['download_url']
            }
                
                
                
            # 구인 조언 응답
            elif agentic_type == AgentType.RESUME:
                return await {
                "response": "이력서 기능은 개발중입니다.",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "RESUME",
                    "error": ""
                 },
                "url":agentic_resume['download_url']
            }

            elif agentic_type == AgentType.LOCATION:
                # 1. foodstore 인스턴스 생성
                TEST = foodstore()
                # 2. 사용자정보불러오는중
                await TEST.load_user_data(token)
                # 3. 사용자 위치 확인
                location = await TEST.location()
                # 4. 카테고리 지정 (예: AT4 = 관광명소, FD6 = 음식점)
                location_category = "AT4"  # 추후 query 기반 분류 가능
                # 5. 카카오 API 호출
                food_store = await TEST.kakao_api_foodstore(
                    location["latitude"],
                    location["longitude"],
                    location_category
                )
                # 6. AI 매칭 (예정)
                await TEST.ai_match(food_store)
                # 7. 응답 반환
                return {
                    "response": "📍 주변 장소를 찾았습니다!",
                    "metadata": {
                        "query": query,
                        "uid": uid,
                        "location": location,
                        "results": food_store
                    },
                    "state": state,
                    "url": None
                }

            else:
                return await self._generate_general_response(query)
            
        
                
        except Exception as e:
            logger.error(f"응답 생성 중 오류 발생: {str(e)}")
            return {
                "response": "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.",
                "metadata": {
                    "query": query,
                    "agentic_type": "error",
                    "error": str(e)
                }
            }
    
    async def _generate_general_response(self, query: str) -> Dict[str, Any]:
        """일반 응답을 생성합니다."""
        try:
            response = await self.llm_client.generate(query)
            return {
                "response": response,
                "metadata": {
                    "query": query,
                    "agentic_type": AgentType.GENERAL.value
                }
            }
        except Exception as e:
            logger.error(f"일반 응답 생성 중 오류 발생: {str(e)}")
            return {
                "response": "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.",
                "metadata": {
                    "query": query,
                    "agentic_type": AgentType.GENERAL.value,
                    "error": str(e)
                }
            }
    
    async def _generate_calendar_response(self, query: str, uid: str, token: str) -> Dict[str, Any]:
        """캘린더 관리 응답을 생성합니다."""
        try:
            logger.info(f"[CALENDAR 응답] : CALENDAR")
            response = self.calendar_agent.Calendar_function(query,token)
            logger.info(f"[CALENDAR response]  { response }")
            return response
        except Exception as e:
            logger.error(f"캘린더 관리 응답 생성 중 오류 발생: {str(e)}")
            return {
                "response": "죄송합니다. 캘린더 기능 처리 중 오류가 발생했습니다.",
                "metadata": {
                    "query": query,
                    "agentic_type": AgentType.CALENDAR.value,
                    "error": str(e)
                }
            }
############################################################################# 게시판 생성 기능  

    async def _generate_post_response(self, token, original_query, query) -> Dict[str,Any]:
        """ 게시판 생성 기능 """
        
        # 1. 카테고리 반환 단계
        logger.info("[1. 카테고리 반환 단계]: 대분류, 소분류 추출 시도")
        logger.info(f"[1. 카테고리 반환 단계]: {query}")
        post_first_response = await self.post_agent.first_query(token, query)
        
        category = post_first_response['category']
        tags = post_first_response['tags']
        logger.info(f"[post_second 필요한정보] : {category} {tags}")
        
        
        # 2. 게시판 생성 단계
        post_second_response = await self.post_agent.second_query(token, original_query, category, tags)
        logger.info(f"[post_second_response] : {post_second_response}")
        
        
        return post_second_response
    

############################################################################# 게시판 생성 기능    
