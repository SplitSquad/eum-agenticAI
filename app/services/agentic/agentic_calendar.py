from googleapiclient.discovery import build # Google API 클라이언트 생성 도구
from google_auth_oauthlib.flow import InstalledAppFlow # OAuth 인증 흐름을 다루는 도구
from google.auth.transport.requests import Request # 토큰 갱신 시 필요한 요청 객체
from datetime import datetime #날짜 다룰 때 사용
# 파일 저장 및 불러오기용 (토큰 저장)
import os
import pickle
import requests
import json
import re
from dotenv import load_dotenv
load_dotenv()  # .env 파일 자동 로딩
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any
from loguru import logger
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser
from pydantic import BaseModel, Field
from app.config.app_config import settings
from app.core.llm_client import get_langchain_llm

def get_llm_client(is_lightweight=False):
    """Get the appropriate LLM client based on the lightweight flag."""
    return get_langchain_llm(is_lightweight)

# 환경변수에서 캘린더 API URL 가져오기
CALENDAR_API_URL = os.getenv("CALENDAR_API_URL","https://api.eum-friends.com/calendar")
if not CALENDAR_API_URL:
    raise ValueError("CALENDAR_API_URL 환경변수가 설정되지 않았습니다.")
###21
################################################ 캘린더 일정 리스트로 반환
# 결과 출력 (선택)
def Output_organization(formatted_events) -> str:
    outputs = []
    for formatted in formatted_events:
        outputs.append("------\n" + formatted)
    return "\n".join(outputs)

