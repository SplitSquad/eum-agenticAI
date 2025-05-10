import os
import tempfile
from typing import Dict, List, Optional, TypedDict, Any
import asyncio
from datetime import datetime, date
import httpx
from fastapi import HTTPException
from playwright.async_api import async_playwright
from app.core.llm_client import get_llm_client
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import subprocess
from pydantic import BaseModel

class ResumeRequest(BaseModel):
    """이력서 생성 요청 모델"""
    response: str

class EducationInfo(TypedDict):
    period: str
    school: str
    major: str
    degree: str

class MilitaryInfo(TypedDict):
    period: str
    branch: str
    rank: str
    discharge: str

class CertificationInfo(TypedDict):
    period: str
    name: str
    issuer: str
    grade: str

class CareerInfo(TypedDict):
    period: str
    company: str
    position: str
    description: str

# 필요한 정보 목록
REQUIRED_FIELDS = {
    'birth_date': '생년월일',
    'education': '학력',
    'military_service': '병역',
    'certifications': '자격사항',
    'career': '경력사항'
}

async def test_resume_generation():
    """이력서 생성 테스트 함수"""
    try:
        # 1. HTML 생성
        pdf_form = await make_pdf("test", TEST_USER_DATA)
        
        # 2. 출력 디렉토리 생성
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. PDF 저장
        output_path = os.path.join(output_dir, "test_resume.pdf")
        await save_html_to_pdf(pdf_form, output_path)
        
        logger.info(f"✅ 테스트 이력서가 생성되었습니다: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {str(e)}")
        raise

