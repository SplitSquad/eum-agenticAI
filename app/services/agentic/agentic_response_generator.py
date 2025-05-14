from typing import Dict, Any
from loguru import logger
from app.core.llm_client import get_llm_client
from app.services.agentic.agentic_classifier import AgenticType
from app.services.agentic.agentic_calendar import AgenticCalendar
from app.services.agentic.agentic_post import AgenticPost
from app.services.agentic.agentic_resume_service import AgenticResume
import json

class AgenticResponseGenerator:
    """에이전틱 응답 생성기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=False)
        self.calendar_agent = AgenticCalendar()
        self.post_agent = AgenticPost()
        self.resume_agent = AgenticResume()
        # 사용자별 상태 관리
        self.user_states = {}
        logger.info(f"[에이전틱 응답] 고성능 모델 사용: {self.llm_client.model}")
    
    async def generate_response(self,original_query:str, query: str, agentic_type: AgenticType, uid: str, token: str, state: str, keyword:str,intention:str) -> Dict[str, Any]:
        """응답을 생성합니다."""
        try:
            if agentic_type == AgenticType.GENERAL:
                return await self._generate_general_response(query)
            
            elif agentic_type == AgenticType.CALENDAR:
                logger.info(f"[CALENDAR 기능 초기화중...]")
                agentic_calendar = self._generate_calendar_response(original_query,uid,token,intention)
                return await agentic_calendar
            
            elif agentic_type == AgenticType.RESUME:
                logger.info(f"[RESUME 기능 초기화중...]")
                agentic_resume = await self._generate_first_resume(original_query,query,uid,token,intention,state)
                logger.info(f"[반환된 agentic_resume]: {agentic_resume} ")
                
                return agentic_resume
            
            elif agentic_type == AgenticType.POST:
                logger.info("[1. 사용자 질문 받음]")  
                Post_Response = await self._generate_post_response(token,original_query, query , state, keyword)
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
                    "agentic_type": AgenticType.GENERAL.value
                }
            }
        except Exception as e:
            logger.error(f"일반 응답 생성 중 오류 발생: {str(e)}")
            return {
                "response": "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.",
                "metadata": {
                    "query": query,
                    "agentic_type": AgenticType.GENERAL.value,
                    "error": str(e)
                }
            }
    
    async def _generate_schedule_response(self, query: str) -> Dict[str, Any]:
        """일정 관리 응답을 생성합니다."""
        # TODO: 일정 관리 기능 구현
        return await self._generate_general_response(query)
    
    async def _generate_todo_response(self, query: str) -> Dict[str, Any]:
        """할 일 관리 응답을 생성합니다."""
        # TODO: 할 일 관리 기능 구현
        return await self._generate_general_response(query)
    
    async def _generate_memo_response(self, query: str) -> Dict[str, Any]:
        """메모 관리 응답을 생성합니다."""
        # TODO: 메모 관리 기능 구현
        return await self._generate_general_response(query)
    
    async def _generate_calendar_response(self, query: str, uid: str, token: str,intention:str) -> Dict[str, Any]:
        """캘린더 관리 응답을 생성합니다."""
        try:
            logger.info(f"[CALENDAR 응답] : CALENDAR")
            response = self.calendar_agent.Calendar_function(query,token,intention)
            logger.info(f"[CALENDAR response]  { response }")
            return response
        except Exception as e:
            logger.error(f"캘린더 관리 응답 생성 중 오류 발생: {str(e)}")
            return {
                "response": "죄송합니다. 캘린더 기능 처리 중 오류가 발생했습니다.",
                "metadata": {
                    "query": query,
                    "agentic_type": AgenticType.CALENDAR.value,
                    "error": str(e)
                }
            }
    
    async def _generate_reminder_response(self, query: str) -> Dict[str, Any]:
        """알림 관리 응답을 생성합니다."""
        # TODO: 알림 관리 기능 구현
        return await self._generate_general_response(query) 
############################################################################# 게시판 생성 기능  

    async def _generate_post_response(self, token, original_query , query , state, keyword) -> Dict[str,Any]:
        logger.info("[2. 어디 단계인지 확인] (ex_ 카테고리 반환 단계 , 게시판 생성단계)")
        """ 게시판 생성 기능 """
        state="first"
        if state == "first" : 
            post_first_response = await self.post_agent.first_query(token , query , state, keyword)
            
            if post_first_response['title'] is None or post_first_response['tags'] is None:
                return {
                    "response": "작성하려는 게시물에대한정보를 좀 더 자세하게 입력해주세요 ( 만드려는 게시물의 카테고리등 )",
                    "state": "first",
                    "metadata": {
                        "query": query,
                        "agentic_type": "POST",
                        "error": ""
                    },
                    "url": "null"
                }
            
            title = post_first_response['title']
            tags = post_first_response['tags']
            state= "second"

        if state == "second" : 
            logger.info(f"[post_second 필요한정보] : {title} {tags} {state}")
            post_second_response = await self.post_agent.second_query(token , original_query , state, title, tags)
            logger.info(f"[post_second_response] : {post_second_response}")
            return post_second_response
        
        else :
            return "error" 
    

############################################################################# 게시판 생성 기능    

############################################################################# 이력서 생성 기능
    async def _generate_first_resume(self,original_query,query,uid,token,intention,state):
        logger.info(f"[RESUME 단계 확인중 ...] : {state}")
        if state != "complete" : 
            first_ask = await self.resume_agent.first_query(original_query,query,uid,token,intention,state)
    
            return  {
                "response": first_ask['ask_query'],
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "RESUME",
                    "error": ""
                    },
                "url": None,
                "state": first_ask['state']
            }

        elif state == "complete" : 
            make_pdf = await self.resume_agent.make_pdf(original_query,query,uid,token,intention,state)

            return  {
                "response": "이력서 기능은 개발중입니다.",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "RESUME",
                    "error": ""
                    },
                "url": None
            }
        
        else :
             return  {
                "response": "이력서 기능도중 에러발생",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "RESUME",
                    "error": "error"
                    },
                "url": None
            }

############################################################################# 이력서 생성 기능    