def Calendar_list():
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    # 일정 목록 가져오기
    events_result = service.events().list(
        calendarId='primary',
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        print("📭 등록된 일정이 없습니다.")
        return


    # 요약용 이벤트 리스트 (AI가 분석할 수 있도록 최소 정보만 포함)
    simplified_events = [
        {
            "id": event["id"],
            "summary": event.get("summary", "(제목 없음)"),
            "start": event['start'].get('dateTime', event['start'].get('date')),
            "end": event['end'].get('dateTime', event['end'].get('date'))
        }
        for event in events
    ]
    def format_event_pretty(event: dict) -> str:
        return (
            f'"id": "{event["id"]}",\n'
            f'"summary": "{event["summary"]}",\n'
            f'"start": "{event["start"]}",\n'
            f'"end": "{event["end"]}"'
        )
    # 예시 사용법
    events = [
        {
            "id": "########",
            "summary": "점심약속",
            "start": "2025-04-22T12:30:00+09:00",
            "end": "2025-04-22T14:00:00+09:00"
        }
    ]

    # 포맷된 문자열을 저장할 리스트
    formatted_events = [format_event_pretty(event) for event in simplified_events]

    

    return formatted_events

################################################ 캘린더 일정 리스트로 반환

################################################ 구글 켈린더 일정 확인
def schedule(token):
    try:
        logger.info("[구글 켈린더 일정 확인]")
        url = f"{CALENDAR_API_URL}"
        access_token = token

        headers = {
            "Authorization": f"{access_token}",  # ✅ Bearer 꼭 포함
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print("✅ 일정 가져오기 성공")
            response = response.json()
            return response
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print("💬 응답 내용:", response.text)
            return response.status_code

    except Exception as e:
        print("❌ 일정 조회 중 오류 발생:", e)

    return

def calendar_events(events):
    formatted = []
    for event in events:
        event_id = event.get("id", "N/A")
        summary = event.get("summary", "N/A")
        description = event.get("description", "N/A")
        start = event.get("start", {})
        end = event.get("end", {})

        block = (
            "----------------------------------------------------------------\n"
            f"id: {event_id}\n"
            f"summary: {summary}\n"
            f"description: {description}\n"
            '"start": \n'
            f'    "dateTime": "{start.get("dateTime", "N/A")}",\n'
            f'    "timeZone": "{start.get("timeZone", "N/A")}"\n'
            ",\n"
            '"end": \n'
            f'    "dateTime": "{end.get("dateTime", "N/A")}",\n'
            f'    "timeZone": "{end.get("timeZone", "N/A")}"\n'
            ""
        )

        formatted.append(block)
    
    return "\n".join(formatted)


################################################ 구글 켈린더 일정 확인

################################################ 구글 켈린더 엑세스
# 인증 범위 지정
SCOPES = ['https://www.googleapis.com/auth/calendar']

# 사용자 인증 + access_token 관리
def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle','rb') as token : 
            creds = pickle.load(token)
            print("[사용자 인증 + access_token 관리] " , creds)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES )
            creds = flow.run_local_server(port=8080)

        # 새 토큰 저장
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds  # ✅ 함수 끝에서 항상 반환
################################################ 구글 켈린더 엑세스

################################################ user input 분류
def Input_analysis(user_input):
    
    llm = get_llm_client(is_lightweight=False)  # 고성능 모델 사용

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "input": {"type": "string"},
            "output": {"type": "string"},
        }
    })
    prompt = ChatPromptTemplate.from_messages([
    ("system", """You're a scheduling assistant.

    Classify the user's sentence into one of the following three categories:
    - Add (new schedule)
    - Delete (remove schedule)
    - Edit (modify schedule)
    - Check (Check schedule)

    Return the result as JSON like:
    {{
    "input": "...",
    "output": "add"  // or "delete" or "edit"
    }}

    Examples:
    # ✅ ADD
    {{"input": "오늘 오후에 영화 보자", "output": "add"}},
    {{"input": "5월 3일에 생일 파티 일정 추가해줘", "output": "add"}},
    {{"input": "이번 주 금요일에 미용실 예약 좀 넣어줘", "output": "add"}},
    {{"input": "4월 20일에 친구랑 저녁 약속 있어", "output": "add"}},
    {{"input": "내일 오전 9시에 회의 있어", "output": "add"}},
    {{"input": "주말에 등산 일정 잡아줘", "output": "add"}},
    {{"input": "다음주 화요일에 프로젝트 발표 있어", "output": "add"}},
    {{"input": "오늘 밤에 헬스장 갈 거야", "output": "add"}},
    {{"input": "7시에 엄마랑 전화하기 일정 넣어줘", "output": "add"}},

    # ✅ DELETE
    {{"input": "오늘 저녁 약속 취소해줘", "output": "delete"}},
    {{"input": "5시 회의 일정 없애줘", "output": "delete"}},
    {{"input": "내일 생일 파티 취소됐어", "output": "delete"}},
    {{"input": "친구 만나는 일정 지워줘", "output": "delete"}},
    {{"input": "방금 넣은 일정 삭제해줘", "output": "delete"}},
    {{"input": "이번 주말 일정 취소할래", "output": "delete"}},
    {{"input": "3시에 예약한 거 없애줘", "output": "delete"}},
    {{"input": "다음주 월요일 약속 취소해줘", "output": "delete"}},
    {{"input": "쇼핑 일정 삭제해줘", "output": "delete"}},
    {{"input": "헬스장 안 가기로 했어", "output": "delete"}},

    # ✅ EDIT
    {{"input": "내일 회의 시간 바꿔줘", "output": "edit"}},
    {{"input": "오늘 약속 3시로 변경해줘", "output": "edit"}},
    {{"input": "저녁 6시 약속 7시로 옮겨줘", "output": "edit"}},
    {{"input": "생일 파티 장소 바뀌었어", "output": "edit"}},
    {{"input": "오후 회의 Zoom 링크로 수정해줘", "output": "edit"}},
    {{"input": "영화 시간 2시로 바꿔줘", "output": "edit"}},
    {{"input": "점심 시간 다시 조정해줘", "output": "edit"}},
    {{"input": "오늘 일정 제목 바꿔줘", "output": "edit"}},
    {{"input": "내일 약속 위치 바뀜", "output": "edit"}},
    {{"input": "저녁 약속 시간 변경해줘", "output": "edit"}}
     
    # ✅ CHECK
    {{"input": "이번 주 내 일정 알려줘", "output": "check"}},
    {{"input": "내일 일정 확인해줘", "output": "check"}},
    {{"input": "5월 3일에 무슨 일정 있었지?", "output": "check"}},
    {{"input": "다음주 금요일 스케줄 알려줘", "output": "check"}},
    {{"input": "내가 이번 달에 뭐 있지?", "output": "check"}},
    {{"input": "오늘 약속 뭐 있나?", "output": "check"}},
    {{"input": "이번 주말에 일정 있어?", "output": "check"}},
    {{"input": "다음주 일정 좀 볼 수 있을까?", "output": "check"}},
    {{"input": "지금 예정된 일정이 뭐야?", "output": "check"}},
    {{"input": "남은 이번 달 스케줄 보여줘", "output": "check"}}
    """),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser

    def parse_product(description: str) -> dict:
        result = chain.invoke({"input": description})

        return json.dumps(result, indent=2)
        
    description = f"user_input:{user_input}"
    response = parse_product(description)
    response = json.loads(response)  # 문자열 → 딕셔너리

    print("[Input_analysis] :  ",response["output"])

    return response["output"]

################################################ user input 분류

################################################ 일정 추가

def MakeSchedule(user_input):

    llm = get_llm_client(is_lightweight=False)  # 고성능 모델 사용

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "location": {"type": "string"},
            "description": { "type": "string"},
            "startDateTime":{ "type": "string"},
            "endDateTime":{ "type": "string"}
        }
    })
    system_prompt = f"""
    0. today's date : {datetime.now()}
    1. This is an example of a one-shot. 
    
    "summary": "f< requested by user >",
    "location": "< Places mentioned by users >",
    "description": "< What users said >",
    "startDateTime": "2025-05-02T10:00:00+09:00",
    "endDateTime": "2025-05-02T11:00:00+09:00",
    
    ...
    ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.

    """

    prompt=system_prompt
    logger.info("[ADD_CALENDAR_system_prompt] ",prompt)

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser

    def parse_product(description: str) -> dict:
        result = chain.invoke({"input": description})
        print("[USER INPUT] : ",description)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result

    description = user_input

    response = parse_product(description)
    print("[ADD_CALENDAR_output] ",response)

    return response

