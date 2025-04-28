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

class ResumeConversationState:
    """이력서 생성 대화 상태 관리 클래스"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_data: Dict[str, List[Dict[str, str]]] = {}
        self.missing_fields: List[str] = []
        self.current_field: Optional[str] = None
        self.current_question: Optional[str] = None
        self.is_completed: bool = False
        self.pdf_path: Optional[str] = None

    def update_user_data(self, field: str, value: Dict[str, str]):
        """사용자 데이터 업데이트"""
        if field not in self.user_data:
            self.user_data[field] = []
        self.user_data[field].append(value)
        if field in self.missing_fields:
            self.missing_fields.remove(field)
        if not self.missing_fields:
            self.is_completed = True

    def get_next_question(self) -> Optional[str]:
        """다음 질문 가져오기"""
        if not self.missing_fields:
            return None
        self.current_field = self.missing_fields[0]
        return self.current_question

    def process_response(self, response: str) -> Dict[str, str]:
        """사용자 응답 처리"""
        if not self.current_field:
            raise ValueError("현재 진행 중인 질문이 없습니다.")
        
        # 현재 필드를 missing_fields에서 제거
        if self.current_field in self.missing_fields:
            self.missing_fields.remove(self.current_field)
            if not self.missing_fields:
                self.is_completed = True
        
        return {
            "response": response,
            "field": self.current_field
        }

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

async def process_user_response(field: str, response: str) -> Dict[str, str]:
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
        structured_data = await client.generate(prompt)
        logger.info(f"📝 LLM 응답: {structured_data}")
        
        # JSON 문자열에서 실제 JSON 부분만 추출
        import re
        json_match = re.search(r'\{[^{]*\}', structured_data, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # JSON 문자열을 파싱하여 딕셔너리로 변환
            import json
            try:
                # 작은따옴표를 큰따옴표로 변환
                json_str = json_str.replace("'", '"')
                data = json.loads(json_str)
                logger.info(f"✅ {field} 데이터 구조화 완료: {data}")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 오류: {str(e)}")
                logger.error(f"❌ 원본 JSON 문자열: {json_str}")
                raise ValueError(f"JSON 파싱 오류: {str(e)}")
        else:
            logger.error(f"❌ JSON 형식의 응답을 찾을 수 없습니다: {structured_data}")
            raise ValueError("JSON 형식의 응답을 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"🚨 응답 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"응답 처리 중 오류 발생: {str(e)}"
        )

def get_current_date() -> str:
    """현재 날짜를 이력서 형식에 맞게 반환합니다."""
    now = datetime.now()
    return f"{now.year}년 {now.month}월 {now.day}일"

# 이력서 생성 프롬프트
def generate_resume_prompt(user_data: Dict[str, List[Dict[str, str]]]) -> str:
    """이력서 생성 프롬프트"""
    # 학력 정보 포맷팅
    education_info = ""
    if 'education' in user_data:
        for edu in user_data['education']:
            education_info += f"- {edu['period']}: {edu['school']} {edu['major']} ({edu['degree']})\n"
    
    # 병역 정보 포맷팅
    military_info = ""
    if 'military_service' in user_data:
        for mil in user_data['military_service']:
            military_info += f"- {mil['period']}: {mil['branch']} {mil['rank']} ({mil['discharge']})\n"
    
    # 자격사항 정보 포맷팅
    certification_info = ""
    if 'certifications' in user_data:
        for cert in user_data['certifications']:
            certification_info += f"- {cert['period']}: {cert['name']} ({cert['issuer']}) {cert['grade']}\n"
    
    # 경력사항 정보 포맷팅
    career_info = ""
    if 'career' in user_data:
        for career in user_data['career']:
            career_info += f"- {career['period']}: {career['company']} {career['position']}\n  {career['description']}\n"
    
    return f"""
    다음은 사용자의 이력서 정보입니다.

    [기본 정보]
    이름: {user_data.get('name', [''])[0]}
    생년월일: {user_data.get('birth_date', [''])[0]}

    [학력]
    {education_info}

    [병역]
    {military_info}

    [자격사항]
    {certification_info}

    [경력사항]
    {career_info}

    위 정보를 바탕으로 전문적이고 매력적인 이력서를 작성해주세요.
    응답은 명확하고 구체적이어야 합니다.
    """

async def generate_resume_text(user_data: Dict[str, str], max_retries: int = 3) -> str:
    last_error = None
    
    for attempt in range(max_retries):
        try:
            client = get_llm_client(is_lightweight=True)
            prompt = generate_resume_prompt(user_data)
            
            logger.info(f"📤 LLM 요청 프롬프트 (시도 {attempt + 1}/{max_retries}):\n{prompt}")
            
            resume_text = await client.generate(prompt)
            
            if not resume_text or not resume_text.strip():
                raise ValueError("LLM 응답이 비어있습니다.")
                
            logger.info(f"📥 LLM 응답 성공 (처음 500자):\n{resume_text[:500]}...")
            return resume_text
            
        except Exception as e:
            last_error = e
            logger.error(f"🚨 이력서 텍스트 생성 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}", exc_info=True)
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 지수 백오프: 2초, 4초, 6초...
                logger.info(f"⏳ {wait_time}초 후 재시도합니다...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ 최대 재시도 횟수 ({max_retries}회) 도달")
                raise ValueError(f"이력서 텍스트 생성 실패 ({max_retries}회 시도): {str(last_error)}")

async def save_resume_pdf(user_data: Dict[str, Any], output_path: str) -> str:
    """사용자 데이터를 PDF로 저장합니다."""
    try:
        # 데이터 로깅
        logger.info(f"📊 PDF 생성용 사용자 데이터: {user_data}")
        
        # HTML 생성
        html_content = f"""
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
                        <td colspan="2">{user_data.get('name', '')}</td>
                        <td colspan="2">생년월일</td>
                        <td colspan="2">{user_data.get('birth_date', '')}</td>
                    </tr>
                    <tr>
                        <td>전화번호</td>
                        <td colspan="2">{user_data.get('phone', '')}</td>
                        <td colspan="2">국적</td>
                        <td>{user_data.get('nation', '')}</td>
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
                        <td colspan="5">{user_data.get('address', '')}</td>
                    </tr>
                    <tr>
                        <td colspan="2">이메일</td>
                        <td colspan="5">{user_data.get('email', '')}</td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <th class="period-cell">기 간</th>
                        <th class="content-cell">학 력 · 병 역 · 자 격 사 항</th>
                        <th class="note-cell">비 고</th>
                    </tr>
                    {''.join([
                        f'''
                        <tr>
                            <td class="period-cell">{edu.get('period', '')}</td>
                            <td class="content-cell">{edu.get('school', '')} {edu.get('major', '')} {edu.get('degree', '')}</td>
                            <td class="note-cell"></td>
                        </tr>
                        ''' for edu in user_data.get('education', [])
                    ])}
                    {''.join([
                        f'''
                        <tr>
                            <td class="period-cell">{mil.get('period', '')}</td>
                            <td class="content-cell">{mil.get('branch', '')} {mil.get('rank', '')} {mil.get('discharge', '')}</td>
                            <td class="note-cell"></td>
                        </tr>
                        ''' for mil in user_data.get('military_service', [])
                    ])}
                    {''.join([
                        f'''
                        <tr>
                            <td class="period-cell">{cert.get('period', '')}</td>
                            <td class="content-cell">{cert.get('name', '')} ({cert.get('issuer', '')}) {cert.get('grade', '')}</td>
                            <td class="note-cell"></td>
                        </tr>
                        ''' for cert in user_data.get('certifications', [])
                    ])}
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                </table>

                <table>
                    <tr>
                        <th class="period-cell">기 간</th>
                        <th class="content-cell">경 력 사 항</th>
                        <th class="note-cell">비 고</th>
                    </tr>
                    {''.join([
                        f'''
                        <tr>
                            <td class="period-cell">{career.get('period', '')}</td>
                            <td class="content-cell">{career.get('company', '')} {career.get('position', '')}</td>
                            <td class="note-cell">{career.get('description', '')}</td>
                        </tr>
                        ''' for career in user_data.get('career', [])
                    ])}
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                    <tr><td class="period-cell"></td><td class="content-cell"></td><td class="note-cell"></td></tr>
                </table>

                <div class="footer">
                    <p>위의 기재한 내용이 사실과 다름이 없습니다.</p>
                    <div class="date-line">
                        {get_current_date()}
                    </div>
                    <p>(인)</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 임시 HTML 파일 생성
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_file.write(html_content.encode('utf-8'))
            temp_path = temp_file.name
        
        # Playwright를 사용하여 PDF 생성
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f'file://{temp_path}')
            await page.pdf(path=output_path)
            await browser.close()
        
        # 임시 파일 삭제
        import os
        os.unlink(temp_path)
        
        logger.info(f"✅ PDF 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"🚨 PDF 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF 생성 중 오류 발생: {str(e)}"
        )

