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
            logger.info(f"[에이전틱 응답] {agentic_type.value} 기능 처리 시작")
            
            # 기본 응답 형식
            response_data = {
                "metadata": {
                    "query": original_query,
                    "english_query": english_query,
                    "agentic_type": agentic_type.value,
                    "state": state or "general"
                }
            }

            # 에이전트 타입별 라우팅
            if agentic_type == AgenticType.GENERAL:
                logger.info("[에이전틱 응답] 일반 대화 처리")
                response_data["response"] = "tmp general response"
            
            elif agentic_type == AgenticType.CALENDAR:
                logger.info("[에이전틱 응답] 캘린더 기능 처리")
                response_data["response"] = "tmp calendar response"
            
            elif agentic_type == AgenticType.RESUME:
                logger.info("[에이전틱 응답] 이력서 기능 처리")
                response_data["response"] = "tmp resume response"
            
            elif agentic_type == AgenticType.COVERLETTER:
                logger.info("[에이전틱 응답] 자소서 기능 처리")
                response_data["response"] = "tmp coverletter response"
            
            elif agentic_type == AgenticType.POST:
                logger.info("[에이전틱 응답] 게시판 기능 처리")
                response_data["response"] = "tmp post response"
                response_data["url"] = "null"
            
            else:
                logger.warning(f"[에이전틱 응답] 알 수 없는 에이전트 타입: {agentic_type.value}")
                response_data["response"] = "tmp unknown response"
            
            logger.info(f"[에이전틱 응답] 응답 생성 완료: {response_data}")
            return response_data
                
        except Exception as e:
            logger.error(f"[에이전틱 응답] 오류 발생: {str(e)}")
            error_msg = await translate_response("죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.", original_query)
            return {
                "response": error_msg,
                "metadata": {
                    "query": original_query,
                    "english_query": english_query,
                    "agentic_type": agentic_type.value,
                    "state": "error",
                    "error": str(e)
                }
            }

# 이전 코드 참고용 주석 (각 기능별 상세 구현)
'''
[일반 대화 처리]
async def _generate_general_response(self, query: str, original_query: str) -> Dict[str, Any]:
    """일반 응답을 생성합니다."""
    try:
        response = await self.llm_client.generate(query)
        translated_response = await translate_response(response, original_query)
        return {
            "response": translated_response,
            "metadata": {
                "query": original_query,
                "english_query": query,
                "agentic_type": AgenticType.GENERAL.value
            }
        }
    except Exception as e:
        error_msg = await translate_response("죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.", original_query)
        return {
            "response": error_msg,
            "metadata": {
                "query": original_query,
                "english_query": query,
                "agentic_type": AgenticType.GENERAL.value,
                "error": str(e)
            }
        }

[캘린더 처리]
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

[이력서 처리]
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

[게시판 처리]
async def _generate_post_response(self, token, original_query, english_query, state) -> Dict[str,Any]:
    """게시판 생성 기능"""
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
'''

############################################################################# 게시판 생성 기능    
