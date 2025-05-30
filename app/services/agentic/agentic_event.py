from googleapiclient.discovery import build
from dotenv import load_dotenv
from loguru import logger
from app.core.llm_client import get_llm_client,get_langchain_llm
from app.services.common.user_information import User_Api
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json
import os

class EVENT():
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_EVENT_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_EVENT_ENGINE_ID")
        self.llm = get_llm_client()
        self.user_information = User_Api()


    async def google_search(self, query,source_lang,token,location):
        logger.info("[구글 이벤트 서치중...]")

        ##########################################################
        service = build("customsearch", "v1", developerKey=self.api_key)


        user_information = await self.user_information.user_api(token,location)
        if user_information.get("address") is None:
            user_information["address"] = "부산 동구"
    
        logger.info( f"[user_information[address] ] : {user_information['address']}")

        llm = get_langchain_llm(is_lightweight=False)  # 고성능 모델 사용

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "output": {"type": "string"},
            }
        })
        prompt = ChatPromptTemplate.from_messages([
        ("system",f"""
        1. This is an AI that searches for events around the user.
        2. Please check the user's location carefully.
        3. return json
        default. please return Korean
         
        [format]
        "output" : "..."
         
        [one-shot-example]
        input : 
            query : <user_input> + user_location : <user_location> 
        output :
            <user_location> 행사
        """),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            logger.info(f"[json.dumps] : {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        description = f" query : {query} + user_location : {user_information['address']} "    

        response = parse_product(description)
        
        logger.info(f"[lang_chain] : {response['output']}")
        logger.info(f"[lang_chain_type] : {type(response)}")

        response = response["output"]

        ##########################################################

        
        service = build("customsearch", "v1", developerKey=self.api_key)

    
        res = service.cse().list(
            q=response,
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
                        "state": "event_state",        # ✅ metadata 안에 포함
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
    




   