async def start_resume_conversation(user_id: str) -> ResumeConversationState:
    """이력서 생성 대화 시작"""
    state = ResumeConversationState(user_id)
    
    # 1. 사용자 프로필 정보 가져오기
    state.user_data = await get_user_profile(user_id)
    logger.info(f"📊 사용자 프로필 정보: {state.user_data}")
    
    # 2. 부족한 정보 확인
    state.missing_fields = await check_missing_info(state.user_data)
    if state.missing_fields:
        logger.info(f"⚠️ 부족한 정보: {state.missing_fields}")
        # 첫 번째 질문 생성
        state.current_field = state.missing_fields[0]
        state.current_question = await ask_for_missing_info(state.current_field)
    
    return state

async def process_resume_response(state: ResumeConversationState, response: str) -> Dict[str, str]:
    """사용자 응답 처리 및 다음 단계 진행"""
    try:
        # 1. 현재 응답 처리
        processed_data = await process_user_response(state.current_field, response)
        logger.info(f"✅ {state.current_field} 정보 업데이트: {processed_data}")
        
        # 2. 사용자 데이터 업데이트
        field_mapping = {
            '학력': 'education',
            '병역': 'military_service',
            '자격사항': 'certifications',
            '경력사항': 'career'
        }
        
        english_field = field_mapping.get(state.current_field)
        if english_field:
            if english_field not in state.user_data:
                state.user_data[english_field] = []
            state.user_data[english_field].append(processed_data)
            logger.info(f"📝 업데이트된 사용자 데이터: {state.user_data}")
        
        # 3. 현재 필드를 missing_fields에서 제거
        if state.current_field in state.missing_fields:
            state.missing_fields.remove(state.current_field)
            if not state.missing_fields:
                state.is_completed = True
        
        # 4. 다음 질문 생성 또는 이력서 생성
        if state.is_completed:
            # 모든 정보 수집 완료 - 이력서 생성
            resume_text = await generate_resume_text(state.user_data)
            
            # 임시 디렉토리에 PDF 파일 생성
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, f"{state.user_data.get('name', 'resume')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            
            await save_resume_pdf(state.user_data, pdf_path)
            state.pdf_path = pdf_path
            
            return {
                'status': 'completed',
                'message': '이력서가 성공적으로 생성되었습니다.',
                'pdf_path': pdf_path
            }
        else:
            # 다음 질문 생성
            state.current_field = state.missing_fields[0]
            state.current_question = await ask_for_missing_info(state.current_field)
            
            return {
                'status': 'continue',
                'question': state.current_question,
                'field': state.current_field
            }
            
    except Exception as e:
        logger.error(f"🚨 응답 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"응답 처리 중 오류 발생: {str(e)}"
        )