# 실제 이벤트 등록 함수
# 위에서 얻은 인증 정보로 API를 사용할 수 있는 service 객체 생성
def add_event(make_event , token):
    try:
        print("[TOKEN] ",token)
        url = f"{CALENDAR_API_URL}"
        access_token = token
        headers = {
            "Authorization": access_token ,            
            "Content-Type": "application/json"
        }

        print("\n📤 보내는 이벤트 JSON:")
        print(json.dumps(make_event, indent=4, ensure_ascii=False))

        response = requests.post(url, headers=headers, data=json.dumps(make_event))

        if response.status_code == 200:
            print("✅ 일정이 성공적으로 추가되었습니다.")
            print("🔗 응답:", response.json())
            return make_event
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print("💬 응답 내용:", response.text)
            return response.status_code

    except Exception as e:
        print("❌ 일정 추가 중 오류 발생:", e)
################################################ 일정 추가

################################################ 일정 삭제

delete_set = [
    {
        "list": '''[
            {"id": "########", "summary": "회의", "start": "2025-04-10T10:00:00+09:00", "end": "2025-04-10T11:00:00+09:00"},
            {"id": "########", "summary": "치과 예약", "start": "2025-04-11T15:00:00+09:00", "end": "2025-04-11T15:30:00+09:00"},
            {"id": "########", "summary": "친구와 저녁", "start": "2025-04-12T19:00:00+09:00", "end": "2025-04-12T21:00:00+09:00"}
        ]''',
        "input": "치과 일정 취소해줘",
        "output": '{"id": "########", "summary": "일정 이름", "start": "YYYY-MM-DD TT:00:00+09:00", "end": "2025-04-11T15:30:00+09:00"}'
    },
    {
        "list": '''[
            {"id": "########", "summary": "프로젝트 미팅", "start": "2025-04-14T14:00:00+09:00", "end": "2025-04-14T15:30:00+09:00"},
            {"id": "########", "summary": "헬스장", "start": "2025-04-14T18:00:00+09:00", "end": "2025-04-14T19:00:00+09:00"}
        ]''',
        "input": "오늘 헬스장 삭제해줘",
        "output": '{"id": "########", "summary": "헬스장", "start": "2025-04-14T18:00:00+09:00", "end": "2025-04-14T19:00:00+09:00"}'
    },
    {
        "list": '''[
            {"id": "########", "summary": "엄마 생신 파티", "start": "2025-04-16T17:00:00+09:00", "end": "2025-04-16T20:00:00+09:00"},
            {"id": "########", "summary": "개발자 밋업", "start": "2025-04-17T13:00:00+09:00", "end": "2025-04-17T15:00:00+09:00"}
        ]''',
        "input": "개발자 모임 일정 지워줘",
        "output": '{"id": "########", "summary": "개발자 밋업", "start": "2025-04-17T13:00:00+09:00", "end": "2025-04-17T15:00:00+09:00"}'
    },
    {
        "list": '''[
            {"id": "########", "summary": "출장 - 부산", "start": "2025-04-20T07:00:00+09:00", "end": "2025-04-20T20:00:00+09:00"},
            {"id": "########", "summary": "가족 여행", "start": "2025-04-21T08:00:00+09:00", "end": "2025-04-23T20:00:00+09:00"}
        ]''',
        "input": "부산 출장 취소해줘",
        "output": '{"id": "########", "summary": "출장 - 부산", "start": "2025-04-20T07:00:00+09:00", "end": "2025-04-20T20:00:00+09:00"}'
    },
    {
        "list": '''[
            {"id": "########", "summary": "스터디 모임", "start": "2025-04-22T10:00:00+09:00", "end": "2025-04-22T12:00:00+09:00"},
            {"id": "########", "summary": "점심약속", "start": "2025-04-22T12:30:00+09:00", "end": "2025-04-22T14:00:00+09:00"}
        ]''',
        "input": "22일 점심약속 빼줘",
        "output": '{"id": "########", "summary": "점심약속", "start": "2025-04-22T12:30:00+09:00", "end": "2025-04-22T14:00:00+09:00"}'
    }
]


