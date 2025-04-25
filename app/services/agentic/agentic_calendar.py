from datetime import datetime #날짜 다룰 때 사용
# 파일 저장 및 불러오기용 (토큰 저장)
import os
import pickle
import requests
import json
import re
from enum import Enum
from typing import Dict, Any, List, Optional
from loguru import logger
from dotenv import load_dotenv
load_dotenv(".env")  # 프로젝트 루트의 .env 파일 로딩
# from langchain_groq import ChatGroq
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import ChatPromptTemplate


class CalendarState(str, Enum):
    """일정 관리 상태"""
    INITIAL = "initial"  # 초기 상태
    ADD = "add"  # 일정 추가
    DELETE = "delete"  # 일정 삭제
    EDIT = "edit"  # 일정 수정
    DATE_INPUT = "date_input"  # 날짜 입력
    TIME_INPUT = "time_input"  # 시간 입력
    TITLE_INPUT = "title_input"  # 제목 입력
    CONFIRM = "confirm"  # 확인


class AgenticCalendar:
    """일정 관리 에이전트"""
    
    def __init__(self):
        """일정 관리 에이전트 초기화"""
        logger.info("[일정 관리] 에이전트 초기화")
        
    async def process_query(self, query: str, uid: str, user_states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        일정 관리 관련 질의 처리
        
        Args:
            query: 사용자 질의
            uid: 사용자 ID
            user_states: 사용자별 상태 정보
            
        Returns:
            Dict[str, Any]: 응답 데이터
        """
        # 사용자 상태 확인
        if uid not in user_states:
            user_states[uid] = {
                "state": "general",
                "context": {},
                "calendar": {
                    "state": CalendarState.INITIAL,
                    "collected_info": {}
                }
            }
            
        calendar_state = user_states[uid]["calendar"]["state"]
        collected_info = user_states[uid]["calendar"]["collected_info"]
        
        logger.info(f"[일정 관리] 현재 상태: {calendar_state}")
        
        # 기능이 구현되지 않았음을 알리는 메시지 반환
        return {
            "response": "죄송합니다. 현재 일정 관리 기능은 개발 중입니다. 나중에 다시 시도해주세요.",
            "metadata": {
                "state": "calendar",
                "calendar_state": CalendarState.INITIAL.value,
                "query": query,
                "uid": uid
            }
        }

# 스텁 구현
def Calendar_list():
    logger.info("Calendar_list 호출됨 (스텁)")
    return []

def get_credentials():
    logger.info("get_credentials 호출됨 (스텁)")
    return None

def Input_analysis(user_input):
    logger.info(f"Input_analysis 호출됨 (스텁): {user_input}")
    if "추가" in user_input:
        return "add"
    elif "삭제" in user_input:
        return "delete"
    elif "수정" in user_input or "변경" in user_input:
        return "edit"
    else:
        return "unknown"

def MakeSchedule(user_input):
    logger.info(f"MakeSchedule 호출됨 (스텁): {user_input}")
    return {"summary": "일정 제목", "start": {"dateTime": "2025-04-25T09:00:00"}, "end": {"dateTime": "2025-04-25T10:00:00"}}

def add_event(make_event):
    logger.info(f"add_event 호출됨 (스텁): {make_event}")
    return True

def delete_event(user_input):
    logger.info(f"delete_event 호출됨 (스텁): {user_input}")
    return True

def delete_event_by_id(event_id):
    logger.info(f"delete_event_by_id 호출됨 (스텁): {event_id}")
    return True

def edit_event(user_input):
    logger.info(f"edit_event 호출됨 (스텁): {user_input}")
    return True

def update_event_by_id(event_id, updated_fields):
    logger.info(f"update_event_by_id 호출됨 (스텁): {event_id}, {updated_fields}")
    return True

# 실행 진입전
if __name__ == '__main__':

    user_input = input("🗓️ 일정을 입력하세요: ")

    classification = Input_analysis(user_input)
    print("classification",classification)
    
    if classification == "add" :
        print("일정 추가")        
        make_event = MakeSchedule(user_input) ## 이벤트 생성
        add_event( make_event ) ## 이벤트 추가
    elif classification == "edit" : 
        print("일정 수정")
        edit_event(user_input)    
    elif classification == "delete" : 
        print("일정 삭제")
        delete_event(user_input)
    else : 
        print('알 수 없는 명령입니다.')

    

