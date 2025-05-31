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
from app.services.agentic.agentic_event import EVENT
from app.services.agentic.agentic_random_dog import RandomDog
from app.services.agentic.agentic_cat_information import Cat_Infromation
from app.services.agentic.agentic_eum_image import agentic_eum_image
import json

class AgenticResponseGenerator:
    """에이전틱 응답 생성기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=False)
        self.light_llm_client = get_llm_client(is_lightweight=True)
        self.calendar_agent = AgenticCalendar()
        self.post_agent = AgenticPost()
        self.agentic_resume = AgenticResume()
        self.TEST = foodstore()
        self.cover_letter = AgenticCoverLetter()
        self.job_search = agentic_job_search()
        self.weather_search = Weather()
        self.event_search = EVENT()
        self.dog_search = RandomDog()
        self.cat_information = Cat_Infromation()
        self.eum_image = agentic_eum_image()
        # 사용자별 상태 관리
        self.user_states = {}
        logger.info(f"[에이전틱 응답] 고성능 모델 사용: {self.llm_client.model}")
    

    async def generate_response(self, original_query:str, query: str, agentic_type: AgentType, uid: str, token: str, state: str, source_lang: str, live_location: str) -> Dict[str, Any]:
        """응답을 생성합니다."""
        try:
            logger.info(f"[live_location] : {live_location}")
            if state not in ["education", "certifications", "career", "complete","growth", "motivation", "experience", "plan","complete_letter","job_search","location_category"]:
                state = "initial"

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
                result = await self.job_search.google_search(query,source_lang)                
                return result
            
            # 위치 찾기 기능 즉시 라우팅
            if state == "location_category":
                # 1. 카테고리추출
                category_code = await self.TEST.Category_extraction(query)
                # 2. 사용자정보불러오는중
                await self.TEST.load_user_data(token)

                # 3. 사용자 위치 확인
                if not live_location:
                    location = await self.TEST.location()
                else:
                    location = live_location   

                # 4. 카카오 API 호출    
                category = category_code["output"]
                logger.info(f"[category] : {category}")
                if category in {"AT4", "CE7", "FD6", "AC5", "SC4"}:
                    # ⬅︎ 사용자 의도 (족발, 스타벅스 등)를 query로 사용
                    food_store = await self.TEST.kakao_search(
                        keyword=query,
                        latitude=float(location.latitude),
                        longitude=float(location.longitude),
                        location_category=category
                    )
                elif category in {  "MT1", "CS2", "AD5", "OL7", "PK6", "SW8", "HP8", "PM9", "AG2", "PO3"}:
                    # ⬅︎ 의도는 필요 없음. 카테고리만으로 충분
                    location_category=category
                    logger.info(f"[category] : {location_category}")
                    food_store = await self.TEST.kakao_api_foodstore(
                        latitude=float(location.latitude),
                        longitude=float(location.longitude),
                        location_category=category  # ✅ 이 방식으로 정확하게 매핑
                    )

                # 6. AI 매칭 (예정)
                    location_ai = await self.TEST.ai_match(food_store,check['intention'])
                    
                # 7. 응답 반환
                return {
                    "response": location_ai ,
                    "metadata": {
                        "query": query,
                        "uid": uid,
                        "location": location,
                        "results": food_store,
                        "state": "find_food_state"
                    },
                    "state": "find_food_state",
                    "url": None
                }

            # 캘린더 응답 > 수정 완료
            if agentic_type == AgentType.CALENDAR:
                logger.info(f"[CALENDAR 기능 초기화중...]")
                agentic_calendar = self._generate_calendar_response(query,uid,token)
                return await agentic_calendar
            
            # EUM 이미지
            if agentic_type == AgentType.EUM:
                logger.info(f"[EUM 기능 초기화중...]")
                selected_eum_image = await self.eum_image.select_image(query)
                if selected_eum_image == "There_is_no_image":
                    text = f"""
                    [character description] 
                    This character is wearing traditional Korean clothing. He wears a red band on his head and a hat with a cloud-shaped decoration on top. His face has a curious and serious expression. 
                    the character name's eum

                    [user's needs]
                    {query}
                    """
                    img_url = await self.cat_information.describe_img(text)
                    return {
                        "response": f"{query}" ,
                        "state": "initial",
                        "metadata": {
                            "query": query,
                            "agentic_type": "POST",
                            "error": "",
                            "cat":"random"
                        },
                        "url": img_url  # null → None (Python 문법)
                    }
                s3_url = await self.eum_image.choose_img(selected_eum_image)
                describe = await self.eum_image.describe_eum(s3_url)
                return {
                    "response": f" {describe } " ,
                    "state": "initial",
                    "metadata": {
                        "query": query,
                        "agentic_type": "POST",
                        "error": "",
                        "eum":"random"
                    },
                    "url": s3_url  
                }
            
            # 고양이 이미지 
            elif agentic_type == AgentType.CAT:
                logger.info(f"[CATSEARCH]")
                response = await self.cat_information.hidden_cat_information()
                img_url = await self.cat_information.describe_img(response['fact'])
                
                return {
                    "response": f"{response['fact']} , {img_url}" ,
                    "state": "initial",
                    "metadata": {
                        "query": query,
                        "agentic_type": "POST",
                        "error": "",
                        "cat":"random"
                    },
                    "url": img_url  # null → None (Python 문법)
                }
                
            # 강아지 이미지 
            elif agentic_type == AgentType.DOG:
                logger.info(f"[DOGSEARCH]")
                response = await self.dog_search.api_random_image()
                describe = await self.dog_search.describe_img(response['message'])
                       
                return {
                    "response": f"{describe} " ,
                    "state": "initial",
                    "metadata": {
                        "query": query,
                        "agentic_type": "POST",
                        "error": "",
                        "dog":"random"
                    },
                    "url": response['message'] # null → None (Python 문법)
                }
            
            # 행사 서치
            elif agentic_type == AgentType.EVENT:
                logger.info(f"[EVENTSEARCH]")
                response = await self.event_search.google_search(query,source_lang,token,live_location)
                logger.info(f"[EVENTSEARCH_statecheck] : {response}")
                return response
            
            # 날씨 서치
            elif agentic_type == AgentType.WEATHER:
                logger.info(f"[WEATHERSEARCH]")
                response = await self.weather_search.weather_google_search(query,token,source_lang)
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
                    제목📝 : {Post_Response['title']} 
                    카테고리✈️ : {Post_Response['category']} 
                    내용📑 : {Post_Response['content']}  
                    ✅게시판에 업로드 되었습니다. """,
                    "metadata": {
                        "query": query,
                        "agentic_type": "POST",
                        "error": "",
                        "state": "post_state"
                    },
                    "state": "post_state",
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

                # 0 즉시 라우팅이 필요한지 체크
                check = await self.TEST.query_analyze(query)
                
                logger.info(f"[check] : {check}")
                if check['tag'] == "Find" : 
                    # 1. 카테고리추출
                    category_code = await self.TEST.Category_extraction(query)
                    # 2. 사용자정보불러오는중
                    await self.TEST.load_user_data(token)

                    # 3. 사용자 위치 확인
                    if not live_location:
                        location = await self.TEST.location()
                    else:
                        location = live_location   
                    
                    logger.info(f"[location] : {location}")

                    # 4. 카카오 API 호출    
                    category = category_code["output"]
                    logger.info(f"[category] : {category}")
                    if category in {"AT4", "CE7", "FD6", "AC5", "SC4"}:
                        # ⬅︎ 사용자 의도 (족발, 스타벅스 등)를 query로 사용
                        food_store = await self.TEST.kakao_search(
                            keyword=check['intention'],
                            latitude=float(location.latitude),
                            longitude=float(location.longitude),
                            location_category=category
                        )
                    elif category in {  "MT1", "CS2", "AD5", "OL7", "PK6", "SW8", "HP8", "PM9", "AG2", "PO3"}:
                        # ⬅︎ 의도는 필요 없음. 카테고리만으로 충분
                        location_category=category
                        logger.info(f"[category] : {location_category}")
                        food_store = await self.TEST.kakao_api_foodstore(
                            latitude=float(location.latitude),
                            longitude=float(location.longitude),
                            location_category=category  # ✅ 이 방식으로 정확하게 매핑
                        )

                    # 6. AI 매칭 (예정)
                    location_ai = await self.TEST.ai_match(food_store,check['intention'])
                    
                    # 7. 응답 반환
                    return {
                        "response": location_ai ,
                        "metadata": {
                            "query": query,
                            "uid": uid,
                            "location": location,
                            "results": food_store,
                            "state": "find_food_state"
                        },
                        "state": "find_food_state",
                        "url": None
                    }


                if state == "initial" :
                # 1 원하는 카테고리 질문
                    category = await self.TEST.category_query(source_lang)
        
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

