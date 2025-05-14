from typing import Dict, Any, Optional
from loguru import logger
from app.core.llm_client import get_llm_client
from app.services.agentic.agentic_classifier import AgenticType
from app.services.agentic.agentic_calendar import AgenticCalendar
from app.services.agentic.agentic_post import AgenticPost
from app.services.agentic.agentic_resume_service import AgenticResume
from app.services.common.postprocessor import translate_response
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
    
    async def generate_response(
        self,
        original_query: str,
        english_query: str,
        agentic_type: AgenticType,
        uid: str,
        token: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """응답을 생성합니다."""
        try:
            if agentic_type == AgenticType.GENERAL:
                return await self._generate_general_response(english_query, original_query)
            elif agentic_type == AgenticType.CALENDAR:
                logger.info(f"[CALENDAR 기능 초기화중] : CALENDAR")
                return await self._generate_calendar_response(original_query, uid, token)
            elif agentic_type == AgenticType.RESUME:
                logger.info(f"[RESUME 기능 초기화중] : RESUME")
                return await self._generate_resume_response(original_query, uid, state, token)
            elif agentic_type == AgenticType.POST:
                logger.info("[1. 사용자 질문 받음]")
                post_response = await self._generate_post_response(
                    token=token,
                    original_query=original_query,
                    query=english_query,
                    state=state
                )
                if isinstance(post_response, str):
                    error_msg = await translate_response("게시글 생성 중 오류가 발생했습니다.", original_query)
                    return {
                        "response": error_msg,
                        "metadata": {
                            "query": english_query,
                            "agentic_type": "POST",
                            "error": post_response
                        }
                    }
                return post_response
            else:
                return await self._generate_general_response(english_query, original_query)
                
        except Exception as e:
            error_msg = await translate_response("죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.", original_query)
            return {
                "response": error_msg,
                "metadata": {
                    "query": english_query,
                    "agentic_type": "error",
                    "error": str(e)
                }
            }
    
    async def _generate_general_response(self, query: str, original_query: str) -> Dict[str, Any]:
        """일반 응답을 생성합니다."""
        try:
            response = await self.llm_client.generate(query)
            translated_response = await translate_response(response, original_query)
            return {
                "response": translated_response,
                "metadata": {
                    "query": query,
                    "agentic_type": AgenticType.GENERAL.value
                }
            }
        except Exception as e:
            error_msg = await translate_response("죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.", original_query)
            return {
                "response": error_msg,
                "metadata": {
                    "query": query,
                    "agentic_type": AgenticType.GENERAL.value,
                    "error": str(e)
                }
            }
    
    async def _generate_calendar_response(self, query: str, uid: str, token: str) -> Dict[str, Any]:
        """캘린더 관리 응답을 생성합니다."""
        try:
            logger.info(f"[CALENDAR 응답] : CALENDAR")
            response = self.calendar_agent.Calendar_function(query, token)
            logger.info(f"[CALENDAR response]  { response }")
            return response
        except Exception as e:
            error_msg = await translate_response("죄송합니다. 캘린더 기능 처리 중 오류가 발생했습니다.", query)
            return {
                "response": error_msg,
                "metadata": {
                    "query": query,
                    "agentic_type": AgenticType.CALENDAR.value,
                    "error": str(e)
                }
            }
    
    async def _generate_resume_response(self, query: str, uid: str, state: str, token: str) -> Dict[str, Any]:
        """이력서 관리 응답을 생성합니다."""
        try:
            logger.info(f"[RESUME 응답] : RESUME")
            response = await self.resume_agent.collect_user_input(query, state, uid)
            logger.info(f"[RESUME response] {response}")
            return response
        except Exception as e:
            error_msg = await translate_response("죄송합니다. 이력서 기능 처리 중 오류가 발생했습니다.", query)
            return {
                "response": error_msg,
                "metadata": {
                    "query": query,
                    "agentic_type": AgenticType.RESUME.value,
                    "error": str(e)
                }
            }
    
    async def _generate_reminder_response(self, query: str) -> Dict[str, Any]:
        """알림 관리 응답을 생성합니다."""
        # TODO: 알림 관리 기능 구현
        return await self._generate_general_response(query) 
############################################################################# 게시판 생성 기능  

    async def _generate_post_response(self, token, original_query, query, state) -> Dict[str,Any]:
        logger.info("[2. 어디 단계인지 확인] (ex_ 카테고리 반환 단계 , 게시판 생성단계)")
        """ 게시판 생성 기능 """
        # 기존 코드 주석 처리
        """
        state="first"
        if state == "first" : 
            post_first_response = await self.post_agent.first_query(token , query , state)
            
            if post_first_response['title'] is None or post_first_response['tags'] is None:
                error_msg = await translate_response("작성하려는 게시물에 대한 정보를 좀 더 자세하게 입력해주세요 ( 만드려는 게시물의 카테고리등 )", original_query)
                return {
                    "response": error_msg,
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
        """
        
        # 임시 응답 반환
        return {
            "response": "tmp post response",
            "metadata": {
                "query": original_query,
                "agentic_type": "post",
                "state": state
            }
        }
    

############################################################################# 게시판 생성 기능    