def delete_event(user_input,token):

    formatted_events = schedule(token)
    schedule_list=calendar_events(formatted_events)

    llm = get_llm_client(is_lightweight=False)  # 고성능 모델 사용

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "id": {"type": "string"}
        }
    })

    
    # 프롬프트 문자열 구성
    system_prompt_template = f"""
    [ROLE]
    You are an AI that deletes one event from a user's schedule according to their request.

    [Today's Date]  
    {datetime.now()}

    [User Request]  
    The user asked to delete an existing event from their calendar.

    [Schedule List]  
    Below is the list of events retrieved from the calendar:  
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  
    {schedule_list}  
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    [INSTRUCTION]  
    1. Identify which event the user wants to delete by matching the appropriate `"id"` from the list.  
    2. Return only the `"id"` of the selected event to be deleted.

    [Output Format]  
    Return the result in the following JSON format:

    ```json
    "id": "<id of the event to delete>"
    "summary": "<title of the event>",
    "description": "<description of the event>",
    "startDateTime": "<start time in ISO 8601 format>",
    "endDateTime": "<end time in ISO 8601 format>"

    ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
    """
    
    print("[DELETE_CALENDAR_system_prompt] ",system_prompt_template)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template ),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser

    def parse_product(description: str) -> dict:
        result = chain.invoke({"input": description})
        
        return json.dumps(result, indent=2)

    description = user_input

    response = parse_product(description)
    print("[DELETE_CALENDAR_output] :",response)

    return response

