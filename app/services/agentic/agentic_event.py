from googleapiclient.discovery import build
from dotenv import load_dotenv
from loguru import logger
from app.core.llm_client import get_llm_client,get_langchain_llm
from app.services.common.user_information import User_Api
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.services.common.search_location import search_location
import json
import os

class EVENT():
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_EVENT_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_EVENT_ENGINE_ID")
        self.llm = get_llm_client()
        self.user_information = User_Api()
        self.search_live_location = search_location()


    async def google_search(self, query,source_lang,token,live_location):
        logger.info("[구글 이벤트 서치중...]")

        ##########################################################
        service = build("customsearch", "v1", developerKey=self.api_key)

        logger.info(f"[live_location] : {live_location}")

        if live_location == "None" : 
            user_information = await self.user_information.user_api(token)
            if user_information.get("address") is None:
                user_information["address"] = "부산 동구"
        back_user_information = await self.user_information.user_api(token)
        back_user_prefer_information = await self.user_information.user_prefer_api(token)

        back_user_data = f"""
        {back_user_information}  
        {back_user_prefer_information}
        """

        logger.info(f"[back_user_data] : {back_user_data} ")

        user_information = self.search_live_location.search(live_location)
    
        logger.info(f"[user_information_location] : {user_information} ")

        search_user_data = f""" 
        [back_user_data] : {back_user_data}  
        [user_information_location] : {user_information} 
        """ 

        llm = get_langchain_llm(is_lightweight=True)  

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "output": {"type": "string"},
            }
        })
        prompt = ChatPromptTemplate.from_messages([
        ("system",f"""
        You are an AI that generates optimized search terms for finding local events.

        1. Analyze the user's personal and location data.
        2. Generate Korean search terms suitable for finding local events (e.g., festivals, lectures, job fairs) based on:
        - User's purpose of visit (e.g., Study → education, campus events)
        - Interests (e.g., employment → job fairs, seminars)
        - Language (Korean fluent)
        - Gender and age (optional)
        - Region (from address or current location: 서울 중구 필동로1길 30, 동국대학교)
        3. Search terms must be region-specific and relevant to the user’s life stage.
        4. Output in **JSON format** only. Do not explain.

        [format]
        "output": "..."         
        """),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            logger.info(f"[json.dumps] : {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        description = search_user_data    

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
            dateRestrict='m1'  # 최근 3주 이내의 결과로 제한
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
    




   