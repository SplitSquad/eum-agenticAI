from dotenv import load_dotenv
load_dotenv()  # .env 파일 자동 로딩
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Optional, List, Any
from app.core.llm_client import get_llm_client
from loguru import logger
from pydantic import BaseModel
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime
import tempfile
import os
import uuid
from playwright.async_api import async_playwright
from langchain_openai import ChatOpenAI  # Ollama 대신 OpenAI import
import re


class CoverLetterConversationState(BaseModel):
    """자기소개서 생성 대화 상태 관리 클래스"""
    user_id: str
    current_step: str = "start"  # start -> job_info -> experience -> motivation -> completion
    job_keywords: Optional[str] = None
    experience: Optional[str] = None
    motivation: Optional[str] = None
    cover_letter: Optional[str] = None
    is_completed: bool = False


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
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
        )
        
        # 파일 이름 추출
        file_name = os.path.basename(file_path)
        
        # S3에 업로드
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
        logger.error(f"S3 업로드 실패: {str(e)}")
        raise


async def save_cover_letter_pdf(cover_letter: str, output_path: str) -> str:
    """자기소개서를 PDF로 저장"""
    try:
        # HTML 템플릿 생성
        html_content = generate_cover_letter_html(cover_letter)
        
        # PDF 생성
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # HTML 콘텐츠 로드
            await page.set_content(html_content)
            
            # PDF로 저장
            await page.pdf(path=output_path, format='A4')
            await browser.close()
            
        return output_path
    except Exception as e:
        logger.error(f"PDF 저장 중 오류 발생: {str(e)}")
        raise


def split_cover_letter_sections(cover_letter: str):
    """AI가 생성한 자기소개서를 4개 항목으로 분리 (정확한 번호와 제목 기준)"""
    # 각 항목의 제목을 명확히 기준으로 분리
    pattern = r"1\. 성장 과정 및 가치관[\s\S]*?2\. 지원 동기 및 포부|2\. 지원 동기 및 포부[\s\S]*?3\. 역량 및 경험|3\. 역량 및 경험[\s\S]*?4\. 입사 후 계획|4\. 입사 후 계획[\s\S]*"
    matches = re.findall(r"1\. 성장 과정 및 가치관([\s\S]*?)2\. 지원 동기 및 포부([\s\S]*?)3\. 역량 및 경험([\s\S]*?)4\. 입사 후 계획([\s\S]*)", cover_letter)
    if matches and len(matches[0]) == 4:
        return tuple(s.strip() for s in matches[0])
    # fallback: cover_letter 전체를 첫 항목에 넣고 나머지는 빈칸
    return cover_letter, '', '', ''


def generate_cover_letter_html(cover_letter: str) -> str:
    """자기소개서 HTML 생성 (4개 항목 박스, 프롬프트와 동일한 제목)"""
    growth, motivation, experience, plan = split_cover_letter_sections(cover_letter)
    html = f"""
    <!DOCTYPE html>
    <html lang=\"ko\">
    <head>
        <meta charset=\"UTF-8\">
        <style>
            @page {{ size: A4; margin: 0; }}
            body {{ font-family: 'Batang', serif; margin: 0; padding: 0; line-height: 1.5; }}
            .page {{ width: 210mm; height: 297mm; padding: 15mm 20mm; box-sizing: border-box; }}
            .cover-letter-title {{ font-size: 28px; font-weight: bold; margin-bottom: 40px; text-align: center; letter-spacing: 10px; }}
            .section {{ border: 2px solid #000; margin-bottom: 30px; padding: 18px 20px; border-radius: 6px; }}
            .section-title {{ font-weight: bold; font-size: 16px; margin-bottom: 10px; }}
            .section-content {{ white-space: pre-wrap; font-size: 13px; }}
            .footer {{ margin-top: 60px; text-align: center; font-size: 12px; }}
            .date-line {{ margin: 30px 0; line-height: 2; }}
        </style>
    </head>
    <body>
        <div class=\"page\">
            <div class=\"cover-letter-title\">자기소개서</div>
            <div class=\"section\">
                <div class=\"section-title\">1. 성장 과정 및 가치관</div>
                <div class=\"section-content\">{growth}</div>
            </div>
            <div class=\"section\">
                <div class=\"section-title\">2. 지원 동기 및 포부</div>
                <div class=\"section-content\">{motivation}</div>
            </div>
            <div class=\"section\">
                <div class=\"section-title\">3. 역량 및 경험</div>
                <div class=\"section-content\">{experience}</div>
            </div>
            <div class=\"section\">
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
            state.is_completed = True
            state.current_step = "completed"

            # 랜덤 파일 이름 생성
            random_filename = f"{uuid.uuid4()}.pdf"
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, random_filename)
            
            # PDF 파일 생성
            await save_cover_letter_pdf(state.cover_letter, pdf_path)

            logger.info(f"자기소개서 생성 완료: user_id={state.user_id}")

            return {
                "message": "자기소개서가 성공적으로 생성되었습니다.",
                "cover_letter": state.cover_letter,
                "pdf_path": pdf_path,
                "state": state
            }

        else:
            return {"message": "이미 자기소개서가 생성되었습니다.", "state": state}

    except Exception as e:
        logger.error(f"자기소개서 생성 중 오류 발생: {str(e)}")
        return {"message": "자기소개서 생성 중 오류가 발생했습니다.", "error": str(e), "state": state}


async def generate_cover_letter(job_keywords: str, experience: str, motivation: str) -> str:
    prompt = f"""
    다음 정보를 바탕으로 전문적인 자기소개서를 작성해주세요. 아래의 네 개 항목 제목과 번호를 반드시 포함하여 구분해 주세요.

    지원 분야: {job_keywords}
    경험 및 프로젝트: {experience}
    지원 동기 및 목표: {motivation}

    아래의 형식을 따라 자기소개서를 작성해주세요. 각 항목은 반드시 해당 제목과 번호로 시작해야 합니다:

    1. 성장 과정 및 가치관\n(내용)
    2. 지원 동기 및 포부\n(내용)
    3. 역량 및 경험\n(내용)
    4. 입사 후 계획\n(내용)

    전체 자기소개서는 1,000자 내외로 작성해 주세요.
    각 항목은 명확하고 설득력 있게 작성해야 합니다.
    """
    # Ollama 대신 OpenAI 사용
    llm_client = ChatOpenAI(
        api_key=os.getenv("HIGH_PERFORMANCE_OPENAI_API_KEY"),
        model_name=os.getenv("HIGH_PERFORMANCE_OPENAI_MODEL"),
        timeout=int(os.getenv("HIGH_PERFORMANCE_OPENAI_TIMEOUT"))
    )
    response = await llm_client.ainvoke([
        HumanMessage(content=prompt)
    ])
    if not response:
        raise ValueError("AI가 자기소개서를 생성하지 못했습니다.")
    logger.info(f"AI가 생성한 자기소개서: {response.content[:200]}...")
    return response.content
