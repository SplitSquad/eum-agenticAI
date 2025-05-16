from typing import Dict, Any
from loguru import logger
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json
import re
import requests
import os
from dotenv import load_dotenv
from app.core.llm_post_prompt import Prompt
# 기존: from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from app.core.llm_client import get_langchain_llm

load_dotenv()  # .env 파일 자동 로딩

# 환경변수에서 API URL 가져오기
COMMUNITY_API_URL = os.getenv("COMMUNITY_API_URL", "https://api.eum-friends.com/community/post")
if not COMMUNITY_API_URL:
    raise ValueError("COMMUNITY_API_URL 환경변수가 설정되지 않았습니다.")

class AgenticPost:
    def __init__(self):
        logger.info("[게시글 에이전트 초기화]")
        
    # 단계에 맞는 함수 생성
    async def first_query(self, token , query) : 

        logger.info("[카테고리 반환 단계]")
        logger.info(f"[user token]: {token}")
        logger.info(f"[user query]: {query}")

        llm = get_langchain_llm(is_lightweight = False)

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "category": {"type":"string"},
                "postType": {"type":"string"}
            }
        })

        system_prompt = Prompt.post_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            logger.info(f"[AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        #### tmp keyword 추가
        keyword = query
        description = keyword

        response = parse_product(description)

        return response
    #####################################################################


    #####################################################################
    async def second_query(self, token, query, title, tags) : 
        logger.info("[게시판 생성 단계]")
        category = title
        llm = get_langchain_llm(is_lightweight=False)
        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "category" : {"type" : "string"},
                "language": { "type": "string"},
                "tags" : {"type": "string"},
                "postType":{ "type": "string"},
                "address":{ "type": "string"}
            }
        })
        system_prompt = Prompt.post_creation_form()
        
        prompt=system_prompt

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            logger.info(f"[게시판 생성 AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        description = f"{query}, category: {category}, tags: {tags}"

        response = parse_product(description)
        response = response["post"]
        response = json.dumps(response, indent=2, ensure_ascii=False)
        logger.info(f"[response 반환값] : {response}")

        post_api(response, token)
        
        return response
    #####################################################################

##################################################################### 게시판 api 요청

def post_api(form_data: str, token: str):
    headers = {
        "Authorization": token
    }

    files = {
        "post": (None, form_data, "application/json")
    }

    logger.info(f"[headers] : {headers}")
    logger.info(f"[files] : {files}")

    try:
        response = requests.post(
            url=f"{COMMUNITY_API_URL}",
            headers=headers,
            files=files
        )

        print("Status Code:", response.status_code)
        print("Response:", response.text)

    except Exception as e:
        logger.error(f"게시글 API 호출 중 오류 발생: {str(e)}")
        return "응답 생성 중 오류 발생"
    
    return response

##################################################################### 게시판 api 요청