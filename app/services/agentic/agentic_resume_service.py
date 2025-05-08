import os
import tempfile
from typing import Dict, List, Optional, TypedDict, Any
import asyncio
from datetime import datetime
import httpx
from fastapi import HTTPException
from playwright.async_api import async_playwright
from app.core.llm_client import get_llm_client
from loguru import logger
from dotenv import load_dotenv
load_dotenv()  # .env 파일 자동 로딩
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

class ResumeConversationState:
    """이력서 생성 대화 상태 관리 클래스"""
    def __init__(self, user_id: str):
        self.user_id = user_id         # ✅ 저장
        self.user_data: Dict[str, List[Dict[str, str]]] = {}
        self.missing_fields: List[str] = []
        self.current_field: Optional[str] = None
        self.current_question: Optional[str] = None
        self.is_completed: bool = False
        self.pdf_path: Optional[str] = None

    async def initialize(self, authotization, user_email, request):
        """외부 API로부터 사용자 프로필을 받아 초기화"""
        logger.info("[API로부터 사용자 프로필을 받아 초기화]")
        profile = await get_user_profile(self.user_id)
        self.user_data = {
            key: [{"value": value}] for key, value in profile.items()
        }
        # 예: 기본적으로 name, email, phone만 남겨둠
        self.missing_fields = [
            field for field in ["name", "email", "phone", "birth_date", "address"]
            if field not in profile or not profile[field]
        ]

    async def missing_info(self, authotization, user_email, request):
        """외부 API로부터 사용자 추가 프로필을 받아 초기화"""
        profile = await ask_for_missing_info(self)

        # 기존 user_data에 병합
        for key, value in profile.items():
            if key not in self.user_data:
                self.user_data[key] = []
            self.user_data[key].append({"value": value})

        # 예: 기본적으로 name, email, phone만 남겨둠
        self.missing_fields = [
            field for field in ["name", "email", "phone", "birth_date", "address"]
            if field not in profile or not profile[field]
        ]

########################################################## 실제 백엔드 API를 통해 사용자 프로필 정보를 가져옵니다.
async def get_user_profile(user_id: str) -> Dict[str, str]:
    """실제 백엔드 API를 통해 사용자 프로필 정보를 가져옵니다."""
    try:
        # 테스트용 데이터 사용
        user_data = {
            'userId': 'test123',
            'email': 'test@test.com',
            'name': '홍길동', 
            'birth_date': '1990-01-01',
            'phone': '010-1234-5678',
            'address': '서울시 강남구'
        }
        return user_data
            
    except Exception as e:
        logger.error(f"🚨 사용자 프로필 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사용자 프로필 조회 중 오류 발생: {str(e)}"
        )
########################################################## """실제 백엔드 API를 통해 사용자 프로필 정보를 가져옵니다."""

########################################################## 이력서 추가정보
async def ask_for_missing_info(field: str) -> str:
    logger.info("[사용자의 자기소개 초기화중 ...]")
    
    try:
        # 테스트용 데이터 사용
        user_data = {
            'languages ': 'kor',
            'nation': 'jap',
            'gender': "MALE",
            'visitPurpose': 'Travel',
            'period': '1_month',

        }
        return user_data
            
    except Exception as e:
        logger.error(f"🚨 사용자 프로필 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사용자 프로필 조회 중 오류 발생: {str(e)}"
        )
    
    return
########################################################## 이력서 추가정보

########################################################## """이력서 생성 대화 시작"""
async def start_resume_conversation(authotization, user_email, request) -> ResumeConversationState:
    
    state = ResumeConversationState(user_email)

    # 1. 사용자 프로필 정보 가져오기
    logger.info("[ 사용자 프로필 정보 백으로 api 요청중...] ")
    await state.initialize(authotization, user_email, request)
    logger.info(f"[ 📊 사용자 프로필 정보 ] {state.user_data} ")
    
    # 2. 필요한 정보 요청
    logger.info("[ 필요한 프로필 정보 백으로 api 요청중...] ")
    await state.missing_info(authotization, user_email, request)
    logger.info(f"[ 📊 추가된 프로필 정보 ] {state.user_data} ")
    
    return state
