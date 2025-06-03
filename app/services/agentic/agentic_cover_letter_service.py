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
from app.core.llm_client import get_llm_client,get_langchain_llm
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
from app.services.common.user_information import User_Api

class CategoryOutput(BaseModel):
    tag: str
    want: str

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
        self.user_information_data = User_Api()

    async def save_user_data(self, uid: str, state: str, query: str, intend:str):
        await self.user_information.store_user_data(uid, query, state,intend)

    async def ask_job_category(self, query: str):
        logger.info("[서치 태그 만드는중...]")

        llm = get_langchain_llm(is_lightweight=False)

        parser = JsonOutputParser(pydantic_object=CategoryOutput)
    
        system_prompt=f"""
        [ROLE]  
        You are an AI that analyzes user input and determines whether a specific job role is mentioned, in order to create appropriate tags.

        [INSTRUCTION]  
        1. Analyze the user's input to understand their intent.  
        2. If a specific job (e.g., developer, designer, marketer) is explicitly mentioned, return:  
        - "tag": "yes"  
        - "want": "< ex_ Developer cover-letter >"  
        3. If the job is not mentioned or unclear, return:  
        - "tag": "no"  
        - "want": "None"  
        4. If it's ambiguous but likely a job-related request, return your best guess (e.g., "want": "Developer cover-letter").  
        5. Your output must follow the format below and include no extra text or explanation.

        [FORMAT]  
        "tag": "yes" | "no",
        "want": "<string or 'None'>"
        

        [EXAMPLES]  

        "input": Please write a developer cover-letter.  
        "output":  
            "tag": "yes",
            "want": "Developer cover-letter"
        

        "input": Please write a personal statement.  
        "output":  
            "tag": "no",
            "want": "None"
            

        "input": Can you help me prepare something for a design job?  
        "output":  
            "tag": "yes",
            "want": "Designer cover-letter"
            
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt ),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            
            return result

        description = query

        response = parse_product(description)
        print("[response] :",response)

        return response

    async def first_query(self, query, uid, token, state, source_lang,intend):
        logger.info("[자소서 first_query 함수 실행중...]")
        logger.info(f"[처음 state 상태] : {state}")
        
        if state == "initial":
            state = "growth"
        logger.info(f"[initial 처리후 state 상태] : {state}")

        if state == "growth":
            logger.info("[질문 만드는중...]")
            
            # user_data 없애기
            user_data = await self.user_information.delete_user_data(uid)
            
            state = "motivation"
            return {
                "response": "성장 과정 및 가치관에 대해 말씀해 주세요.",
                "metadata": {"source": "default","state":state},
                "state": state,
                "url": None
            }
        
        elif state == "motivation":

            # back_user_data 가져오기
            user_data = await self.user_information_data.user_api(token)
            user_name = user_data['name']
            # user_data 가져오기
            user_data = await self.user_information.all(uid)

            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f"""
                                                    [USER_DATA]
                                                    {user_data}

                                                    [ROLE]
                                                    You are an AI that writes a paragraph about the user's growth process and core values for a self-introduction letter.

                                                    [INSTRUCTION]
                                                    1. Write in Korean.
                                                    2. Use a polite and formal tone suitable for a self-introduction letter.
                                                    3. Expand the content in a natural and coherent manner.
                                                    4. Do not include any introductions like "Sure!" or "Here is your answer".
                                                    5. The response should be exactly 5 well-structured sentences.
                                                    6. The content must be relevant for the following purpose: {intend}.
                                                    7. Avoid repetition and keep the style natural and human-like.

                                                    [QUERY]
                                                    {query}
                                                    """)
            state = "growth"
            await self.save_user_data(uid, state, response_query,intend)
            
            state = "experience"
            return {
                "response": "지원 동기 및 포부에 대해 말씀해 주세요.",
                "metadata": {"source": "default","state":state},
                "state": state,
                "url": None
            }
        
        elif state == "experience":

            # back_user_data 가져오기
            user_data = await self.user_information_data.user_api(token)
            user_name = user_data['name']
            # user_data 가져오기
            user_data = await self.user_information.all(uid)

            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f"""
                                                    [USER_DATA]
                                                    {user_data}

                                                    [ROLE]
                                                    You are an AI that writes a paragraph about the user's motivation and aspirations for applying to a particular opportunity.

                                                    [INSTRUCTION]
                                                    1. Write in Korean.  
                                                    2. Use a polite and respectful tone appropriate for a self-introduction letter.  
                                                    3. Expand the content slightly in a natural and coherent manner.  
                                                    4. Do not include any introductions like "Sure" or "Here is your answer." Start directly with the response.  
                                                    5. The response must consist of exactly 4 well-structured sentences.  
                                                    6. Ensure the format and content are appropriate for the following purpose: {intend}.

                                                    [QUERY]
                                                    {query}
                                                    """)
            state = "motivation"
            await self.save_user_data(uid, state, response_query,intend)
            
            logger.info("[질문 만드는중...]")
            state = "plan"
            return {
                "response": "역량 및 경험에 대해 말씀해 주세요.",
                "metadata": {"source": "default","state":state},
                "state": state,
                "url": None
            }
        
        elif state == "plan":
            # back_user_data 가져오기
            user_data = await self.user_information_data.user_api(token)
            user_name = user_data['name']
            # user_data 가져오기
            user_data = await self.user_information.all(uid)

            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f"""
                                                    [USER_DATA]
                                                    {user_data}

                                                    [ROLE]
                                                    You are an AI that writes a paragraph about the user's capabilities and past experiences for a self-introduction letter.

                                                    [INSTRUCTION]
                                                    1. Write in Korean.  
                                                    2. Use a polite and respectful tone appropriate for a self-introduction letter.  
                                                    3. Expand the content naturally and coherently.  
                                                    4. Do not include any introductions like "Sure" or "Here is your answer." Start directly with the response.  
                                                    5. The response must consist of exactly 5 well-structured sentences.  
                                                    6. Ensure the format and content are suitable for the following purpose: {intend}.

                                                    [QUERY]
                                                    {query}
                                                    """
                                                    )
            state = "experience"
            await self.save_user_data(uid, state, response_query,intend)
            
            logger.info("[질문 만드는중...]")
            state = "complete_letter"
            return {
                "response": "입사 후 계획에대해 말해주세요.",
                "metadata": {"source": "default","state":state},
                "state": state,
                "url": None
            }
        
        
        
        elif state == "complete_letter":
            # back_user_data 가져오기
            user_data = await self.user_information_data.user_api(token)
            user_name = user_data['name']
            # user_data 가져오기
            user_data = await self.user_information.all(uid)

            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f"""
                                                    [USER_DATA]
                                                    {user_data}

                                                    [ROLE]
                                                    You are an AI that writes a paragraph about the user's goals and plans after joining the company for a self-introduction letter.

                                                    [INSTRUCTION]
                                                    1. Write in Korean.  
                                                    2. Use a polite and respectful tone appropriate for a self-introduction letter.  
                                                    3. Expand the content naturally and coherently.  
                                                    4. Do not include any introductions like "Sure" or "Here is your answer." Start directly with the response.  
                                                    5. The response must consist of exactly 5 well-structured sentences.  
                                                    6. Ensure the format and content are suitable for the following purpose: {intend}.

                                                    [QUERY]
                                                    {query}
                                                    """
                                                    )
            state = "plan"
            await self.save_user_data(uid, state, response_query,intend)
            
            state = "cover_letter_state"
            # back_user_data 가져오기
            user_data = await self.user_information_data.user_api(token)
            user_name = user_data['name']
            # user_data 가져오기
            user_data = await self.user_information.all(uid)
            # cover_letter 텍스트 조합
            cover_letter = ""
            cover_letter += f"[1. 성장 과정 및 가치관]\n{user_data.get('growth', '')}\n\n"
            cover_letter += f"[2. 지원 동기 및 포부]\n{user_data.get('motivation', '')}\n\n"
            cover_letter += f"[3. 역량 및 경험]\n{user_data.get('experience', '')}\n\n"
            cover_letter += f"[4. 입사 후 계획]\n{user_data.get('plan', '')}\n\n"
            # HTML 생성
            html = self.user_pdf.pdf_html_form(cover_letter,user_name)
            # PDF 변환
            pdf_path = await self.user_pdf.make_pdf(uid, html)
            # S3 업로드
            url = await self.user_s3.upload_pdf(pdf_path)

            # user_data 없애기
            user_data = await self.user_information.delete_user_data(uid)

            await self.user_pdf.delete_pdf(uid)
            return {
                "response": "자소서 작성 완료.",
                "metadata": {"source": "default","state":state},
                "state": state,
                "url": url
            }
        
        else:
            logger.warning(f"[first_query] 알 수 없는 state: {state}")
            return {
                "response": " 알 수 없는 state",
                "metadata": {"source": "default","state":state},
                "state": state,
                "url": None
            }

# 1. 대화 시작 시 빈 상태 객체를 초기화해줍니다.
async def start_cover_letter_conversation(user_id: str) -> CoverLetterConversationState:
    """자기소개서 생성 대화 시작"""
    
    state = CoverLetterConversationState(
        user_id=user_id,
        current_step="start"
    )
    logger.info(f"자기소개서 대화 시작: user_id={user_id}")
    return staticmethod

# 2. 상태 업데이트.
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

#3. 자기소개서 생성
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

