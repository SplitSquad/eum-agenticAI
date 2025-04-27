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

################################################ 구글 켈린더 엑세스
# 인증 범위 지정
SCOPES = ['https://www.googleapis.com/auth/calendar']

# 사용자 인증 + access_token 관리
def get_credentials():
    creds = None
    print("[사용자 인증 + access_token 관리] : get_credentials ")
    if os.path.exists('token.pickle'):
        with open('token.pickle','rb') as token : 
            creds = pickle.load(token)

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
    
    llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.7
    )
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
    {{"input": "모레 점심 먹자", "output": "add"}},
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
        
    description = user_input
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

    llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.7
    )
    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "location": {"type": "string"},
            "description": { "type": "string"},
            "start":{
                "dateTime": {"type": "string"},
                "timeZone": {"type": "string"}
            },
            "end":{
                "dateTime": {"type": "string"},
                "timeZone": {"type": "string"}
            },
            "reminders":{
                "useDefault": {"type": "boolean"},
                "overrides": {"type": "string"}
            }
        }
    })
    system_prompt = f"""
    0. Always remember the date : {now}
    1. This is an example of a one-shot. 
    
    "summary": "f< requested by user >",
    "location": "< Places mentioned by users >",
    "description": "< What users saidr >",
    "start": 
        "dateTime": "2025-04-18T10:00:00+09:00",
        "timeZone": "Asia/Seoul"
    ,
    "end": 
        "dateTime": "2025-04-18T11:00:00+09:00",
        "timeZone": "Asia/Seoul"
    ,
    "reminders": 
        "useDefault": false,
        "overrides": [
         "method": "popup", "minutes": 10 
        ]
    
    ...
    ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.

    """

    prompt=system_prompt
    print("[ADD_CALENDAR_system_prompt] ",prompt)

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
    print("[ADD_CALENDAR_output] :",response)

    return response

# 실제 이벤트 등록 함수
# 위에서 얻은 인증 정보로 API를 사용할 수 있는 service 객체 생성
def add_event(make_event):
    try:
        
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        event = make_event
        print("\n📤 보내는 이벤트 JSON:")
        print(json.dumps(event, indent=4, ensure_ascii=False))
        event_result = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        print(f"\n✅ 일정이 추가되었습니다: {event_result.get('htmlLink')}")
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


def delete_event(user_input):

    formatted_events=Calendar_list()

    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
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
    0. Always remember the date : {now}
    1. I would like to ask you to delete the schedule.
    2. It's a schedule: {Output_organization(formatted_events)}
    3. This is an example output

    "output": <What the user entered>
    "id": "<choose in schedule>",
    "summary": "<What the user entered>",
    "start": "<Time changed by user_input>",
    "end": "<Time changed by user_input>"

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

    response_dict = json.loads(response)
    delete_event_by_id(response_dict['id'])
   

# ✅ 주어진 event_id로 일정 삭제
def delete_event_by_id(event_id):
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"🗑️ 일정이 성공적으로 삭제되었습니다: {event_id}")
    except Exception as e:
        print(f"❌ 삭제 실패: {e}")

################################################ 일정 삭제

################################################ 일정 수정
def edit_event(user_input):

    formatted_events=Calendar_list()

    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
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
    0. Always remember the date : {now}
    1. I would like to ask you to change the schedule.
    2. It's a schedule: {Output_organization(formatted_events)}
    3. This is an example output

    "output": <What the user entered>
    "id": "<choose in schedule>",
    "summary": "<What the user entered>",
    "start": "<Time changed by user_input>",
    "end": "<Time changed by user_input>"

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
   
    response_dict = json.loads(response)

    event_id = response_dict["id"]
    updated_fields = {
        "summary": response_dict["summary"],
        "start": {
            "dateTime": response_dict["start"]
        },
        "end": {
            "dateTime": response_dict["end"]
        }
    }
    
    update_event_by_id(event_id,updated_fields)
   

# ✅ 주어진 event_id로 일정 수정
def update_event_by_id(event_id, updated_fields: dict):
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    try:
        # 기존 이벤트 정보 가져오기
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # 수정할 필드 반영
        event.update(updated_fields)

        # 이벤트 업데이트
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()

        print("✅ 일정이 성공적으로 수정되었습니다:")
        print(f"- 제목: {updated_event.get('summary')}")
        print(f"- 시작: {updated_event['start'].get('dateTime')}")
        print(f"- 종료: {updated_event['end'].get('dateTime')}")
    except Exception as e:
        print(f"❌ 수정 실패: {e}")


################################################ 일정 수정
################################################ 일정 확인
def check_event(user_input):
    formatted_events=Calendar_list()

    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
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
    0. Always remember the date : {now}
    1. I would like to ask you to check the schedule.
    2. It's a schedule: {Output_organization(formatted_events)}

    3. This is an example output
    "output": 
    <schedule>
    -------------
    <schedule> 
    -------------
    <schedule> 
    -------------
    ...
    -------------

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

    def Calendar_function(self, query: str) -> Dict[str, Any]:

        classification = Input_analysis(query)
        print("classification",classification)
        
        if classification == "add" :
            print("일정 추가")        
            make_event = MakeSchedule(query) ## 이벤트 생성
            print("[MAKED_EVENT] ",make_event)
            add_event( make_event ) ## 이벤트 추가
            return {
                "response": "일정이 추가되었습니다.",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar",
                    "error": ""
                }
            }
        elif classification == "edit" : 
            print("일정 수정")
            edit_event(query) 
            return {
                "response": "일정이 수정되었습니다.",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar",
                    "error": ""
                }
            }
        elif classification == "delete" : 
            print("일정 삭제")
            delete_event(query)
            return  {
                "response": "일정이 삭제되었습니다.",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar",
                    "error": ""
                }
            } 
        elif classification == "check" : 
            print("일정 확인")
            check_output = check_event(query)
            return  {
                "response": f"{check_output}",
                "metadata": {
                    "query": "{query}",
                    "agentic_type": "calendar",
                    "error": ""
                }
            } 
        else : 
            print('알 수 없는 명령입니다.')

    


