import json
import requests
from geopy.geocoders import Nominatim
from loguru import logger
from app.core.llm_client import get_langchain_llm
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import ChatPromptTemplate
from app.services.common.user_information import User_Api

# ✅ API 기본 설정
# url = "https://dapi.kakao.com/v2/local/search/category.json"


class foodstore():
    user_api=User_Api()
    
    def __init__(self):
        self.user = ""
        self.user_prefer = ""

    async def load_user_data(self, token: str):
        # ✅ user_api는 비동기이므로 await로 호출
        logger.info("[사용자 정보 불러오는중...]")
        self.user = await self.user_api.user_api(token)
        self.user_prefer = await self.user_api.user_prefer_api(token)
        logger.info(f"[사용자 정보]: {self.user} | {self.user_prefer}")
    
    async def location(self):
        logger.info("[사용자 위치 조회중...]")
        user_address=self.user['address']

        ##임의로 주소 선정
        user_address = "서울 강남"

        ## 실제 이메일 사용해야함!
        geolocator = Nominatim(user_agent="jwontiger@gmail.com")
        location = geolocator.geocode(user_address)
        print((location.latitude, location.longitude))
        return {
            "latitude": location.latitude , 
            "longitude": location.longitude
        }

    async def kakao_api_foodstore(self,latitude:str,longitude:str,location_category):
        logger.info(f"[주변 {location_category} 데이터 불러오는중...]")

        headers = {
            "Authorization": "KakaoAK 5d96c7a6ef9ac4662396eafc9c44f63e"  # ← 본인의 REST API 키로 교체
        }

        params = {
            "category_group_code": location_category,       # 위치
            "x": longitude,                  # 경도
            "y": latitude,                   # 위도
            "radius": "10000",                 # 반경 10km
            "sort": "distance",                # 거리순 정렬
            "page": 1,
            "size": 10                         # 1페이지당 10개
        }

        # ✅ GET 요청
        response = requests.get("https://dapi.kakao.com/v2/local/search/category.json", headers=headers, params=params)

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

    async def ai_match(self,food_store):
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
        1. Can you recommend a place that fits my user information?
        2. Please return it as json. < "output" : "..." >
        3. please return at least 3
        
        [example]

        "output":  [
            "address_name": "서울 강남구 삼성동 16",
            "distance": "50",
            "id": "950568212",
            "phone": "02-540-8688",
            "place_name": "미얌 샌드위치",
            "road_address_name": "서울 강남구 학동로68길 7",
            "x": "127.046744137873",
            "y": "37.5176168952442"
        ]

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

        [user_data]
        address : {self.user["address"]}
        country born: {self.user_prefer["nation"]}
        birthday : {self.user["birthday"]}
        visitpurpose : {self.user_prefer["visitPurpose"]}
        gender : {self.user_prefer["gender"]}

        [Food_store]
        {food_store}
        """

        logger.info(f"[SYSTEM PROMPT] : {system_prompt}")
        logger.info(f"[USER PROMPT] : {description}")

        response = parse_product(description)
    
        print("[Input_analysis] :  ",response["output"])

        return response["output"]