########################################################## """이력서 생성 대화 시작"""

########################################################## job_resume조건문
async def job_resume(query, uid, state, token):
    authotization = token
    user_email = uid
    pre_state = state
    logger.info(f"[job_resume parameter] : {authotization} , {user_email} , {pre_state}")

    ## 첫번째 응답.
    if pre_state == "first" :
        print("[first_response]")
        first_response = await start_resume(state)
        return first_response
    ## 두번째 응답.
    elif pre_state == "second" : 
        print("[second_response]")
        request=query
        second_response = await respond_to_resume(authotization, user_email, request)
        logger.info(f"[두번째 응답] : {second_response}")
        print(f"[두번째 응답] : {second_response}")
        return second_response
    else :
        print("잘못된 상태입니다.") 

    return " "
########################################################## job_resume조건문

########################################################## 이력서 생성 환경설정
from pydantic import BaseModel    
class ResumeResponse(BaseModel):
    """이력서 생성 응답 모델"""
    status: str
    message: Optional[str] = None
    question: Optional[str] = None
    field: Optional[str] = None
    pdf_path: Optional[str] = None

class ResumeRequest(BaseModel):
    """이력서 생성 요청 모델"""
    response: str

# 대화 상태 저장소 (실제 프로덕션에서는 Redis나 DB를 사용해야 함)
conversation_states: Dict[str, ResumeConversationState] = {}
########################################################## 이력서 생성 환경설정

########################################################## 이력서 작성 시작 API
async def start_resume(state: str) -> Dict[str, str]:
    """이력서 생성 대화 시작"""
    logger.info("[사용자에게 이력서 요청을 보냄...] ")

    response = "본인을 어필해주세요 (사용 가능한 기술 , 수상경력 , 성격 등 )"
    new_state = "second"

    return {
        "response": response,
        "state": new_state
    }

    
########################################################## 이력서 작성 시작 API