def calendar_delete_api(delete_id,token):
    
    delete_id=json.loads(delete_id)
    schedule_id = delete_id.get("id")

    print("[schedule_id]",schedule_id)

    print("[URL] " + f"{CALENDAR_API_URL}/{schedule_id}")
    
    try:
        url = f"{CALENDAR_API_URL}/{schedule_id}"
        access_token = token

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        response = requests.delete(url, headers=headers, data="")

        if response.status_code == 200:
            print("✅ 일정이 성공적으로 수정되었습니다.")
            print("🔗 응답:", response.json())
            return delete_id
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print("💬 응답 내용:", response.text)
            return response.status_code

    except Exception as e:
        print("❌ 일정 추가 중 오류 발생:", e)    

    return 

################################################ 일정 삭제

################################################ 일정 수정
def edit_event(user_input,token):

    logger.info("[user_input]",user_input)

    formatted_events = schedule(token)
    schedule_list=calendar_events(formatted_events)
    
    llm = get_llm_client(is_lightweight=False)  # 고성능 모델 사용

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "summary": {"type": "string"},
            "start": {"type": "string"},
            "end" : {"type": "string"}
        }
    })

    # 프롬프트 문자열 구성
    system_prompt_template = f"""
    [Role]
    You are an AI that modifies one event from a schedule list according to user input.

    [Today's Date]  
    {datetime.now()}

    [User Request]  
    The user has asked to change an existing event in their schedule.

    [Schedule List]  
    Below is the list of events retrieved from the calendar:  
    ##############################################################################################################
    {schedule_list}
    ##############################################################################################################

    [INSTRUCTION]  
    1. Based on the user input, select the appropriate schedule item by its `"id"`.  
    2. Modify its fields as requested by the user:  
    - Change `summary`, `location`, `description`, `startDateTime`, or `endDateTime` if specified.
    - Keep `description` non-empty — never leave it blank.

    3. Return only the updated item in the following JSON format:

    ```json
    "id": "<id from the selected schedule>",
    "summary": "<summary from user input>",
    "location": "<location from user input>",
    "description": "<description from user input, must not be empty>",
    "startDateTime": "<ISO 8601 format start time>",
    "endDateTime": "<ISO 8601 format end time>"
    
    ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
    """
    
    print("[EDIT_CALENDAR_system_prompt] ",system_prompt_template)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template ),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser

    def parse_product(description: str) -> dict:
        result = chain.invoke({"input": description})

        return json.dumps(result, indent=2, ensure_ascii=False)

    description = user_input

    response = parse_product(description)

    print("[EDIT_CALENDAR_output] :",response)
   
    return response


def calendar_edit_api(response,token):
    response_dict = json.loads(response)
    event_id = response_dict["id"]
    print(f"[event_id] : {event_id}")

    response_dict = json.loads(response)

    # 'id' 키 제거
    response_dict.pop("id", None)
    # 출력
    response=json.dumps(response_dict, indent=2, ensure_ascii=False)
    print(f"[event] : {response}")

    print("[TYPE]",type(response))
    

    try:
        url = f"{CALENDAR_API_URL}/{event_id}"
        access_token = token

        headers = {
            "Authorization": access_token,         
            "Content-Type": "application/json"
        }

        print("\n📤 보내는 이벤트 JSON:")
        response = requests.patch(url, headers=headers, data=response)

        if response.status_code == 200:
            print("✅ 일정이 성공적으로 수정되었습니다.")
            print("🔗 응답:", response.json())
            return response_dict
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print("💬 응답 내용:", response.text)
            return response.status_code

    except Exception as e:
        print("❌ 일정 추가 중 오류 발생:", e)    

    return 
################################################ 일정 수정

