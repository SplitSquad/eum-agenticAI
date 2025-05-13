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
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException


class CoverLetterConversationState(BaseModel):
@@ -29,6 +32,11 @@
    is_completed: bool = False


class CoverLetterRequest(BaseModel):
    """자기소개서 생성 요청 모델"""
    response: str


async def start_cover_letter_conversation(user_id: str) -> CoverLetterConversationState:
    """자기소개서 생성 대화 시작"""
    state = CoverLetterConversationState(
@@ -39,34 +47,32 @@
    return state


async def upload_to_s3(file_path: str, bucket_name: str) -> str:
async def upload_to_s3(file_path: str, object_name: str) -> str:
    """파일을 S3에 업로드하고 URL을 반환합니다."""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
            aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
            region_name=os.getenv('S3_REGION')
        )
        
        # 파일 이름 추출
        file_name = os.path.basename(file_path)
        bucket = os.getenv('S3_BUCKET_NAME')

        # S3에 업로드
        s3_client.upload_file(
            file_path,
            bucket_name,
            f"cover-letters/{file_name}",
            bucket,
            object_name,
            ExtraArgs={'ContentType': 'application/pdf'}
        )

        # URL 생성
        url = f"https://{bucket_name}.s3.amazonaws.com/cover-letters/{file_name}"
        logger.info(f"S3 업로드 완료: {url}")
        url = f"https://{bucket}.s3.{os.getenv('S3_REGION')}.amazonaws.com/{object_name}"
        logger.info(f"[upload_to_s3] 업로드 성공: {url}")

        return url
    except ClientError as e:
        logger.error(f"S3 업로드 실패: {str(e)}")
    except Exception as e:
        logger.error(f"[upload_to_s3] 업로드 실패: {str(e)}")
        raise


@@ -196,12 +202,18 @@
            # PDF 파일 생성
            await save_cover_letter_pdf(state.cover_letter, pdf_path)

            # S3 업로드
            logger.info("[upload_to_s3] 파일 업로드 시작")
            s3_url = await upload_to_s3(pdf_path, f"pdfs/cover_letters/{random_filename}")
            logger.info(f"[S3 업로드] : {s3_url}")

            logger.info(f"자기소개서 생성 완료: user_id={state.user_id}")

            return {
                "message": "자기소개서가 성공적으로 생성되었습니다.",
                "cover_letter": state.cover_letter,
                "pdf_path": pdf_path,
                "download_url": s3_url,
                "state": state
            }

@@ -244,3 +256,108 @@
        raise ValueError("AI가 자기소개서를 생성하지 못했습니다.")
    logger.info(f"AI가 생성한 자기소개서: {response.content[:200]}...")
    return response.content


async def job_cover_letter(query: str, uid: str, state: str, token: str) -> Dict[str, Any]:
    """자기소개서 생성 프로세스 처리"""
    authorization = token
    user_email = uid
    pre_state = state
    logger.info(f"[job_cover_letter parameter] : {authorization}, {user_email}, {pre_state}")

    ## 첫번째 응답 - 직무 정보 요청
    if pre_state == "first":
        logger.info("[first_response] - 직무 정보 요청")
        return {
            "response": "지원하고자 하는 직무와 필요한 기술 스택에 대해 설명해주세요.",
            "state": "second"
        }
    
    ## 두번째 응답 - 경험 정보 요청
    elif pre_state == "second":
        logger.info("[second_response] - 경험 정보 요청")
        try:
            # 대화 상태 초기화
            state = CoverLetterConversationState(user_id=user_email)
            state.job_keywords = query
            state.current_step = "experience"
            
            return {
                "response": "해당 분야에서의 구체적인 경험이나 프로젝트에 대해 말씀해 주세요. 어떤 기술을 사용했고, 어떤 성과를 이루었나요?",
                "state": "third"
            }
            
        except Exception as e:
            logger.error(f"자기소개서 생성 시작 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    
    ## 세번째 응답 - 지원 동기 요청
    elif pre_state == "third":
        logger.info("[third_response] - 지원 동기 요청")
        try:
            state = CoverLetterConversationState(user_id=user_email)
            state.experience = query
            state.current_step = "motivation"
            
            return {
                "response": "이 직무를 선택하게 된 동기와 앞으로의 목표에 대해 말씀해 주세요.",
                "state": "fourth"
            }
            
        except Exception as e:
            logger.error(f"경험 정보 처리 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    
    ## 네번째 응답 - 자기소개서 생성 및 S3 업로드
    elif pre_state == "fourth":
        logger.info("[fourth_response] - 자기소개서 생성 및 S3 업로드")
        try:
            state = CoverLetterConversationState(user_id=user_email)
            state.motivation = query
            
            # 자기소개서 생성
            logger.info("[AI가 자기소개서 생성 중...]")
            cover_letter = await generate_cover_letter(
                state.job_keywords,
                state.experience,
                state.motivation
            )
            
            # PDF 생성
            output_dir = os.path.join(os.getcwd(), "app/services/agentic/cover_letter")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "cover_letter.pdf")
            
            # PDF 저장
            await save_cover_letter_pdf(cover_letter, output_path)
            
            # S3 업로드
            logger.info("[upload_to_s3] 파일 업로드 시작")
            s3_url = await upload_to_s3(output_path, "pdfs/cover_letter.pdf")
            logger.info(f"[S3 업로드] : {s3_url}")
            
            return {
                "response": "자기소개서가 생성되었습니다.",
                "state": "first",
                "message": "PDF가 업로드되었습니다.",
                "download_url": s3_url
            }
            
        except Exception as e:
            logger.error(f"자기소개서 생성 실패: {str(e)}")
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