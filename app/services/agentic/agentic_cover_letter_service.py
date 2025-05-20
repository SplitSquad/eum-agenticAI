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
from app.services.common.user_coverletter_information import UserCoverLetterInformation
from app.services.common.user_coverletter_pdf import UserCoverLetterPDF
from app.services.common.user_coverletter_s3 import UserCoverLetterS3

class CoverLetterConversationState(BaseModel):
    """자기소개서 생성 대화 상태 관리 클래스"""
    user_id: str
    current_step: str = "start"  # start -> growth -> motivation -> experience -> plan -> complete
    growth: Optional[str] = None
    motivation: Optional[str] = None
    experience: Optional[str] = None
    plan: Optional[str] = None
    cover_letter: Optional[str] = None
    is_completed: bool = False
    pdf_path: Optional[str] = None
    s3_url: Optional[str] = None

class AgenticCoverLetter:
    def __init__(self):
        self.user_information = UserCoverLetterInformation()
        self.user_pdf = UserCoverLetterPDF()
        self.user_s3 = UserCoverLetterS3()
        self.llm = get_llm_client(is_lightweight=False)

    async def save_user_data(self, uid: str, state: str, query: str):
        await self.user_information.store_user_data(uid, query, state)

    async def first_query(self, query, uid, token, state, source_lang):
        logger.info("[자소서 first_query 함수 실행중...]")
        logger.info(f"[처음 state 상태] : {state}")
        
        if state == "initial":
            state = "growth"
        logger.info(f"[initial 처리후 state 상태] : {state}")

        if state == "growth":
            logger.info("[질문 만드는중...]")
            result = await self.llm.generate(f"<Please translate it into {source_lang}> 성장 과정 및 가치관에 대해 말씀해 주세요.")
            logger.info("[사용자에게 질문할 쿼리]", result)
            state = "motivation"
            return {
                "response": result,
                "metadata": {"source": "default"},
                "state": state,
                "url": None
            }
        
        elif state == "motivation":
            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f"<Please translate it into Korean> {query}")
            await self.save_user_data(uid, state, response_query)
            
            logger.info("[질문 만드는중...]")
            result = await self.llm.generate(f"<Please translate it into {source_lang}> 지원 동기 및 포부에 대해 말씀해 주세요.")
            logger.info("[사용자에게 질문할 쿼리]", result)
            state = "experience"
            return {
                "response": result,
                "metadata": {"source": "default"},
                "state": state,
                "url": None
            }
        
        elif state == "experience":
            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f"<Please translate it into Korean> {query}")
            await self.save_user_data(uid, state, response_query)
            
            logger.info("[질문 만드는중...]")
            result = await self.llm.generate(f"<Please translate it into {source_lang}> 역량 및 경험에 대해 말씀해 주세요.")
            logger.info("[사용자에게 질문할 쿼리]", result)
            state = "plan"
            return {
                "response": result,
                "metadata": {"source": "default"},
                "state": state,
                "url": None
            }
        
        elif state == "plan":
            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f"<Please translate it into Korean> {query}")
            await self.save_user_data(uid, state, response_query)
            
            logger.info("[질문 만드는중...]")
            result = await self.llm.generate(f"<Please translate it into {source_lang}> 입사 후 계획에 대해 말씀해 주세요.")
            logger.info("[사용자에게 질문할 쿼리]", result)
            state = "complete"
            # user_data 가져오기
            user_data = await self.user_information.all(uid)
            # cover_letter 텍스트 조합
            cover_letter = ""
            cover_letter += f"[1. 성장 과정 및 가치관]\n{user_data.get('growth', '')}\n\n"
            cover_letter += f"[2. 지원 동기 및 포부]\n{user_data.get('motivation', '')}\n\n"
            cover_letter += f"[3. 역량 및 경험]\n{user_data.get('experience', '')}\n\n"
            cover_letter += f"[4. 입사 후 계획]\n{response_query}\n\n"
            # HTML 생성
            html = self.user_pdf.pdf_html_form(cover_letter)
            # PDF 변환
            pdf_path = await self.user_pdf.make_pdf(uid, html)
            # S3 업로드
            url = await self.user_s3.upload_pdf(pdf_path)
            return {
                "response": "자기소개서가 완성되었습니다.",
                "metadata": {"source": "default"},
                "state": state,
                "url": url
            }
        
        elif state == "complete":
            logger.info("[이미 완성된 상태에서 요청]")
            return {
                "response": "이미 자기소개서가 완성되었습니다.",
                "metadata": {"source": "default"},
                "state": state,
                "url": None
            }
        
        else:
            logger.warning(f"[first_query] 알 수 없는 state: {state}")
            return {
                "response": "다시 작성해주세요.",
                "metadata": {"source": "default"},
                "state": state,
                "url": None
            }

async def start_cover_letter_conversation(user_id: str) -> CoverLetterConversationState:
    """자기소개서 생성 대화 시작"""
    
    state = CoverLetterConversationState(
        user_id=user_id,
        current_step="start"
    )
    logger.info(f"자기소개서 대화 시작: user_id={user_id}")
    return state

async def process_cover_letter_response(state: CoverLetterConversationState, response: str) -> Dict[str, Any]:
    """사용자 응답 처리 및 자기소개서 생성"""
    try:
        if state.current_step == "start":
            state.growth = response
            state.current_step = "motivation"
            return {
                "message": "지원 동기 및 포부에 대해 말씀해 주세요.",
                "state": state
            }
        elif state.current_step == "motivation":
            state.motivation = response
            state.current_step = "experience"
            return {
                "message": "역량 및 경험에 대해 말씀해 주세요.",
                "state": state
            }
        elif state.current_step == "experience":
            state.experience = response
            state.current_step = "plan"
            return {
                "message": "입사 후 계획에 대해 말씀해 주세요.",
                "state": state
            }
        elif state.current_step == "plan":
            state.plan = response
            state.current_step = "complete"
            # cover_letter 텍스트 조합
            cover_letter = ""
            cover_letter += f"[1. 성장 과정 및 가치관]\n{state.growth}\n\n"
            cover_letter += f"[2. 지원 동기 및 포부]\n{state.motivation}\n\n"
            cover_letter += f"[3. 역량 및 경험]\n{state.experience}\n\n"
            cover_letter += f"[4. 입사 후 계획]\n{state.plan}\n\n"
            state.cover_letter = cover_letter
            state.is_completed = True
            return {
                "message": "자기소개서가 성공적으로 생성되었습니다.",
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
    timeout: int = 60
) -> str:
    """자기소개서 생성"""
    try:
        # LLM 클라이언트 초기화 
        client = get_llm_client(is_lightweight=False)
        
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
        
        response = await client.generate(prompt)
        
        if not response:
            logger.error("자기소개서 생성 실패: 응답이 비어있습니다.")
            return None
            
        return response
        
    except Exception as e:
        logger.error(f"자기소개서 생성 중 오류 발생: {str(e)}")
        return None