class ResumeConversationState:
    """이력서 생성 대화 상태 관리 클래스 (대화형)"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_step: str = "start"  # start -> edu_cert -> career -> completed
        self.edu_cert_input: Optional[str] = None
        self.career_input: Optional[str] = None
        self.education: Optional[list] = None
        self.certifications: Optional[list] = None
        self.career: Optional[list] = None
        self.is_completed: bool = False
        self.user_data: Optional[Dict[str, Any]] = None

    async def initialize(self, authorization: str, user_email: str, request: ResumeRequest) -> None:
        """사용자 프로필 정보 초기화"""
        try:
            # 사용자 프로필 정보 가져오기
            logger.info("[ 사용자 프로필 정보 백으로 api 요청중...] ")
            self.user_data = await get_user_profile(user_email)
            
            # 필요한 정보 요청
            logger.info("[ 필요한 프로필 정보 백으로 api 요청중...] ")
            missing_fields = await check_missing_info(self.user_data)
            
            if missing_fields:
                for field in missing_fields:
                    question = await ask_for_missing_info(field)
                    response = request.response
                    result = await process_user_response(field, response)
                    self.user_data[field] = result
            
        except Exception as e:
            logger.error(f"초기화 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"초기화 실패: {str(e)}"
            )

    async def missing_info(self, authorization: str, user_email: str, request: ResumeRequest) -> None:
        """필요한 정보 요청"""
        try:
            # 필요한 정보 요청
            logger.info("[ 필요한 프로필 정보 백으로 api 요청중...] ")
            missing_fields = await check_missing_info(self.user_data)
            
            if missing_fields:
                for field in missing_fields:
                    question = await ask_for_missing_info(field)
                    response = request.response
                    result = await process_user_response(field, response)
                    self.user_data[field] = result
            
        except Exception as e:
            logger.error(f"필요한 정보 요청 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"필요한 정보 요청 실패: {str(e)}"
            )

async def start_resume_conversation(user_id: str) -> ResumeConversationState:
    state = ResumeConversationState(user_id)
    return state

async def get_resume_question(state: ResumeConversationState) -> str:
    if state.current_step == "start":
        state.current_step = "edu_cert"
        return "학력과 자격사항을 한 번에 입력해 주세요.\n예시: 2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격"
    elif state.current_step == "edu_cert":
        return "학력과 자격사항을 한 번에 입력해 주세요.\n예시: 2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격"
    elif state.current_step == "career":
        return "경력사항을 모두 입력해 주세요.\n예시: 2016-2018 네이버 소프트웨어 엔지니어(검색 엔진 개발), 2018-2020 카카오 시니어 개발자(메시징 플랫폼 개발)"
    else:
        return "이력서 정보가 모두 입력되었습니다."

async def process_resume_conversation_response(state: ResumeConversationState, response: str) -> dict:
    """사용자 응답 처리 및 상태 전이"""
    if state.current_step == "edu_cert":
        state.edu_cert_input = response
        # OpenAI 파싱
        result = await parse_edu_cert_with_openai(response)
        state.education = result.get("education", [])
        state.certifications = result.get("certifications", [])
        state.current_step = "career"
        return {"message": "경력사항을 모두 입력해 주세요. 예시: 2016-2018 네이버 소프트웨어 엔지니어(검색 엔진 개발)", "state": state}
    elif state.current_step == "career":
        state.career_input = response
        # OpenAI 파싱
        result = await parse_career_with_openai(response)
        state.career = result
        state.current_step = "completed"
        state.is_completed = True
        return {"message": "이력서 정보가 모두 입력되었습니다.", "state": state}
    else:
        return {"message": "이미 이력서 정보가 모두 입력되었습니다.", "state": state}

async def get_user_profile(user_id: str) -> Dict[str, str]:
    """실제 백엔드 API를 통해 사용자 프로필 정보를 가져옵니다."""
    try:
        # 테스트용 데이터 사용
        user_data = {
            'userId': 'test123',
            'email': 'test@test.com',
            'name': '홍길동',
            'nation': '대한민국',
            'gender': '남자',
            'language': '한국어',
            'purpose': '취업',
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

async def check_missing_info(user_data: Dict[str, str]) -> List[str]:
    """부족한 정보를 확인합니다."""
    missing_fields = []
    for field, description in REQUIRED_FIELDS.items():
        if not user_data.get(field):
            missing_fields.append(description)
    return missing_fields

async def ask_for_missing_info(field: str) -> str:
    """AI가 부족한 정보에 대해 질문하고 응답을 받습니다."""
    client = get_llm_client(is_lightweight=True)
    
    field_prompts = {
        'education': """
        사용자의 학력 정보가 필요합니다.
        다음 정보를 순서대로 물어보세요:
        1. 기간 (입학년월 ~ 졸업년월)
        2. 학교명
        3. 전공
        4. 학위
        """,
        'military_service': """
        사용자의 병역 정보가 필요합니다.
        다음 정보를 순서대로 물어보세요:
        1. 기간 (입대년월 ~ 전역년월)
        2. 군종
        3. 계급
        4. 전역사유
        """,
        'certifications': """
        사용자의 자격사항 정보가 필요합니다.
        다음 정보를 순서대로 물어보세요:
        1. 취득일
        2. 자격증명
        3. 발급기관
        4. 등급
        """,
        'career': """
        사용자의 경력사항 정보가 필요합니다.
        다음 정보를 순서대로 물어보세요:
        1. 기간 (입사년월 ~ 퇴사년월)
        2. 회사명
        3. 직위
        4. 담당업무
        """
    }
    
    prompt = field_prompts.get(field, f"""
    사용자의 {field} 정보가 필요합니다.
    사용자에게 {field}에 대해 자연스럽게 질문해주세요.
    질문은 한 문장으로 간단하게 작성해주세요.
    """)
    
    question = await client.generate(prompt)
    return question.strip()

async def process_user_response(field: str, response: str) -> Dict[str, Any]:
    """사용자의 응답을 처리하고 구조화된 데이터로 변환합니다."""
    client = get_llm_client(is_lightweight=True)
    
    field_prompts = {
        '학력': f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "period": "2018.03 ~ 2022.02",
            "school": "서울대학교",
            "major": "컴퓨터공학과",
            "degree": "학사"
        }}
        """,
        '병역': f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "period": "2022.03 ~ 2023.12",
            "branch": "육군",
            "rank": "병장",
            "discharge": "만기제대"
        }}
        """,
        '자격사항': f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "period": "2022.03",
            "name": "정보처리기사",
            "issuer": "한국산업인력공단",
            "grade": "합격"
        }}
        """,
        '경력사항': f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "period": "2024.01 ~ 현재",
            "company": "삼성전자",
            "position": "선임연구원",
            "description": "AI 알고리즘 개발"
        }}
        """
    }
    
    prompt = field_prompts.get(field)
    if not prompt:
        prompt = f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "{field}": "구조화된 데이터"
        }}
        """
    
    try:
        llm_response = await client.generate(prompt)
        logger.info(f"📝 LLM 응답: {llm_response}")
        
        # JSON 문자열에서 실제 JSON 부분만 추출
        import re, json
        json_match = re.search(r'\{[^}]*\}', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # 작은따옴표를 큰따옴표로 변환
            json_str = json_str.replace("'", '"')
            # 줄바꿈과 공백 제거
            json_str = re.sub(r'\s+', '', json_str)
            try:
                data = json.loads(json_str)
                logger.info(f"✅ {field} 데이터 구조화 완료: {data}")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 오류: {str(e)}")
                logger.error(f"❌ 원본 JSON 문자열: {json_str}")
                # 기본값 반환
                return {field: response}
        else:
            logger.error(f"❌ JSON 형식의 응답을 찾을 수 없음: {llm_response}")
            # 기본값 반환
            return {field: response}
    except Exception as e:
        logger.error(f"🚨 응답 처리 중 오류 발생: {str(e)}")
        # 기본값 반환
        return {field: response}

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
async def job_resume(query: str, uid: str, state: str, token: str) -> Dict[str, Any]:
    authotization = token
    user_email = uid
    pre_state = state
    logger.info(f"[job_resume parameter] : {authotization} , {user_email} , {pre_state}")

    ## 첫번째 응답 - 학력/자격사항 질문
    if pre_state == "first":
        logger.info("[first_response] - 학력/자격사항 질문")
        return {
            "response": "학력과 자격사항을 입력해주세요.\n예시: 2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격",
            "state": "second"
        }
    
    ## 두번째 응답 - 경력사항 질문
    elif pre_state == "second":
        logger.info("[second_response] - 경력사항 질문")
        request = ResumeRequest(response=query)
        try:
            # 이력서 생성 초기화
            logger.info("[이력서 생성 초기화]")
            resume_state = await start_resume_conversation(authotization, user_email, request)
            
            # 학력/자격사항 파싱
            edu_cert_result = await parse_edu_cert_with_openai(query)
            resume_state.user_data['education'] = edu_cert_result.get('education', [])
            resume_state.user_data['certifications'] = edu_cert_result.get('certifications', [])
            
            # 상태 저장
            conversation_states[user_email] = resume_state
            
            return {
                "response": "경력사항을 입력해주세요.\n예시: 2016-2018 네이버 소프트웨어 엔지니어(검색 엔진 개발), 2018-2020 카카오 시니어 개발자(메시징 플랫폼 개발)",
                "state": "third"
            }
            
        except Exception as e:
            logger.error(f"이력서 생성 시작 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    
    ## 세번째 응답 - 이력서 생성 및 S3 업로드
    elif pre_state == "third":
        logger.info("[third_response] - 이력서 생성 및 S3 업로드")
        try:
            # 저장된 상태 가져오기
            resume_state = conversation_states.get(user_email)
            if not resume_state:
                raise HTTPException(
                    status_code=400,
                    detail="이력서 생성 세션이 만료되었습니다. 처음부터 다시 시작해주세요."
                )
            
            # 경력사항 파싱
            career_result = await parse_career_with_openai(query)
            resume_state.user_data['career'] = career_result
            
            # 이력서 PDF 생성
            logger.info("[AI가 이력서 PDF 만드는중...]")
            pdf_form = await make_pdf(resume_state, resume_state.user_data)

            output_dir = os.path.join(os.getcwd(), "app/services/agentic/resume")
            os.makedirs(output_dir, exist_ok=True)

            # 저장할 파일 전체 경로
            output_path = os.path.join(output_dir, "resume.pdf")
            await save_html_to_pdf(pdf_form, output_path)

            # S3 업로드
            logger.info("[upload_to_s3] 파일 업로드 시작")
            s3_url = upload_to_s3(output_path, "pdfs/resume.pdf")
            logger.info(f"[S3 업로드] : {s3_url}")

            # 상태 제거
            del conversation_states[user_email]

            return {
                "response": "이력서가 생성되었습니다.",
                "state": "first",
                "message": "PDF가 업로드되었습니다.",
                "download_url": s3_url     
            }
            
        except Exception as e:
            logger.error(f"이력서 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    else:
        logger.error("잘못된 상태입니다.")
        return {
            "response": "잘못된 상태입니다.",
            "state": "error"
        }
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
async def make_pdf(state: str, user_data: dict):
    """
    사용자 데이터를 받아 HTML 이력서 생성 (병역 삭제, 학력/자격/경력 5개 고정, 빈칸 채움)
    """
    def get_current_date():
        today = date.today()
        return f"{today.year}년 {today.month:02d}월 {today.day:02d}일"

    # 가족사항 3줄 생성 (빈 줄 포함)
    family_rows = user_data.get('family', [])
    family_rows = (family_rows + [{}]*3)[:3]  # 최대 3줄로 제한
    family_html = ''
    family_html += '''
        <tr>
            <td rowspan="4">가족관계</td>
            <td>관 계</td>
            <td>성 명</td>
            <td colspan="2">연 령</td>
            <td colspan="2">현재직업</td>
        </tr>
    '''
    for row in family_rows:
        family_html += f'''
        <tr>
            <td>{row.get('relation', '')}</td>
            <td>{row.get('name', '')}</td>
            <td colspan="2">{row.get('age', '')}</td>
            <td colspan="2">{row.get('job', '')}</td>
        </tr>
        '''

    # 학력/자격사항 5개 row 생성
    education_rows = user_data.get('education', [])
    certifications_rows = user_data.get('certifications', [])
    edu_cert_rows = education_rows + certifications_rows
    edu_cert_rows = (edu_cert_rows + [{}]*5)[:5]
    edu_cert_html = ''.join([
        f'''<tr>\n<td class="period-cell">{row.get('period', '')}</td>\n<td class="content-cell">{row.get('school', row.get('name', ''))} {row.get('major', '')} {row.get('degree', '')} {row.get('issuer', '')} {row.get('grade', '')}</td>\n<td class="note-cell"></td>\n</tr>''' for row in edu_cert_rows
    ])

    # 경력사항 5개 row 생성
    career_rows = user_data.get('career', [])
    career_rows = (career_rows + [{}]*5)[:5]
    career_html = ''.join([
        f'''<tr>\n<td class="period-cell">{row.get('period', '')}</td>\n<td class="content-cell">{row.get('company', '')} {row.get('position', '')}</td>\n<td class="note-cell">{row.get('description', '')}</td>\n</tr>''' for row in career_rows
    ])

    html_content = f"""
    <!DOCTYPE html>
    <html lang=\"ko\">
    <head>
        <meta charset=\"UTF-8\">
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
        <div class=\"page\">
            <table class=\"header-table\">
                <tr>
                    <td rowspan=\"3\" class=\"photo-cell\">(사 진)</td>
                    <td colspan=\"6\"><h1>이 력 서</h1></td>
                </tr>
                <tr>
                    <td>성 명</td>
                    <td colspan=\"2\">{user_data.get('name', '')}</td>
                    <td colspan=\"2\">생년월일</td>
                    <td colspan=\"2\">{user_data.get('birth_date', '')}</td>
                </tr>
                <tr>
                    <td>전화번호</td>
                    <td colspan=\"2\">{user_data.get('phone', '')}</td>
                    <td colspan=\"2\">국적</td>
                    <td>{user_data.get('nation', '')}</td>
                </tr>
                {family_html}
                <tr>
                    <td colspan=\"2\">현 주 소</td>
                    <td colspan=\"5\">{user_data.get('address', '')}</td>
                </tr>
                <tr>
                    <td colspan=\"2\">이메일</td>
                    <td colspan=\"5\">{user_data.get('email', '')}</td>
                </tr>
            </table>

            <table>
                <tr>
                    <th class=\"period-cell\">기 간</th>
                    <th class=\"content-cell\">학 력 · 자 격 사 항</th>
                    <th class=\"note-cell\">비 고</th>
                </tr>
                {edu_cert_html}
            </table>

            <table>
                <tr>
                    <th class=\"period-cell\">기 간</th>
                    <th class=\"content-cell\">경 력 사 항</th>
                    <th class=\"note-cell\">비 고</th>
                </tr>
                {career_html}
            </table>

            <div class=\"footer\">
                <p>위의 기재한 내용이 사실과 다름이 없습니다.</p>
                <div class=\"date-line\">
                    {get_current_date()}
                </div>
                <p>(인)</p>
            </div>
        </div>
    </body>
    </html>
    """
    return {"html": html_content}

########################################################## 이력서 작성 중 응답 API
async def respond_to_resume(user_id: str, request: ResumeRequest) -> ResumeResponse:
    """이력서 생성 대화 응답 처리"""
    try:
        # 대화 상태 확인
        if user_id not in conversation_states:
            raise HTTPException(
                status_code=400,
                detail="진행 중인 이력서 생성 대화가 없습니다."
            )
        
        state = conversation_states[user_id]
        result = await process_resume_conversation_response(state, request.response)
        
        # 대화가 완료된 경우 상태 제거
        if result["status"] == "completed":
            del conversation_states[user_id]
        
        return ResumeResponse(**result)
        
    except Exception as e:
        logger.error(f"이력서 생성 응답 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
########################################################## 이력서 작성 중 응답 API

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

async def ask_edu_cert_question(state: ResumeConversationState) -> str:
    state.current_step = "edu_cert"
    return "학력과 자격사항을 한 번에 입력해 주세요.\n예시: 2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격"

async def ask_career_question(state: ResumeConversationState) -> str:
    state.current_step = "career"
    return "경력사항을 모두 입력해 주세요.\n예시: 2016-2018 네이버 소프트웨어 엔지니어(검색 엔진 개발), 2018-2020 카카오 시니어 개발자(메시징 플랫폼 개발)"

async def parse_edu_cert_with_openai(user_input: str) -> dict:
    """OpenAI로 학력/자격사항을 리스트로 파싱 (JSON 파싱 robust)"""
    prompt = f"""
    다음 사용자의 입력을 분석하여 학력(education)과 자격사항(certifications)을 각각 리스트로 JSON으로 반환하세요.
    - 학력: period, school, major, degree
    - 자격사항: period, name, issuer, grade
    예시 입력: 2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격
    반드시 아래와 같은 JSON만 반환:
    {{
      "education": [{{"period": "", "school": "", "major": "", "degree": ""}}...],
      "certifications": [{{"period": "", "name": "", "issuer": "", "grade": ""}}...]
    }}
    입력: {user_input}
    """
    llm = ChatOpenAI(api_key=os.getenv("HIGH_PERFORMANCE_OPENAI_API_KEY"), model_name=os.getenv("HIGH_PERFORMANCE_OPENAI_MODEL"), timeout=int(os.getenv("HIGH_PERFORMANCE_OPENAI_TIMEOUT")))
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    import json, re
    
    # 응답에서 JSON 형식 찾기
    json_match = re.search(r'\{[\s\S]*\}', response.content)
    if json_match:
        json_str = json_match.group(0)
        json_str = json_str.replace("'", '"')  # 작은따옴표를 큰따옴표로 변환
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return {
                    "education": parsed.get("education", []),
                    "certifications": parsed.get("certifications", [])
                }
        except Exception as e:
            logger.error(f"JSON 파싱 오류: {str(e)}")
            logger.error(f"원본 JSON 문자열: {json_str}")
            
    # 파싱 실패 시 빈 딕셔너리 반환
    logger.error(f"OpenAI 응답에서 유효한 JSON을 찾을 수 없음: {response.content}")
    return {"education": [], "certifications": []}

async def parse_career_with_openai(user_input: str) -> list:
    """OpenAI로 경력사항을 리스트로 파싱"""
    prompt = f"""
    다음 경력사항을 JSON 형식으로 변환하세요:
    입력: {user_input}

    다음과 같은 형식의 JSON으로만 응답하세요:
    {{
      "career": [
        {{
          "period": "2016-2018",
          "company": "네이버",
          "position": "소프트웨어 엔지니어",
          "description": "검색 엔진 개발"
        }},
        {{
          "period": "2018-2020",
          "company": "카카오",
          "position": "시니어 개발자",
          "description": "메시징 플랫폼 개발"
        }}
      ]
    }}
    """
    llm = ChatOpenAI(api_key=os.getenv("HIGH_PERFORMANCE_OPENAI_API_KEY"), model_name=os.getenv("HIGH_PERFORMANCE_OPENAI_MODEL"), timeout=int(os.getenv("HIGH_PERFORMANCE_OPENAI_TIMEOUT")))
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    
    # 응답에서 JSON 형식 찾기
    import json, re
    json_match = re.search(r'\{[\s\S]*\}', response.content)
    if json_match:
        try:
            json_str = json_match.group(0)
            json_str = json_str.replace("'", '"')  # 작은따옴표를 큰따옴표로 변환
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and "career" in parsed and isinstance(parsed["career"], list):
                logger.info(f"경력사항 파싱 성공: {parsed['career']}")
                return parsed["career"]
        except Exception as e:
            logger.error(f"JSON 파싱 오류: {str(e)}")
            logger.error(f"원본 JSON 문자열: {json_str}")
    
    # 파싱 실패 시 직접 파싱 시도
    try:
        career = []
        items = user_input.split(", ")
        for item in items:
            match = re.search(r'(\d{4}-\d{4})\s+(\S+)\s+([^(]+)\(([^)]+)\)', item)
            if match:
                career.append({
                    "period": match.group(1),
                    "company": match.group(2),
                    "position": match.group(3).strip(),
                    "description": match.group(4)
                })
        if career:
            logger.info(f"정규식으로 경력사항 파싱 성공: {career}")
            return career
    except Exception as e:
        logger.error(f"정규식 파싱 오류: {str(e)}")
    
    logger.error(f"경력사항 파싱 실패. OpenAI 응답: {response.content}")
    return []

async def save_html_to_pdf(html_content: dict, output_path: str):
    """HTML을 PDF로 변환하여 저장"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content['html'])
        await page.pdf(path=output_path, format='A4')
        await browser.close()

async def test_resume_pdf_conversation():
    """대화형 플로우를 더미 입력으로 자동 진행하고, PDF까지 생성 및 열기"""
    state = ResumeConversationState("test_user")

    # 1. 학력/자격사항 질문 및 더미 입력
    print("[Q]", await get_resume_question(state))
    edu_cert_input = "2010-2014 한국조리사관학교 호텔조리학과 졸업, 2014 한식조리기능사(한국산업인력공단) 합격, 2015 양식조리기능사(한국산업인력공단) 합격"
    await process_resume_conversation_response(state, edu_cert_input)

    # 2. 경력사항 질문 및 더미 입력
    print("[Q]", await get_resume_question(state))
    career_input = "2014-2016 신라호텔 한식당 수석요리사(전통 한식 메뉴 개발 및 조리), 2016-2018 롯데호텔 양식당 부주방장(이탈리안 요리 전문), 2018-2020 그랜드하얏트 호텔 주방장(한식당 총괄 및 메뉴 기획)"
    await process_resume_conversation_response(state, career_input)

    # 3. PDF 생성
    user_data = {
        'name': '김요리',
        'birth_date': '1992-05-15',
        'phone': '010-1234-5678',
        'nation': '대한민국',
        'address': '서울시 강남구 테헤란로 123',
        'email': 'chef.kim@example.com',
        'education': state.education or [],
        'certifications': state.certifications or [],
        'career': state.career or []
    }
    pdf_form = await make_pdf(state, user_data)
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "chef_resume.pdf")
    await save_html_to_pdf(pdf_form, output_path)
    print(f"[PDF 생성 완료] {output_path}")
    # PDF 열기 (macOS)
    subprocess.run(["open", output_path])

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_resume_pdf_conversation())
