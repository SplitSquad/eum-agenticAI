import json
import requests
import aiohttp
from geopy.geocoders import Nominatim
from loguru import logger
from app.core.llm_client import get_langchain_llm,get_llm_client
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import ChatPromptTemplate
from app.services.common.user_information import User_Api
import os
from pydantic import BaseModel

class CategoryOutput(BaseModel):
    input: str
    output: str

# ✅ API 기본 설정
url = os.getenv("MAPS_API_URL","https://dapi.kakao.com/v2/local/search/category.json")

class foodstore():
    
    def __init__(self):
        self.user_api=User_Api()
        self.user = ""
        self.user_prefer = ""
        self.url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        self.headers = {
            "Authorization": "KakaoAK 5d96c7a6ef9ac4662396eafc9c44f63e"
        }

    async def load_user_data(self, token: str):
        # ✅ user_api는 비동기이므로 await로 호출
        logger.info("[사용자 정보 불러오는중...]")
        self.user = await self.user_api.user_api(token)
        self.user_prefer = await self.user_api.user_prefer_api(token)
        logger.info(f"[사용자 정보]: {self.user} | {self.user_prefer}")

    async def query_analyze(self,query):
        
        logger.info("[query_analyze...]")

        llm = get_langchain_llm(is_lightweight=False)  # 고성능 모델 사용

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "output": {"type": "string"},
            }
        })

        # 프롬프트 문자열 구성
        system_prompt_template = f"""
        [Role]
        You are an AI that analyzes user input and determines the user's search intention related to location.

        [Format]
        "intention": "...",
        "tag": "Find" | "None"
    
        [Instructions]
        1. Check if the user is asking about a specific place or type of location (e.g., a restaurant, hospital, subway station).
        2. If the user clearly mentions a specific place or category they are looking for, set `"tag"` to `"Find"`.
        3. If the user is asking vaguely or only mentions "nearby" without a clear place or category, set `"tag"` to `"None"`.
        4. Always respond in JSON format.

        [Examples]
        "Input": "Find a icecream store near me"
        "output": 
            "intention": "아이스크림",
            "tag": "Find"

        "Input": "Find a starbucks near me"
        "output": 
            "intention": "스타벅스",
            "tag": "Find"

        "Input": "Find a Jockbal restaurant near me"
        "output": 
            "intention": "족발",
            "tag": "Find"

        "Input": "Find nearby amenities"
        "output": 
            "intention": "기념품점",
            "tag": "None"

        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_template ),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            
            return result

        description = query

        response = parse_product(description)
        # 예외 처리: 누락된 키에 기본값 설정
        if 'intention' not in response or not response['intention']:
            response['intention'] = "기념품점"
        if 'tag' not in response or response['tag'] not in ["Find", "None"]:
            response['tag'] = "None"


        print("[response] :",response)

        return response

    async def category_query(self,source_lang):
        logger.info("[질문 만드는중...]")

        # LLM 클라이언트 인스턴스 가져오기
        llm_client = get_llm_client(is_lightweight=True)

        # 프롬프트 구성
        prompt = f"<Please translate it into {source_lang}> 어떤 장소를 찾고 계신가요?? 1.대형마트 2.편의점 3.음식점 4.카페 5.관광명소 6.숙박 7.주유소,충전소 8.주차장 9.지하철역 10.학교 11.학원 12.병원 13.약국 14.중개업소 15.공공기관"

        # 직접 호출 (클라이언트마다 방식 다를 수 있음)
        response_query = await llm_client.generate(prompt)

        return response_query
    
    async def Category_extraction(self,query):
        logger.info("[카테고리 추출 하는중 만드는중...]")

       
        llm = get_langchain_llm(is_lightweight=False)

        parser = JsonOutputParser(pydantic_object=CategoryOutput)
       

        system_prompt=f"""
        1. Choose **exactly one** category code that best matches the input.
        2. You **must** choose one — do not skip or leave it blank.
        3. You must choose **from the following list only**:
        MT1, CS2, FD6, CE7, AT4, AD5, OL7, PK6, SW8, SC4, AC5, HP8, PM9, AG2, PO3
        4. Your response must be **strictly in JSON format**.
        5. Do **not** include any extra text, comments, or explanations. Return **only** the JSON.

        [Format]
        "output" : "<CATEGORY_CODE>"
        
        [few-shot]
        input : 대형마트 
        output : MT1

        input : 편의점 
        output : CS2

        input : 음식점 
        output : FD6

        input : 카페 
        output : CE7

        input : 관광명소 
        output : AT4

        input : 숙박 
        output : AD5

        input : 주유소, 충전소 
        output : OL7

        input : 주차장
        output : PK6

        input : 지하철역 
        output : SW8

        input : 학교 
        output : SC4

        input : 학원
        output : AC5

        input : 병원
        output : HP8

        input : 약국
        output : PM9

        input : 중개업소
        output : AG2

        input : 공공기관
        output : PO3
 
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt ),
            ("user", "{input}")
        ])


        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            print(f"[Category] : {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        response = parse_product(query)
        # 예외처리
        # 예외 처리: 'output' 키가 없거나 유효하지 않은 값일 경우 기본값 설정
        valid_codes = {
            "MT1", "CS2", "FD6", "CE7", "AT4", "AD5",
            "OL7", "PK6", "SW8", "SC4", "AC5", "HP8",
            "PM9", "AG2", "PO3"
        }

        if 'output' not in response or response['output'] not in valid_codes:
            response['output'] = "MT1"  # 기본값 (예: 대형마트)
    
        return response
    
    async def location(self):
        logger.info("[사용자 위치 조회중...]")
        
        try:
            # ✅ 사용자 주소 조회
            user_address = self.user['address']
            
            if not user_address:
                logger.warning("[사용자 주소 없음] 기본 주소 사용")
                user_address = "서울 강남"
                self.user['address'] = user_address
            
            ## 실제 이메일 사용해야함!
            geolocator = Nominatim(user_agent="jwontiger@gmail.com")
            location = geolocator.geocode(user_address)
            
            if location is None:
                logger.warning(f"[위치 조회 실패] 주소 '{user_address}'에 대한 위치 정보를 찾을 수 없음. 기본 주소 사용")
                user_address = "서울 강남"
                location = geolocator.geocode(user_address)
            
            logger.info(f"[위치 조회 성공] 위도: {location.latitude}, 경도: {location.longitude}")
            return {
                "latitude": location.latitude,
                "longitude": location.longitude
            }
            
        except Exception as e:
            logger.error(f"[위치 조회 오류] {str(e)}. 기본 주소 사용")
            # 기본 주소로 재시도
            try:
                user_address = "서울 강남"
                geolocator = Nominatim(user_agent="jwontiger@gmail.com")
                location = geolocator.geocode(user_address)
                
                return {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                }
            except Exception as e:
                logger.error(f"[기본 주소 조회 실패] {str(e)}")
                # 강남역 좌표 하드코딩 (최후의 수단)
                return {
                    "latitude": 37.498095,
                    "longitude": 127.027610
                }
            
    async def kakao_search(self, keyword: str, latitude:str,longitude:str,location_category) -> list:
        params = {
            "query": keyword,
            "x": longitude,
            "y": latitude,
            "radius": 3000,
            "size": 15
        }
        logger.info(f"[kakao_search_location] : {longitude} , {latitude}")
        logger.info(f"[kakao_search_keyword] : {keyword}")
        logger.info(f"[kakao_search_url] : {self.url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=self.headers, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Kakao API Error: {response.status}")
                
                data = await response.json()
                places = data.get("documents", [])
                # 음식점만 필터링
                return [place["place_name"] for place in places if place.get("category_group_code") == location_category]

    
    async def kakao_api_foodstore(self,latitude:str,longitude:str,location_category:str):
        logger.info(f"[주변 {location_category} 데이터 불러오는중...]")
        logger.info(f"[kakao_api_foodstore] : {location_category}")

        headers = {
            "Authorization": "KakaoAK 5d96c7a6ef9ac4662396eafc9c44f63e"  # ← 본인의 REST API 키로 교체
        }

        params = {
            "category_group_code": location_category,       # 위치
            "x": longitude,                  # 경도
            "y": latitude,                   # 위도
            "radius": 3000,                 # 반경 3km
            "sort": "distance",                # 거리순 정렬
            "page": 1,
            "size": 10                         # 1페이지당 10개
        }

        # ✅ GET 요청
        response = requests.get(url, headers=headers, params=params)

        # ✅ 결과 확인
        if response.status_code == 200:
            data = response.json()
            for place in data['documents']:
                print(f"{place['place_name']} - {place['address_name']} ({place['distance']}m)")
        else:
            print("❌ 요청 실패:", response.status_code, response.text)

        data = response.json()

        logger.info(f"[반환할 데이터...]: {data}")

        return data['documents']

    async def ai_match(self,food_store,intention):
        logger.info("[ai가 주변식당 찾아주는중...]")
        
        llm = get_langchain_llm(is_lightweight=True)

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "output": {"type": "string"},
            }
        })
       

        system_prompt="""
        [Role]
        - You are a personalized location recommendation AI assistant.
        - Your goal is to select and return at least 3 locations from a provided list, considering the user's personal profile.

        [user_info]
        - country_born: (ex. ko)
        - birthday: (ex. 1555-05-05)
        - visit_purpose: (ex. Study)
        - gender: (ex. male)

        [place_list]
        1. 대형마트 (Large Mart)
        2. 편의점 (Convenience Store)
        3. 음식점 (Restaurant)
        4. 카페 (Café)
        5. 관광명소 (Tourist Spot)
        6. 숙박 (Accommodation)
        7. 주유소, 충전소 (Gas Station / EV Charging Station)
        8. 주차장 (Parking Lot)
        9. 지하철역 (Subway Station)
        10. 학교 (School)
        11. 학원 (Academy)
        12. 병원 (Hospital)
        13. 약국 (Pharmacy)
        14. 중개업소 (Real Estate)
        15. 공공기관 (Government Office)

        [instructions]
        Please recommend 3~5 places from the list that best fit the user's lifestyle and context, based on:
        - National background, age, gender and general taste
        - Visit purpose (e.g., Study → Cafés, libraries, affordable restaurants, pharmacies)
        - If user intention is provided, please take the user's stated intent into consideration when selecting the recommendations.

        [format]
        "output": [...] 

        [Example]
        "output": [
            "place_name": "서울구로구청",
            "category_group_name": "공공기관",
            "address_name": "서울 구로구 가마산로 245",
            "road_address_name": "서울 구로구 가마산로 245",
            "phone": "02-860-2114",
            "distance": "320",
            "x": "126.889145",
            "y": "37.494682"
        ,
        ...
        ]

        Return only the JSON output. No extra commentary.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt ),
            ("user", "{input}")
        ])


        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            print(f"[ai_match] : {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        description = f"""
        [user_intention]
        {intention}

        [user_data]
        country born: {self.user_prefer['nation']}
        birthday : {self.user['birthday']}
        visitpurpose : {self.user_prefer['visitPurpose']}
        gender : {self.user_prefer['gender']}

        [Food_store]
        {food_store}
        """

        logger.info(f"[SYSTEM PROMPT] : {system_prompt}")
        logger.info(f"[USER PROMPT] : {description}")

        response = parse_product(description)
        # 예외 처리: 'output' 키가 없거나 형식이 잘못된 경우 빈 리스트로 대체
        if "output" not in response or not isinstance(response["output"], list):
            logger.warning("[WARNING] 'output' key is missing or not a list. Defaulting to empty list.")
            response["output"] = []
            
        print("[Input_analysis] :  ",response["output"])

        return response["output"]
