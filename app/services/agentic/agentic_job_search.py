from googleapiclient.discovery import build
from dotenv import load_dotenv
from loguru import logger
from app.core.llm_client import get_llm_client
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.llm_client import get_langchain_llm
from app.services.common.user_information import User_Api
from app.services.common.search_location import search_location
from pydantic import BaseModel
import json
import os

load_dotenv()  # .env 파일을 읽어서 환경변수로 등록
class CategoryOutput(BaseModel):
    input: str
    output: str

class agentic_job_search():
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_WEATHER_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.user_information=User_Api()
        self.user=""
        self.user_prefer=""
        self.user_information_data=""
        self.search_live_location = search_location()
        self.llm = get_llm_client()

    async def search_tag(self,query):
        logger.info("[서치 태그 만드는중...]")

        llm = get_langchain_llm(is_lightweight=False)

        parser = JsonOutputParser(pydantic_object=CategoryOutput)
    
        system_prompt=f"""

        [Role]  
        - You are an AI assistant that analyzes user queries related to job search.  
        - Your task is to determine whether the user has specified a clear **desired job role**.

        [Instruction]  
        1. If the user clearly mentions a **specific job title or role**, output `"yes"`.  
        2. If the user speaks only in general terms (e.g., "looking for a job" without a specific role), output `"no"`.
        3. You **must** return the result strictly in **valid JSON format** as shown below.

        [Output Format]  
        "output": "..."

        [Examples]  
        "input": "I am looking for a developer job."  
        "output": "yes"

        "input": "I am looking for a job."  
        "output": "no"

        "input": "I want to work in marketing."  
        "output": "yes"

        "input": "I need employment."  
        "output": "no"

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

        return response['output']

        

    async def first_query(self,source_lang):
        logger.info("[질문 만드는중...]")

        # LLM 클라이언트 인스턴스 가져오기
        llm_client = get_llm_client(is_lightweight=True)

        # 프롬프트 구성
        prompt = f"<Please translate it into {source_lang}> 어떤 종류의 일자리를 찾고 계신가요??"

        # 직접 호출 (클라이언트마다 방식 다를 수 있음)
        response_query = await llm_client.generate(prompt)

        return {
                "response": response_query,
                "metadata": {
                    "source": "default",
                    "state": "job_search",        # ✅ metadata 안에 포함
                    "results": "default"
                },
            "url": None
            }


    async def google_search(self, query,source_lang):
        logger.info("[구글 서치중...]")
        service = build("customsearch", "v1", developerKey=self.api_key)

        # ai가 쿼리문 다듬어줌.

        # LLM 클라이언트 인스턴스 가져오기
        llm_client = get_llm_client(is_lightweight=True)

        # 프롬프트 구성
        prompt = f"""
        Please rephrase the following job-related user input
        so that it is short and suitable for Google search,
        in Korean.

        User input: {query}
        Output:
        """

        # 직접 호출 (클라이언트마다 방식 다를 수 있음)
        response_query = await llm_client.generate(prompt)
        logger.info(f"[다듬어진 문장] : {response_query}")

        res = service.cse().list(
            q=response_query,
            cx=self.search_engine_id,
            num=5,
            dateRestrict='w3'  # 최근 3주 이내의 결과로 제한
        ).execute()


        logger.info(f"[구글 서치 출력] : {res}")

        # 결과값 다듬기.
        trimmed_results = await self.Trim(res.get("items", []))  # ✨ 여기

        return {
                    "response": trimmed_results,
                    "metadata": {
                        "source": "default",
                        "state": "job_search_state",        # ✅ metadata 안에 포함
                        "results": "default"
                    },
                "url": None
                }
    
    async def Trim(self, items: list) -> list:
        """검색 결과를 프론트엔드용으로 정제"""
        logger.info("[결과 값 다듬는중...]")
        trimmed = []
        for item in items:
            result = {
                "title": item.get("title"),
                "link": item.get("link")
            }


            trimmed.append(result)

        return trimmed



