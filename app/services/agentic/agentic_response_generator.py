from typing import Dict, Any
from loguru import logger
from app.core.llm_client import get_llm_client
from app.services.agentic.agentic_classifier import AgentType
from app.services.agentic.agentic_calendar import AgenticCalendar
from app.services.agentic.agentic_post import AgenticPost
from app.services.agentic.agentic_find_foodstore import foodstore
from app.services.agentic.agentic_resume_service import AgenticResume
from app.services.agentic.agentic_cover_letter_service import AgenticCoverLetter
from app.services.agentic.agentic_job_search import agentic_job_search
from app.services.agentic.agentic_weather import Weather
import json

class AgenticResponseGenerator:
    """에이전틱 응답 생성기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=False)
        self.calendar_agent = AgenticCalendar()
        self.post_agent = AgenticPost()
        self.agentic_resume = AgenticResume()
        self.TEST = foodstore()
        self.cover_letter = AgenticCoverLetter()
        self.job_search = agentic_job_search()
        self.weather_search = Weather()
        # 사용자별 상태 관리
        self.user_states = {}
        logger.info(f"[에이전틱 응답] 고성능 모델 사용: {self.llm_client.model}")
    

    async def generate_response(self, original_query:str, query: str, agentic_type: AgentType, uid: str, token: str, state: str, source_lang: str) -> Dict[str, Any]:
        """응답을 생성합니다."""
        try:

            # 이력서 기능 즉시 라우팅
            if state in ["education", "certifications", "career", "complete"]:
                result = await self.agentic_resume.first_query(query, uid, token, state, source_lang)
                return result
            
            # 자소서 기능 즉시 라우팅
            if state in ["growth", "motivation", "experience", "plan","complete_letter"]:
                result = await self.cover_letter.first_query(query, uid, token, state, source_lang)
                return result
            
            # job_search 즉시 라우팅
            if state in ["job_search"]:
                result = await self.job_search.google_search(query)                
                return result
            
            # 위치 찾기 기능 즉시 라우팅
            if state == "location_category":
                # 1. 카테고리추출
                category_code = await self.TEST.Category_extraction(query)
                # 2. 사용자정보불러오는중
                await self.TEST.load_user_data(token)
                # 3. 사용자 위치 확인
                location = await self.TEST.location()
                # 4. 카카오 API 호출    
                food_store = await self.TEST.kakao_api_foodstore(
                    location["latitude"],
                    location["longitude"],
                    category_code["output"]
                )
                # 6. AI 매칭 (예정)
                location_ai = await self.TEST.ai_match(food_store)
                # 7. 프론트에게 잘보이도록 파싱.

                # 7. 응답 반환
                return {
                    "response": location_ai ,
                    "metadata": {
                        "query": query,
                        "uid": uid,
                        "location": location,
                        "results": food_store,
                        "state": "initial"
                    },
                    "state": "initial",
                    "url": None
                }

            # 캘린더 응답 > 수정 완료
            if agentic_type == AgentType.CALENDAR:
                logger.info(f"[CALENDAR 기능 초기화중...]")
                agentic_calendar = self._generate_calendar_response(query,uid,token)
                return await agentic_calendar
            
            # 날씨 서치
            elif agentic_type == AgentType.WEATHER:
                logger.info(f"[WEATHERSEARCH]")
                response = await self.weather_search.weather_google_search(query,token)
                return response
            
            # 잡서치
            elif agentic_type == AgentType.JOB_SEARCH:
                logger.info(f"[JOBSEARCH]")
                response = await self.job_search.first_query(source_lang)
                return response
                
            # 게시판 응답 > 수정 완료 
            elif agentic_type == AgentType.POST:
                logger.info("[1. 사용자 질문 받음]")  
                Post_Response = await self._generate_post_response(token, original_query, query)
                Post_Response = json.loads(Post_Response)
                return {
                    "response": f""" 
                    {Post_Response['category']} 게시판에 게시글이 생성되었습니다.
                    
                    제목 : {Post_Response['title']} 
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
            elif agentic_type == AgentType.COVER_LETTER:
                # 1. 질문 & 이력서 생성
                result = await self.cover_letter.first_query(query, uid, token, state, source_lang)
                return result  # ✅ 응답값 리턴
                        

            elif agentic_type == AgentType.LOCATION:
                logger.info("[위치찾기 실행중...]")

                if state == "initial" :
                # 1 원하는 카테고리 질문
                    category = await self.TEST.category_query(source_lang)
                    # return {
                    #     "response": category,
                    #     "metadata": {
                    #         "query": query,
                    #         "uid": uid,
                    #         "location": "default",
                    #         "results": "default"
                    #     },
                    #     "state": "location_category",
                    #     "url": None
                    # }
                    return {
                        "response": category,
                        "metadata": {
                            "source": "default",
                            "state": "location_category",        # ✅ metadata 안에 포함
                            "query": query,
                            "uid": uid,
                            "location": "default",
                            "results": "default"
                        },
                        "url": None
                    }
                    
                # 2. 사용자정보불러오는중
                await self.TEST.load_user_data(token)
                # 3. 사용자 위치 확인
                location = await self.TEST.location()
                # 4. 카테고리 지정 (예: AT4 = 관광명소, FD6 = 음식점)
                location_category = "AT4"  # 추후 query 기반 분류 가능
                # 5. 카카오 API 호출
                food_store = await self.TEST.kakao_api_foodstore(
                    location["latitude"],
                    location["longitude"],
                    location_category
                )
                # 6. AI 매칭 (예정)
                await self.TEST.ai_match(food_store)
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
        
        
        # 2. 게시판 생성 단계
        logger.info(f"[게시판 생성 단계] : {category} {tags}")
        post_second_response = await self.post_agent.second_query(token, original_query, category, tags)
        logger.info(f"[post_second_response] : {post_second_response}")
        
        
        return post_second_response
############################################################################# 게시판 생성 기능    

