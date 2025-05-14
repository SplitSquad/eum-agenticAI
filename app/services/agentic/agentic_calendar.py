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
from typing import Dict, Any, Optional
from loguru import logger
from pathlib import Path
# 기존: from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

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
        url = "http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar"
        access_token = token

        headers = {
            "Authorization": access_token,  # ✅ Bearer 꼭 포함
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
def Input_analysis(user_input,intention):
    
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7
    )

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "input": {"type": "string"},
            "output": {"type": "string"},
        }
    })
    from langchain.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
    You are a scheduling assistant.

    Your task is to classify the user's input into one of the following schedule-related actions:
    - add: Add a new schedule
    - delete: Remove an existing schedule
    - edit: Modify or update an existing schedule
    - check: Check or view a schedule

    ⚠️ Return your answer in the following **exact JSON format**:
    {
    "input": "...", 
    "output": "add"  // or "delete", "edit", "check"
    }

    Use the examples below as guidance.

    ### ADD Examples:
    {"input": "오늘 오후에 영화 보자", "output": "add"}
    {"input": "5월 3일에 생일 파티 일정 추가해줘", "output": "add"}
    {"input": "이번 주 금요일에 미용실 예약 좀 넣어줘", "output": "add"}
    {"input": "내일 오전 9시에 회의 있어", "output": "add"}

    ### DELETE Examples:
    {"input": "오늘 저녁 약속 취소해줘", "output": "delete"}
    {"input": "5시 회의 일정 없애줘", "output": "delete"}
    {"input": "방금 넣은 일정 삭제해줘", "output": "delete"}

    ### EDIT Examples:
    {"input": "오늘 약속 3시로 변경해줘", "output": "edit"}
    {"input": "오후 회의 Zoom 링크로 수정해줘", "output": "edit"}
    {"input": "내일 약속 위치 바뀜", "output": "edit"}

    ### CHECK Examples:
    {"input": "이번 주 내 일정 알려줘", "output": "check"}
    {"input": "5월 3일에 무슨 일정 있었지?", "output": "check"}
    {"input": "지금 예정된 일정이 뭐야?", "output": "check"}
    """),
        ("user", "{input}")
    ])


    chain = prompt | llm | parser

    def parse_product(description: str) -> dict:
        result = chain.invoke({"input": description})

        return json.dumps(result, indent=2)
        
    description = f"user_input:{user_input} intention:{intention}"
    response = parse_product(description)
    response = json.loads(response)  # 문자열 → 딕셔너리

    print("[Input_analysis] :  ",response["output"])

    return response["output"]

################################################ user input 분류

################################################ 일정 추가

from langchain.output_parsers import StructuredOutputParser
from pydantic import BaseModel, Field


# 현재 날짜와 시간
now = datetime.now()
def MakeSchedule(user_input):

    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7
    )

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
    0. today's date : {now}
    1. This is an example of a one-shot. 
    
    "summary": "f< requested by user >",
    "location": "< Places mentioned by users >",
    "description": "< What users saidr >",
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
        url = "http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar"
        access_token = token
        headers = {
            "Authorization": access_token ,            
            "Content-Type": "application/json"
        }
        print(f" [headers] : { headers} ")
        print("\n📤 보내는 이벤트 JSON:")
        print(json.dumps(make_event, indent=4, ensure_ascii=False))

        response = requests.post(url, headers=headers, data=json.dumps(make_event))

        if response.status_code == 200:
            print("✅ 일정이 성공적으로 추가되었습니다.")
            print("🔗 응답:", response.json())
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print("💬 응답 내용:", response.text)

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

    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7
    )


    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "id": {"type": "string"}
        }
    })

    
    # 프롬프트 문자열 구성
    system_prompt_template = f"""
    0. today's date : {now}
    1. I would like to ask you to delete the schedule.
    2. It's a schedule: 
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    {schedule_list}
    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    3. This is an example output

    "id": <choose id in schedule>

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

    print("[URL] " + f"http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar/{schedule_id}")
    
    try:
        url = f"http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar/{schedule_id}"
        access_token = token

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }

        response = requests.delete(url, headers=headers, data="")

        if response.status_code == 200:
            print("✅ 일정이 성공적으로 수정되었습니다.")
            print("🔗 응답:", response.json())
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print("💬 응답 내용:", response.text)

    except Exception as e:
        print("❌ 일정 추가 중 오류 발생:", e)    

    return 
    return

################################################ 일정 삭제

################################################ 일정 수정
def edit_event(user_input,token):

    logger.info("[user_input]",user_input)

    formatted_events = schedule(token)
    schedule_list=calendar_events(formatted_events)
    
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7
    )


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
    0. today's date : {now}
    1. I would like to ask you to change the schedule.
    2. It's a schedule: 
    ##############################################################################################################
    {schedule_list}
    ##############################################################################################################
    3. This is an example output

    "id": "<choose id in schedule>",
    "summary": "<summary in user_input>"
    "location": "<location in user_input>"
    "description": "<descript in user_input>",
    "startDateTime": "<Time changed by user_input>",
    "endDateTime": "<Time changed by user_input>"

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
        url = f"http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar/{event_id}"
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
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print("💬 응답 내용:", response.text)

    except Exception as e:
        print("❌ 일정 추가 중 오류 발생:", e)    

    return 
