from typing import Dict, Any
from loguru import logger
from app.core.llm_client import get_llm_client
from app.services.agentic.agentic_classifier import AgenticType
from app.services.agentic.agentic_calendar import AgenticCalendar

class AgenticResponseGenerator:
    """에이전틱 응답 생성기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=False)
        self.calendar_agent = AgenticCalendar()
        # 사용자별 상태 관리
        self.user_states = {}
        logger.info(f"[에이전틱 응답] 고성능 모델 사용: {self.llm_client.model}")
    
    async def generate_response(self, query: str, agentic_type: AgenticType, uid: str) -> Dict[str, Any]:
        """응답을 생성합니다."""
        try:
            if agentic_type == AgenticType.GENERAL:
                return await self._generate_general_response(query)
            elif agentic_type == AgenticType.SCHEDULE:
                return await self._generate_schedule_response(query)
            elif agentic_type == AgenticType.TODO:
                return await self._generate_todo_response(query)
            elif agentic_type == AgenticType.MEMO:
                return await self._generate_memo_response(query)
            elif agentic_type == AgenticType.CALENDAR:
                return await self._generate_calendar_response(query, uid)
            elif agentic_type == AgenticType.REMINDER:
                return await self._generate_reminder_response(query)
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
    
    async def _generate_calendar_response(self, query: str, uid: str) -> Dict[str, Any]:
        """캘린더 관리 응답을 생성합니다."""
        try:
            # AgenticCalendar를 통해 일정 관리 기능 처리
            return await self.calendar_agent.process_query(query, uid, self.user_states)
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