################################################ 일정 확인
def check_event(user_input,token):

    formatted_events = schedule(token)
    if formatted_events == 500 : 
        return formatted_events

    schedule_list=calendar_events(formatted_events)
    
    llm = get_llm_client(is_lightweight=False)  # 고성능 모델 사용

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "input": {"type": "string"},
            "output": {"type": "string"},
        }
    })

    
    # 프롬프트 문자열 구성
    system_prompt_template = f"""
    You are an AI that summarizes and reformats schedule data retrieved from Google Calendar.

    [Today's Date]  
    {datetime.now()}

    [Schedule List]  
    Below is the raw schedule data from Google Calendar:  
    {schedule_list}

    [Your Task]  
    Extract the relevant schedule items and reformat them into a valid JSON array.

    Each item should have the following structure:

    ```json
    
    "summary": "Event title",
    "description": "Event description (if available)",
    "start": 
        "dateTime": "Start time in ISO format",
        "timeZone": "Time zone"
    ,
    "end": 
        "dateTime": "End time in ISO format",
        "timeZone": "Time zone"
    
    

    ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
    """
    
    print("[CHECK_CALENDAR_system_prompt] ",system_prompt_template)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template ),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser

    def parse_product(description: str) -> dict:
        result = chain.invoke({"input": description})
        
        return json.dumps(result, indent=2, ensure_ascii=False)

    description = user_input

    response = parse_product(description)
    print("[CHECK_CALENDAR_output] :",response)


    return response
################################################ 일정 확인
# 실행 진입전
class AgenticCalendar:
    def __init__(self):
        pass  # 필요한 초기화가 있다면 여기에

    def Calendar_function(self, query: str, token: str) -> Dict[str, Any]:

        logger.info("[CATEGORY CLASSIFICATION 초기화]")
        classification = Input_analysis(query)
        logger.info("[CALENDAR_CATEGORY] ",classification)
        
        if classification == "add" :
            print("일정 추가")        
            make_event = MakeSchedule(query) ## 이벤트 생성
            logger.info(f"[MAKED_EVENT] {make_event}")
            event_result = add_event( make_event , token ) ## 이벤트 추가
            
            if event_result == 500 :
                return {
                "response": "구글계정 서비스를 이용하세요.",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar",
                    "error": "",
                    }
                }
            return {
                "response": make_event,
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar",
                    "error": "",
                    "state": "calendar_general_add"
                }
            }
        elif classification == "edit" : 
            print("일정 수정")
            make_event = edit_event(query,token) 
            event_result = calendar_edit_api(make_event, token)
            if event_result == 500 : 
                return {
                    "response": "구글계정 서비스를 이용하세요.",
                    "metadata": {
                        "query": "{query}",
                        "agentic_type": "calendar_general_edit",
                        "error": ""
                    }
                }
            return {
                "response": event_result,
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar",
                    "error": "",
                    "state": "calendar_general_edit"
                }
            }
        
        elif classification == "delete" : 
            print("일정 삭제")
            make_event = delete_event(query,token)
            event_result = calendar_delete_api(make_event,token)
            if event_result == 500 : 
                return {
                    "response": "구글계정 서비스를 이용하세요.",
                    "metadata": {
                        "query": "{query}",
                        "agentic_type": "calendar",
                        "error": ""
                    }
                }
            return  {
                "response": event_result ,
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar_delete",
                    "error": "",
                    "state":"calendar_delete"
                },
                "state":"calendar_delete"
            } 
            
        elif classification == "check" : 
            print("일정 확인") 
            check_output = check_event(query,token)
            # 프론트에게 잘보이도록 파싱.
            if check_output == 500 : 
                return {
                    "response": "구글계정 서비스를 이용하세요.",
                    "metadata": {
                        "query": "{query}",
                        "agentic_type": "calendar",
                        "error": ""
                    }
                }
            
            return  {
                "response": f"{check_output}",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar",
                    "error": "",
                    "state":"calendar_check_state"
                }
            } 
        else : 
            print('알 수 없는 명령입니다.')

    


