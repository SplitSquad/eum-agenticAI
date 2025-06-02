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
        self.user_information_data = ""
        self.search_live_location = search_location()


    async def google_search(self, query,source_lang,token,live_location):
        logger.info("[구글 이벤트 서치중...]")

        ##########################################################
        service = build("customsearch", "v1", developerKey=self.api_key)

        
        # 유저 위치 정보 수집
        logger.info("[유저 위치 정보 수집...]")
        logger.info(f"[live_location] : {live_location}")
        if live_location is None or not (getattr(live_location, "latitude", None) and getattr(live_location, "longitude", None)):
            logger.warning("[WARNING] live_location이 유효하지 않아 fallback 주소 사용")
            self.user_information_data = await self.user_information.user_api(token)
            if not self.user_information_data.get("address"):
                self.user_information_data["address"] = "부산 동구"
        else:
            self.user_information_data = self.search_live_location.search(live_location)

        self.user_information_data = self.search_live_location.search(live_location)
        logger.info(f"[user_information_location] : {self.user_information_data} ")

        
        # 유저 정보 수집
        logger.info("[유저 정보 수집...]")
        back_user_information = await self.user_information.user_api(token)
        back_user_prefer_information = await self.user_information.user_prefer_api(token)

        back_user_data = f"""
        {back_user_information}  
        {back_user_prefer_information}
        """

        logger.info(f"[back_user_data] : {back_user_data} ")


        search_user_data = f""" 
        [back_user_data] : {back_user_data}  
        [user_information_location] : {self.user_information_data} 
        """ 
        logger.info(f"[search_user_data] : {search_user_data} ")

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
        [ Role ]
        You are an AI that generates optimized search terms for finding local events.

        [ instruction ] 
        1. Analyze the user's structured data including:
        - Personal info: age, gender, language, nationality
        - Onboarding preferences: visitPurpose, interests, travelData
        - Real-time location (or default address): road_address.region_1depth_name, region_2depth_name, region_3depth_name
       
        2. Based on the analysis, generate Korean search terms that help the user discover **region-specific events** such as festivals, exhibitions, seminars, or local gatherings.
        
        3. The search query must:
        - Reflect the user's purpose (e.g., Travel → 관광지 축제, 지역 전시회)
        - Use the user's interests (e.g., finance_tax → 세금 교육, 재무 세미나)
        - Be region-aware (e.g., 서울 중구 → "서울 중구 행사", "중구 지역 축제")
        - Be appropriate for user’s life stage (e.g., 20s traveler → 체험형 행사, 트렌디한 장소)
        
        4. If user location is not provided, use `default_location` as a fallback.
        
        5. Output the final search term in **JSON format** only. Do not explain.

        [ format - JSON ] 
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
        logger.info(f"[response] {response}")
        
        # ✅ 문자열로 반환된 경우 강제로 딕셔너리로 변환
        if isinstance(response, str):
            logger.warning("[WARNING] response가 문자열입니다. 딕셔너리 형태로 변환합니다.")
            response = {"output": response}

        # ✅ output 키가 없을 경우 기본값 설정
        if 'output' not in response:
            logger.info(f"[예외처리중... 기본값 서울행사]")
            response['output'] = "서울행사"

        logger.info(response['output'])  # ✅ OK
        response = response["output"]    # ✅ str

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
    




   