########################################################## 이력서 작성 중 응답 API
import json
async def make_pdf(state: str,request: str):

    llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.7
    )
    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        }
    })

    system_prompt="""
    0. will provide user information in user_input
    1. making a pdf.
    2. Please return it as html(⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.)
    3. This is an example.

    "html" : " "

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 0;
        }}
        body {{
            font-family: 'Batang', serif;
            margin: 0;
            padding: 0;
            line-height: 1.5;
        }}
        .page {{
            width: 210mm;
            height: 297mm;
            padding: 15mm 20mm;
            box-sizing: border-box;
        }}
        h1 {{
            text-align: center;
            font-size: 24px;
            margin-bottom: 10px;
            letter-spacing: 15px;
            font-weight: normal;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 11px;
        }}
        th, td {{
            border: 1.2px solid black;
            padding: 8px 4px;
            text-align: center;
            vertical-align: middle;
            height: 25px;
            box-sizing: border-box;
        }}
        .photo-cell {{
            width: 30mm;
            height: 40mm;
            text-align: center;
            vertical-align: middle;
            font-size: 10px;
            color: #666;
        }}
        .header-table td {{
            height: 32px;
        }}
        .family-table td {{
            height: 28px;
        }}
        .period-cell {{
            width: 20%;
        }}
        .content-cell {{
            width: 60%;
        }}
        .note-cell {{
            width: 20%;
        }}
        .footer {{
            margin-top: 60px;
            text-align: center;
            font-size: 12px;
        }}
        .date-line {{
            margin: 30px 0;
            line-height: 2;
        }}
    </style>
</head>
<body>
    <div class="page">
        <table class="header-table">
            <tr>
                <td rowspan="3" class="photo-cell">(사 진)</td>
                <td colspan="6"><h1>이 력 서</h1></td>
            </tr>
            <tr>
                <td>성 명</td>
                <td colspan="2">이름</td>
                <td colspan="2">생년월일</td>
                <td colspan="2">YYYY-MM-DD</td>
            </tr>
            <tr>
                <td>전화번호</td>
                <td colspan="2">010-XXXX-XXXX</td>
                <td colspan="2">국적</td>
                <td>KOR</td>
            </tr>
            <tr>
                <td rowspan="4">가족관계</td>
                <td>관 계</td>
                <td>성 명</td>
                <td colspan="2">연 령</td>
                <td colspan="2">현재직업</td>
            </tr>
            <tr>
                <td></td>
                <td></td>
                <td colspan="2"></td>
                <td colspan="2"></td>
            </tr>
            <tr>
                <td></td>
                <td></td>
                <td colspan="2"></td>
                <td colspan="2"></td>
            </tr>
            <tr>
                <td></td>
                <td></td>
                <td colspan="2"></td>
                <td colspan="2"></td>
            </tr>
            <tr>
                <td colspan="2">현 주 소</td>
                <td colspan="5">주소</td>
            </tr>
            <tr>
                <td colspan="2">이메일</td>
                <td colspan="5">email@example.com</td>
            </tr>
        </table>

        <table>
            <tr>
                <th class="period-cell">기 간</th>
                <th class="content-cell">학 력 · 병 역 · 자 격 사 항</th>
                <th class="note-cell">비 고</th>
            </tr>
            <!-- 데이터 반복 영역 -->
            <tr><td colspan="3">데이터 삽입</td></tr>
        </table>

        <table>
            <tr>
                <th class="period-cell">기 간</th>
                <th class="content-cell">경 력 사 항</th>
                <th class="note-cell">비 고</th>
            </tr>
            <!-- 데이터 반복 영역 -->
            <tr><td colspan="3">데이터 삽입</td></tr>
        </table>

        <div class="footer">
            <p>위의 기재한 내용이 사실과 다름이 없습니다.</p>
            <div class="date-line">
                YYYY년 MM월 DD일
            </div>
            <p>(인)</p>
        </div>
    </div>
</body>
</html>
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.

    """

    prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt ),
        ("user", "{input}")
    ])

    chain = prompt | llm | parser

    def parse_product(description: str) -> dict:
        result = chain.invoke({"input": description})
        # print("[AI로받은 응답.]",json.dumps(result, indent=2))

        return result
        
    description = request
    response = parse_product(description)
    print("[AI로부터 받은 응답] ",response)

    return response

########################################################## 이력서 작성 중 응답 API

########################################################## 이력서 작성 중 응답 API
async def respond_to_resume(authotization: str, user_email: str,request: ResumeRequest) -> ResumeResponse:
    try: 
        logger.info("[이력서 생성 초기화]")
        # 새로운 대화 상태 생성
        state = await start_resume_conversation(authotization, user_email, request)
        print("[user_data]",state.user_data)

        # 이력서 만드는중("[이력서 pdf 생성중...]")
        logger.info("[AI가 이력서 PDF 만드는중...]")
        pdf_form = await make_pdf(state,str(state.user_data))

        output_dir = r"C:\Users\r2com\Documents\eum-agenticAI\app\services\agentic\resume"
        os.makedirs(output_dir, exist_ok=True)

        # 저장할 파일 전체 경로
        output_path = os.path.join(output_dir, "resume.pdf")

        print("[pdf_form2] ",pdf_form['html'])
        await save_html_to_pdf(pdf_form,output_path)

        print("[upload_to_s3] 파일 업로드 시작")
        # S3 업로드
        s3_url = upload_to_s3(output_path, "pdfs/resume.pdf")
        print(f"[S3 업로드] : {s3_url}")

        return {
            "response": "이력서가 생성되었습니다.",
            "state": "first",
            "message": "PDF가 업로드되었습니다.",
            "download_url": s3_url     
        }
    
    except Exception as e:
        logger.error(f"이력서 생성 시작 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)   
        )    