################################################ 일정 수정

################################################ 일정 확인
def check_event(user_input,token):

    formatted_events = schedule(token)
    schedule_list=calendar_events(formatted_events)
    
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0.7
    )


    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "input": {"type": "string"},
            "output": {"type": "string"},
        }
    })

    
    # 프롬프트 문자열 구성
    system_prompt_template = f"""
    0. today's date : {now}
    1. I would like to ask you to check the schedule.
    2. It's a schedule: {schedule_list}
    3. This is an example output 

    ----------------
    "time" : 
    "title" :
    "content" : 
    ----------------
    "time" : 
    "title" :
    "content" : 
    ----------------
    "time" : 
    "title" :
    "content" : 
    ----------------

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
    """
    구글 캘린더 기능을 처리하는 에이전트 클래스
    
    States:
        - first: 초기 상태, 기본적인 일정 관리 요청을 처리
        - general: 일반적인 대화 상태
        - error: 에러 발생 상태
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7
        )
        self.now = datetime.now()
        logger.info("[캘린더 에이전트] 초기화 완료")

    async def Calendar_function(self, query: str, token: str, intention: str) -> Dict[str, Any]:
        """
        캘린더 기능을 처리하는 메인 함수
        
        Args:
            query (str): 사용자 입력 쿼리
            token (str): 인증 토큰
            intention (str): 상태 정보 (first, general 등)
            
        Returns:
            Dict[str, Any]: 처리 결과를 포함한 응답 데이터
        """
        logger.info(f"[캘린더 기능] 처리 시작 - intention: {intention}")
        
        # 사용자 입력 분류
        action_type = self._classify_input(query, intention)
        logger.info(f"[캘린더 기능] 분류 결과: {action_type}")
        
        # 액션 타입에 따른 처리
        try:
            if action_type == "add":
                return await self._handle_add_event(query, token)
            elif action_type == "edit":
                return await self._handle_edit_event(query, token)
            elif action_type == "delete":
                return await self._handle_delete_event(query, token)
            elif action_type == "check":
                return await self._handle_check_event(query, token)
            else:
                return self._create_error_response("알 수 없는 명령입니다.", query)
        except Exception as e:
            logger.error(f"[캘린더 기능] 처리 중 오류 발생: {str(e)}")
            return self._create_error_response(str(e), query)

    def _classify_input(self, user_input: str, intention: str) -> str:
        """사용자 입력을 분류하는 함수"""
        classification_prompt = """You are a scheduling assistant.

Your task is to classify the user's input into one of the following schedule-related actions:
- add: Add a new schedule
- delete: Remove an existing schedule
- edit: Modify or update an existing schedule
- check: Check or view a schedule

⚠️ Return your answer in the following **exact JSON format**:
{{
    "input": "<original input>",
    "output": "<category>"  // one of: add, delete, edit, check
}}

Use the examples below as guidance.

### ADD Examples:
{{"input": "오늘 오후에 영화 보자", "output": "add"}}
{{"input": "5월 3일에 생일 파티 일정 추가해줘", "output": "add"}}
{{"input": "이번 주 금요일에 미용실 예약 좀 넣어줘", "output": "add"}}
{{"input": "내일 오전 9시에 회의 있어", "output": "add"}}

### DELETE Examples:
{{"input": "오늘 저녁 약속 취소해줘", "output": "delete"}}
{{"input": "5시 회의 일정 없애줘", "output": "delete"}}
{{"input": "방금 넣은 일정 삭제해줘", "output": "delete"}}

### EDIT Examples:
{{"input": "오늘 약속 3시로 변경해줘", "output": "edit"}}
{{"input": "오후 회의 Zoom 링크로 수정해줘", "output": "edit"}}
{{"input": "내일 약속 위치 바뀜", "output": "edit"}}

### CHECK Examples:
{{"input": "이번 주 내 일정 알려줘", "output": "check"}}
{{"input": "5월 3일에 무슨 일정 있었지?", "output": "check"}}
{{"input": "지금 예정된 일정이 뭐야?", "output": "check"}}

Current user input: {input}
"""
        
        prompt = ChatPromptTemplate.from_template(classification_prompt)
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        result = chain.invoke({"input": user_input})
        logger.info(f"[입력 분류] 결과: {result['output']}")
        
        return result["output"]

    async def _handle_add_event(self, query: str, token: str) -> Dict[str, Any]:
        """일정 추가 처리"""
        add_prompt = f"""
        Current date: {self.now}
        
        Create a calendar event from the user's input.
        Include these fields:
        - summary: Event title/name
        - location: Event location (if mentioned)
        - description: Event details
        - startDateTime: Start time (ISO format with timezone)
        - endDateTime: End time (ISO format with timezone)
        
        Consider:
        - Use Korea timezone (+09:00)
        - Default duration: 1 hour if not specified
        - Include year and full date information
        
        Return only the JSON object.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", add_prompt),
            ("user", query)
        ])
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        event_data = chain.invoke({"input": query})
        response = await self._add_event_api(event_data, token)
        
        return {
            "response": "일정이 추가되었습니다.",
            "metadata": {"query": query, "agentic_type": "calendar"},
            "state": "first",
            "url": "null"
        }

    async def _handle_edit_event(self, query: str, token: str) -> Dict[str, Any]:
        """일정 수정 처리"""
        # 현재 일정 조회
        current_events = await self._get_events(token)
        
        edit_prompt = f"""
        Current date: {self.now}
        
        Current schedules:
        {self._format_events(current_events)}
        
        Analyze the user's request to modify an existing event.
        Return a JSON object with:
        - id: Event ID to modify
        - summary: New title (if changed)
        - startDateTime: New start time (if changed)
        - endDateTime: New end time (if changed)
        - location: New location (if changed)
        - description: New description (if changed)
        
        Only include fields that need to be changed.
        Return only the JSON object.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", edit_prompt),
            ("user", query)
        ])
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        edit_data = chain.invoke({"input": query})
        await self._edit_event_api(edit_data, token)
        
        return {
            "response": "일정이 수정되었습니다.",
            "metadata": {"query": query, "agentic_type": "calendar"},
            "state": "first",
            "url": "null"
        }

    async def _handle_delete_event(self, query: str, token: str) -> Dict[str, Any]:
        """일정 삭제 처리"""
        # 현재 일정 조회
        current_events = await self._get_events(token)
        
        delete_prompt = f"""
        Current date: {self.now}
        
        Current schedules:
        {self._format_events(current_events)}
        
        Identify which event the user wants to delete.
        Return a JSON object with:
        - id: Event ID to delete
        
        Return only the JSON object.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", delete_prompt),
            ("user", query)
        ])
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        delete_data = chain.invoke({"input": query})
        await self._delete_event_api(delete_data["id"], token)
        
        return {
            "response": "일정이 삭제되었습니다.",
            "metadata": {"query": query, "agentic_type": "calendar"},
            "state": "first",
            "url": "null"
        }

    async def _handle_check_event(self, query: str, token: str) -> Dict[str, Any]:
        """일정 확인 처리"""
        # 현재 일정 조회
        current_events = await self._get_events(token)
        
        check_prompt = f"""
        Current date: {self.now}
        
        Current schedules:
        {self._format_events(current_events)}
        
        Analyze the user's request and provide relevant schedule information.
        Format the response as a clear list with:
        - Date and time
        - Event title
        - Location (if any)
        - Additional details (if any)
        
        Return the formatted text response.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", check_prompt),
            ("user", query)
        ])
        
        response = await self.llm.invoke(prompt.format(input=query))
        
        return {
            "response": response,
            "metadata": {"query": query, "agentic_type": "calendar"},
            "state": "first",
            "url": "null"
        }

    async def _get_events(self, token: str) -> Dict[str, Any]:
        """캘린더 일정 조회"""
        url = "http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[캘린더 API] 일정 조회 실패: {str(e)}")
            raise

    def _format_events(self, events: Dict[str, Any]) -> str:
        """일정 목록 포맷팅"""
        formatted = []
        for event in events:
            formatted.append(
                f"ID: {event.get('id')}\n"
                f"제목: {event.get('summary', 'N/A')}\n"
                f"시작: {event.get('start', {}).get('dateTime', 'N/A')}\n"
                f"종료: {event.get('end', {}).get('dateTime', 'N/A')}\n"
                f"위치: {event.get('location', 'N/A')}\n"
                f"설명: {event.get('description', 'N/A')}\n"
                "---"
            )
        return "\n".join(formatted)

    async def _edit_event_api(self, edit_data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """캘린더 API를 통한 이벤트 수정"""
        event_id = edit_data.pop("id")
        url = f"http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar/{event_id}"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.patch(url, headers=headers, json=edit_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[캘린더 API] 이벤트 수정 실패: {str(e)}")
            raise

    async def _delete_event_api(self, event_id: str, token: str) -> None:
        """캘린더 API를 통한 이벤트 삭제"""
        url = f"http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar/{event_id}"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"[캘린더 API] 이벤트 삭제 실패: {str(e)}")
            raise

    def _create_error_response(self, error_msg: str, query: str) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "response": f"죄송합니다. {error_msg}",
            "metadata": {
                "query": query,
                "agentic_type": "calendar",
                "error": error_msg
            },
            "state": "error",
            "url": "null"
        }

    async def _add_event_api(self, event_data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """캘린더 API를 통한 이벤트 추가"""
        url = "http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/calendar"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=event_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[캘린더 API] 이벤트 추가 실패: {str(e)}")
            raise

    


