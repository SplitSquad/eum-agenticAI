from dotenv import load_dotenv
import os
from pathlib import Path

# .env 파일 경로 설정 및 로딩
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Optional, List, Any, Tuple
from app.core.llm_client import get_llm_client
from loguru import logger
from pydantic import BaseModel
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime
import tempfile
import uuid
from playwright.async_api import async_playwright
from langchain_openai import ChatOpenAI
import re
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from docx import Document

class CoverLetterConversationState(BaseModel):
    """자기소개서 생성 대화 상태 관리 클래스"""
    user_id: str
    current_step: str = "start"  # start -> job_info -> experience -> motivation -> completion
    job_keywords: Optional[str] = None
    experience: Optional[str] = None
    motivation: Optional[str] = None
    cover_letter: Optional[str] = None
    is_completed: bool = False
    pdf_path: Optional[str] = None
    s3_url: Optional[str] = None

async def start_cover_letter_conversation(user_id: str) -> CoverLetterConversationState:
    """자기소개서 생성 대화 시작"""
    state = CoverLetterConversationState(
        user_id=user_id,
        current_step="start"
    )
    logger.info(f"자기소개서 대화 시작: user_id={user_id}")
    return state

async def upload_to_s3(file_path: str, bucket_name: str) -> str:
    """파일을 S3에 업로드하고 URL을 반환합니다."""
    try:
        # 환경변수 체크
        access_key = os.getenv('S3_ACCESS_KEY')
        secret_key = os.getenv('S3_SECRET_KEY')
        region = os.getenv('S3_REGION', 'ap-northeast-2')
        
        if not access_key or not secret_key:
            logger.error("S3 인증 정보가 누락되었습니다. 환경변수를 확인해주세요.")
            logger.error(f"S3_ACCESS_KEY: {'설정됨' if access_key else '미설정'}")
            logger.error(f"S3_SECRET_KEY: {'설정됨' if secret_key else '미설정'}")
            raise ValueError("S3 인증 정보가 누락되었습니다.")
            
        if not bucket_name:
            logger.error("S3_BUCKET_NAME이 설정되지 않았습니다.")
            raise ValueError("S3_BUCKET_NAME이 설정되지 않았습니다.")
            
        # 파일 존재 여부 체크
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")
            
        # S3 클라이언트 생성
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # 파일 이름 추출
        file_name = os.path.basename(file_path)
        
        # S3에 업로드
        try:
            s3_client.upload_file(
                file_path,
                bucket_name,
                f"cover-letters/{file_name}",
                ExtraArgs={'ContentType': 'application/pdf'}
            )
            # URL 생성
            url = f"https://{bucket_name}.s3.amazonaws.com/cover-letters/{file_name}"
            logger.info(f"S3 업로드 완료: {url}")
            return url
        except ClientError as e:
            logger.error(f"S3 업로드 실패 (ClientError): {str(e)}")
            raise
        except Exception as e:
            logger.error(f"S3 업로드 실패 (기타 에러): {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"S3 업로드 중 오류 발생: {str(e)}")
        raise

async def save_cover_letter_pdf(cover_letter: str, output_path: str) -> str:
    """자기소개서를 PDF로 저장"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # HTML 템플릿 생성
        html_content = generate_cover_letter_html(cover_letter)
        
        # PDF 생성
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            try:
                # HTML 콘텐츠 로드
                await page.set_content(html_content)
                # PDF로 저장
                await page.pdf(path=output_path, format='A4')
                logger.info(f"PDF 생성 완료: {output_path}")
                return output_path
            except Exception as e:
                logger.error(f"Playwright PDF 생성 중 오류: {str(e)}")
                raise
            finally:
                await browser.close()
    except Exception as e:
        logger.error(f"PDF 저장 중 오류 발생: {str(e)}")
        raise

def _clean_section_text(text: str) -> str:
    """문단 내 불필요한 줄바꿈, 중복 공백, 어색한 분리 등을 정제하여 자연스럽게 만듦"""
    import re
    # 여러 줄바꿈을 하나의 문단 구분(\n\n)으로 통일
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 문장 중간의 불필요한 줄바꿈(문장 끝이 아닌 곳의 \n)을 공백으로 치환
    text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
    # 문장 끝(마침표, 물음표, 느낌표 등) 뒤에 붙은 \n은 문단 구분으로 유지
    text = re.sub(r'([.!?])\n', r'\1\n', text)
    # 중복 공백 제거
    text = re.sub(r' +', ' ', text)
    # 앞뒤 공백/줄바꿈 정리
    text = text.strip()
    return text

def split_cover_letter_sections(cover_letter: str):
    """AI가 생성한 자기소개서를 4개 항목으로 분리 (정확한 번호와 제목 기준, 중복 없이, 불필요한 텍스트 제거 및 자연스러운 문단 정리)"""
    import re
    pattern = r"[\[]?1[\].]? ?성장 과정 및 가치관[\]]?(.*?)(?=\n?\[?2[\].]? ?지원 동기 및 포부[\]]?|\Z)" \
              r"|\[?2[\].]? ?지원 동기 및 포부[\]]?(.*?)(?=\n?\[?3[\].]? ?역량 및 경험[\]]?|\Z)" \
              r"|\[?3[\].]? ?역량 및 경험[\]]?(.*?)(?=\n?\[?4[\].]? ?입사 후 계획[\]]?|\Z)" \
              r"|\[?4[\].]? ?입사 후 계획[\]]?(.*)"
    sections = [None, None, None, None]
    matches = list(re.finditer(pattern, cover_letter, re.DOTALL))
    for m in matches:
        for i in range(4):
            if m.group(i+1):
                sections[i] = m.group(i+1).strip()
    # fallback: 문단 4등분
    if not all(sections):
        paras = [p.strip() for p in re.split(r'\n{2,}', cover_letter) if p.strip()]
        n = len(paras)
        chunk = max(1, n // 4)
        sections = ["\n\n".join(paras[i*chunk:(i+1)*chunk]) for i in range(4)]
        if n > chunk*4:
            sections[3] += "\n\n" + "\n\n".join(paras[chunk*4:])
    clean_sections = []
    for idx, sec in enumerate(sections):
        if not sec:
            clean_sections.append('')
            continue
        sec = re.sub(r'자기소개서', '', sec)
        sec = re.sub(r'\[.*?\]', '', sec)
        sec = re.sub(r'^[0-9]+\.? ?[가-힣 ]+', '', sec)
        sec = sec.strip()
        # 추가: 자연스러운 문단/공백/줄바꿈 정제
        sec = _clean_section_text(sec)
        clean_sections.append(sec)
    return tuple(clean_sections)

def generate_cover_letter_html(cover_letter: str) -> str:
    """자기소개서 HTML 생성 (한 페이지에 여러 칸, 칸이 넘칠 때만 자동 페이지 분리, 불필요한 텍스트 제거 및 자연스러운 문단 정리)"""
    import re
    growth, motivation, experience, plan = split_cover_letter_sections(cover_letter)
    # 각 항목별로 마크다운 '**' 완전 제거
    growth = re.sub(r'\*\*', '', growth)
    motivation = re.sub(r'\*\*', '', motivation)
    experience = re.sub(r'\*\*', '', experience)
    plan = re.sub(r'\*\*', '', plan)
    html = f"""
    <!DOCTYPE html>
    <html lang=\"ko\">
    <head>
        <meta charset=\"UTF-8\">
        <style>
            @page {{ size: A4; margin: 0; }}
            body {{ font-family: 'Batang', serif; margin: 0; padding: 0; line-height: 1.5; }}
            .page {{ width: 210mm; min-height: 297mm; padding: 15mm 20mm; box-sizing: border-box; }}
            .cover-letter-title {{ font-size: 28px; font-weight: bold; margin-bottom: 40px; text-align: center; letter-spacing: 10px; }}
            .section {{ border: 2px solid #000; margin-bottom: 30px; padding: 18px 20px; border-radius: 6px; page-break-inside: avoid; }}
            .section-title {{ font-weight: bold; font-size: 16px; margin-bottom: 10px; }}
            .section-content {{ white-space: pre-wrap; font-size: 13px; }}
            .footer {{ margin-top: 60px; text-align: center; font-size: 12px; }}
            .date-line {{ margin: 30px 0; line-height: 2; }}
        </style>
    </head>
    <body>
        <div class=\"page\">
            <div class=\"cover-letter-title\">자기소개서</div>
            <div class=\"section section1\">
                <div class=\"section-title\">1. 성장 과정 및 가치관</div>
                <div class=\"section-content\">{growth}</div>
            </div>
            <div class=\"section section2\">
                <div class=\"section-title\">2. 지원 동기 및 포부</div>
                <div class=\"section-content\">{motivation}</div>
            </div>
            <div class=\"section section3\">
                <div class=\"section-title\">3. 역량 및 경험</div>
                <div class=\"section-content\">{experience}</div>
            </div>
            <div class=\"section section4\">
                <div class=\"section-title\">4. 입사 후 계획</div>
                <div class=\"section-content\">{plan}</div>
            </div>
            <div class=\"footer\">
                <p>위의 기재한 내용이 사실과 다름이 없습니다.</p>
                <div class=\"date-line\">{datetime.now().strftime('%Y년 %m월 %d일')}</div>
                <p>(인)</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

async def process_cover_letter_response(state: CoverLetterConversationState, response: str) -> Dict[str, Any]:
    """사용자 응답 처리 및 자기소개서 생성"""
    try:
        if state.current_step == "start":
            # 첫 응답에서는 직무 정보를 저장하고 경험에 대해 물어봄
            state.job_keywords = response
            state.current_step = "experience"
            return {
                "message": "해당 분야에서의 구체적인 경험이나 프로젝트에 대해 말씀해 주세요. 어떤 기술을 사용했고, 어떤 성과를 이루었나요?",
                "state": state
            }
        elif state.current_step == "experience":
            # 경험 정보를 받고 지원 동기를 물어봄
            state.experience = response
            state.current_step = "motivation"
            return {
                "message": "이 직무를 선택하게 된 동기와 앞으로의 목표에 대해 말씀해 주세요.",
                "state": state
            }
        elif state.current_step == "motivation":
            # 모든 정보를 받고 자기소개서 생성
            state.motivation = response
            state.cover_letter = await generate_cover_letter(
                state.job_keywords,
                state.experience,
                state.motivation
            )
            
            if not state.cover_letter:
                raise ValueError("자기소개서 생성에 실패했습니다.")
                
            state.is_completed = True
            state.current_step = "completed"
            
            try:
                # 랜덤 파일 이름 생성
                random_filename = f"cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"
                temp_dir = tempfile.gettempdir()
                pdf_path = os.path.join(temp_dir, random_filename)
                
                # PDF 파일 생성
                await save_cover_letter_pdf(state.cover_letter, pdf_path)
                
                # S3 업로드
                s3_url = await upload_to_s3(pdf_path, os.getenv('S3_BUCKET_NAME'))
                state.s3_url = s3_url
                
                # 임시 파일 삭제
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                
                logger.info(f"자기소개서 생성 완료: user_id={state.user_id}")
                return {
                    "message": "자기소개서가 성공적으로 생성되었습니다.",
                    "cover_letter": state.cover_letter,
                    "s3_url": s3_url,
                    "state": state
                }
            except Exception as e:
                logger.error(f"PDF 생성 또는 S3 업로드 중 오류 발생: {str(e)}")
                # PDF/S3 실패해도 자기소개서 텍스트는 반환
                return {
                    "message": "자기소개서가 생성되었으나 PDF 변환에 실패했습니다.",
                    "cover_letter": state.cover_letter,
                    "state": state
                }
        else:
            return {"message": "이미 자기소개서가 생성되었습니다.", "state": state}
    except Exception as e:
        logger.error(f"자기소개서 생성 중 오류 발생: {str(e)}")
        return {"message": "자기소개서 생성 중 오류가 발생했습니다.", "error": str(e), "state": state}

async def generate_cover_letter(
    job_keywords: str,
    experience: str,
    motivation: str,
    model_name: str = "gpt-4-turbo-preview",
    timeout: int = 60
) -> str:
    """자기소개서 생성"""
    try:
        # LLM 클라이언트 초기화
        llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
            timeout=timeout,
            api_key=os.getenv("HIGH_PERFORMANCE_OPENAI_API_KEY")
        )
        
        prompt = f"""
        다음 정보를 바탕으로 자기소개서를 작성해주세요.
        
        지원 직무: {job_keywords}
        경력 사항: {experience}
        지원 동기: {motivation}
        
        다음 형식으로 작성해주세요:
        1. 성장 과정 및 가치관
        2. 지원 동기 및 포부
        3. 역량 및 경험
        4. 입사 후 계획
        
        각 섹션은 2-3문단으로 구성하고, 구체적인 예시와 성과를 포함해주세요.
        """
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        if not response or not response.content:
            logger.error("자기소개서 생성 실패: 응답이 비어있습니다.")
            return None
            
        return response.content
        
    except Exception as e:
        logger.error(f"자기소개서 생성 중 오류 발생: {str(e)}")
        return None

async def generate_pdf(cover_letter: str, user_id: str) -> Optional[Tuple[str, str]]:
    """PDF 생성 및 S3 업로드"""
    try:
        if not cover_letter:
            logger.error("PDF 생성 실패: 자기소개서 내용이 비어있습니다.")
            return None
            
        # PDF 생성
        pdf_path = f"temp/{user_id}_cover_letter.pdf"
        os.makedirs("temp", exist_ok=True)
        
        doc = Document()
        doc.add_heading('자기소개서', 0)
        
        # 내용 추가
        for line in cover_letter.split('\n'):
            if line.strip():
                doc.add_paragraph(line)
        
        # PDF 저장
        doc.save(pdf_path)
        
        # S3 업로드
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
                region_name=os.getenv('S3_REGION', 'ap-northeast-2')
            )
            
            bucket_name = os.getenv('S3_BUCKET_NAME')
            if not bucket_name:
                logger.error("AWS_BUCKET_NAME 환경 변수가 설정되지 않았습니다.")
                return None
                
            s3_key = f"cover_letters/{user_id}/{os.path.basename(pdf_path)}"
            s3_client.upload_file(pdf_path, bucket_name, s3_key)
            
            # S3 URL 생성
            s3_url = f"https://{bucket_name}.s3.{os.getenv('S3_REGION', 'ap-northeast-2')}.amazonaws.com/{s3_key}"
            
            # 임시 파일 삭제
            os.remove(pdf_path)
            
            return pdf_path, s3_url
            
        except Exception as e:
            logger.error(f"S3 업로드 중 오류 발생: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"PDF 생성 중 오류 발생: {str(e)}")
        return None

# 테스트를 위한 더미 데이터 data
TEST_DATA = {
    "job_keywords": "소프트웨어 엔지니어 (백엔드)",
    "experience": "2020-2023 네이버에서 검색 엔진 개발 및 최적화 프로젝트를 주도했습니다. Java와 Spring Boot를 사용하여 마이크로서비스 아키텍처를 설계하고 구현했으며, 시스템 성능을 40% 개선했습니다.",
    "motivation": "대규모 트래픽을 처리하는 안정적인 백엔드 시스템을 구축하는 것에 큰 관심이 있습니다. 귀사의 혁신적인 기술 스택과 도전적인 프로젝트에 참여하여 기술적 성장을 이루고 싶습니다."
}

async def test_cover_letter_generation():
    """자기소개서 생성 테스트"""
    try:
        # 1. 대화 상태 초기화
        state = await start_cover_letter_conversation("test_user")
        
        # 2. 직무 정보 입력
        response = await process_cover_letter_response(state, TEST_DATA["job_keywords"])
        print(f"[직무 정보 응답] {response['message']}")
        
        # 3. 경험 정보 입력
        response = await process_cover_letter_response(state, TEST_DATA["experience"])
        print(f"[경험 정보 응답] {response['message']}")
        
        # 4. 지원 동기 입력 및 자기소개서 생성
        response = await process_cover_letter_response(state, TEST_DATA["motivation"])
        print(f"[자기소개서 생성 완료]")
        if 's3_url' in response:
            print(f"S3 URL: {response['s3_url']}")
        else:
            print("S3 URL이 반환되지 않았습니다.")
        
        return response
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cover_letter_generation())