########################################################## 이력서 작성 중 응답 API

########################################################## ✅ PDF 저장 함수 (save_html_to_pdf)
import os
import tempfile
from playwright.async_api import async_playwright

async def save_html_to_pdf(pdr_form: dict, output_path: str) -> str:
    """
    HTML 문자열을 PDF로 저장하는 함수
    :param pdr_form: {"html": "..."} 형태의 HTML 데이터
    :param output_path: 저장할 PDF 경로 (예: 'output/resume.pdf')
    :return: 저장된 PDF 경로
    """
    html_content = pdr_form.get("html", "")
    
    if not html_content:
        raise ValueError("pdr_form에 'html' 데이터가 없습니다.")

    # 임시 HTML 파일 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_file:
        temp_file.write(html_content)
        temp_html_path = temp_file.name

    # Playwright 사용해서 PDF 생성
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{temp_html_path}")  # ✅ HTML 파일 열기
        await page.pdf(path=output_path, format="A4")  # ✅ 지정된 경로에 저장
        logger.info(f"[output_path] : {output_path}")
        print((f"[output_path] : {output_path}"))
        # await browser.close()
        print((f"[ browser.close()] : {output_path}"))

    # 임시 HTML 삭제
    print((f"[os.remove(temp_html_path) 1 ] : {output_path}"))
    os.remove(temp_html_path)
    print((f"[os.remove(temp_html_path) 2 ] : {output_path}"))
    return output_path

########################################################## ✅ PDF 저장 함수 (save_html_to_pdf)

########################################################## 이력서 진행 상태 조회 API
async def get_resume_status(user_id: str) -> ResumeResponse:
    """이력서 생성 진행 상태 확인"""
    if user_id not in conversation_states:
        raise HTTPException(
            status_code=404,
            detail="진행 중인 이력서 생성 대화가 없습니다."
        )
    
    state = conversation_states[user_id]
    return ResumeResponse(
        status="in_progress" if not state.is_completed else "completed",
        current_field=state.current_field,
        current_question=state.current_question,
        missing_fields=state.missing_fields
    )
########################################################## 이력서 진행 상태 조회 API



########################################################## PDF 파일을 S3로 업로드하는 함수
import boto3
from botocore.exceptions import NoCredentialsError
import os

from botocore.exceptions import NoCredentialsError, ClientError

def upload_to_s3(file_path: str, object_name: str) -> str:
    try:
        print("[upload_to_s3] 파일 업로드 시작")
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            region_name=os.getenv("S3_REGION")
        )
        bucket = os.getenv("S3_BUCKET_NAME")
        if not bucket:
            raise ValueError("S3_BUCKET_NAME 환경변수가 비어있습니다.")

        logger.info("[upload_to_s3] 파일 업로드 시작")
        s3.upload_file(file_path, bucket, object_name, ExtraArgs={'ContentType': 'application/pdf'})
        
        url = f"https://{bucket}.s3.{os.getenv('S3_REGION')}.amazonaws.com/{object_name}"
        logger.info(f"[upload_to_s3] 업로드 성공: {url}")
        return url
    
    except (NoCredentialsError, ClientError, Exception) as e:
        logger.error(f"[upload_to_s3] 업로드 실패: {str(e)}")
        raise Exception(f"S3 업로드 실패: {str(e)}")

########################################################## PDF 파일을 S3로 업로드하는 함수


# 실행 진입전
class AgenticResume:
    def __init__(self):
        pass  # 필요한 초기화가 있다면 여기에

    async def Resume_function( self, query, uid, state, token ) -> Dict[str, Any]:
        """ 이력서 생성 """
        response = await job_resume( query, uid, state, token )
        logger.info(f"[Resume_function] : {response}")
        print(f"[Resume_function] : {response}")
        return response
