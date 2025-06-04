from googleapiclient.discovery import build
from dotenv import load_dotenv
from loguru import logger
from app.core.llm_client import get_llm_client,get_langchain_llm
from app.services.common.user_information import User_Api
import os
import requests
from bs4 import BeautifulSoup
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.services.common.search_location import search_location
import json
load_dotenv()  # .env 파일을 읽어서 환경변수로 등록


class Weather():
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_WEATHER_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_WEATHER_ENGINE_ID")
        self.user_information = User_Api()
        self.user_information_data = ""
        self.user = ""
        self.user_prefer = ""
        self.llm = get_llm_client(is_lightweight=True)  # ✅ 추가된 부분
        self.search_live_location = search_location()

    async def weather_google_search(self, query,token,live_location):
        logger.info("[구글 서치중...]")
        service = build("customsearch", "v1", developerKey=self.api_key)

        # 사용자 정보불러옴
        logger.info("[사용자 정보 불러오는중...]")
        self.user = await self.user_information.user_api(token)
        self.user_prefer = await self.user_information.user_prefer_api(token)
        
        # 유저 위치 정보 수집
        logger.info("[유저 위치 정보 수집...]")
        logger.info(f"[live_location] : {live_location}")

        if live_location is None or not (getattr(live_location, "latitude", None) and getattr(live_location, "longitude", None)):
            logger.warning("[WARNING] live_location이 유효하지 않아 사용자 정보 기반으로 fallback 처리합니다.")
            self.user_information_data = await self.user_information.user_api(token)
            if not self.user_information_data.get("address"):
                self.user_information_data["address"] = "서울 중구"
        else:
            self.user_information_data = self.search_live_location.search(live_location)

        logger.info(f"[user_information_location] : {self.user_information_data}")

    
        
        # self.user_information_data['address']

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
        Extract the region name from the user's input and match it to one of the following values:
        [서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종, 경기도, 강원도, 충청북도, 충청남도, 전라북도, 전라남도, 경상북도, 경상남도, 제주도]

        1. If the user's input contains a region, return the matching region name.
        2. PRIORTIZE FIRST INSTRUCTION.
        3. RESPONSE MUST BE VALUE, NOT NATURAL LANGUAGE.
        default. If there is no location information in user_input, use the location of default_location. 
         
        [format]
        "output":"str"
        
        [one-shot-example]
        input : 
            user_input : <query>  + default_location : <user_information['address']>
        output : 
            <region>


        """),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            logger.info(f"[json.dumps] : {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        description = f"user_input : {query}  + default_location : {self.user_information_data['address']} "

        logger.info(f"[description] : {description} ")

        response = parse_product(description)
        
        # 추출 및 보정
        if not response or 'output' not in response or not response['output'].strip():
            logger.warning("[WARNING] 'output' key is missing or empty. Defaulting to '서울'.")
            response['output'] = '서울'

        # ✅ 여기서 문자열로 덮어쓰기
        region_name = response["output"]

        logger.info(f"[lang_chain] : {region_name}")
        logger.info(f"[lang_chain_type] : {type(region_name)}")




        url = await self.get_special_weather_url(region_name)
        logger.info(f"[ai가 검색할 url] : {url}")

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        # 크롤링
        if not url:
            return {"response": "기상청 정보를 찾지 못했습니다.", "url": None}

        html_data = await self.Crawling(url)

        query=f""" 
        [user data]  
        {self.user}
        {self.user_prefer}

        [html_data]
        {html_data}
        """

        logger.info(f"[query] : {query}")

        logger.info("[사용자의 언어로 변형중...]")
        result = await self.llm.generate(f"""
        [input]
        {query}

        [Role]
        You are a friendly Korean weather announcer AI designed to provide personalized weather briefings in a style akin to a TV forecaster.

        [instruction]
        1. Analyze the user's profile data:
            - Age, gender, nationality, visit purpose, interests, stay period, and Korean proficiency level.
            - Employ a warm, casual tone suitable for travelers or short-term visitors.

        2. Interpret the provided weather forecast in Korean (html_data):
            - Extract temperature and weather conditions for each day.
            - Note: Do not use separate location information; it's already included in the weather text.

        3. Based on the forecast:  
            - Naturally introduce the **weather in the mentioned region** (e.g., 부산) over the next 5–6 days, emulating a TV weather host.  
            - Explicitly emphasize that the weather information is **specific to that region**.  
            - Include simple, helpful tips if necessary (e.g., “don’t forget your umbrella,” “wear something cool,” “great weather for sightseeing”).  
            - Adapt tone and word choices based on the user's background (e.g., for a Japanese tourist, use simpler and more friendly expressions).  

        4. Delivery:
            - Avoid listing the weather mechanically. Instead, present it as a short, natural spoken segment.
            - Do not repeat or explain the input.
            - Format the output with appropriate line breaks to enhance readability and visual clarity. 
""")
        logger.info("[ai 아나운서]", result)
        
        return {
            "response": result,
            "metadata": {
                "source": "kma.go.kr",
                "state": "weather_state",
                "results": "html"
            },
            "url": None
        }

    async def Crawling(self, url: str):
        logger.info(f"[HTML 크롤링 중] : {url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return "페이지를 불러오지 못했습니다."

            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.select_one("table.table_midterm")
            if not table:
                return "날씨 테이블을 찾지 못했습니다."

            # 1. 날짜 헤더 추출
            headers_list = [th.text.strip() for th in table.select("thead tr th")[2:]]

            # 2. 추출 대상 지역 목록
            target_cities = [
                "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
                "경기도", "강원도", "충청북도", "충청남도", "전라북도", "전라남도",
                "경상북도", "경상남도", "제주도"
            ]

            result = ""

            for row in table.select("tbody tr"):
                ths = row.find_all("th")
                if len(ths) >= 2:
                    city_name = ths[1].text.strip()
                    if city_name in target_cities:
                        tds = row.find_all("td")
                        forecast = []

                        for i in range(min(len(headers_list), len(tds))):
                            td = tds[i]
                            weather_img = td.find("img")
                            weather = weather_img["alt"] if weather_img else "정보 없음"

                            spans = td.find_all("span")
                            if len(spans) >= 2:
                                low = spans[0].text.strip()
                                high = spans[1].text.strip()
                                forecast.append(f"🗓️ {headers_list[i]}: {weather}, {low}℃ / {high}℃")
                            else:
                                forecast.append(f"🗓️ {headers_list[i]}: {weather}, 정보 없음")

                        result += f"\n📍 {city_name} 날씨 정보\n" + "\n".join(forecast) + "\n"

            if not result:
                return "해당 지역들의 정보를 찾을 수 없습니다."

            return result.strip()

        except Exception as e:
            logger.exception("크롤링 실패")
            return f"크롤링 오류: {e}"



    async def get_special_weather_url(self,area_name: str) -> str:
        AREA_CODE_MAP = {
            "서울": {
                "sido": "1100000000",
                "gugun": "2644000000",
                "dong": "2644058000"
            },
            "부산": {
                "sido": "2600000000",
                "gugun": "3023000000",
                "dong": "3023052000"
            },
            "대구": {
                "sido": "2700000000",
                "gugun": "2920000000",
                "dong": "2920054000"
            },
            "인천": {
                "sido": "2800000000",
                "gugun": "3114000000",
                "dong": "3114056000"
            },
            "광주": {
                "sido": "2900000000",
                "gugun": "4729000000",
                "dong": "4729053000"
            },
            "대전": {
                "sido": "3000000000",
                "gugun": "2720000000",
                "dong": "2720065000"
            },
            "울산": {
                "sido": "3100000000",
                "gugun": "3611000000",
                "dong": "3611055000"
            },
            "세종": {
                "sido": "3600000000",
                "gugun": "1168000000",
                "dong": "1168066000"
            },
            "경기도": {
                "sido": "4100000000",
                "gugun": "4215000000",
                "dong": "4215061500"
            },
            "강원도": {
                "sido": "4200000000",
                "gugun": "4182000000",
                "dong": "4182025000"
            },
            "충청북도": {
                "sido": "4400000000",
                "gugun": "5013000000",
                "dong": "5013025300"
            },
            "충청남도": {
                "sido": "4400000000",
                "gugun": "5013000000",
                "dong": "5013025300"
            },
            "전라북도": {
                "sido": "4500000000",
                "gugun": "4681000000",
                "dong": "4681025000"
            },
            "전라남도": {
                "sido": "4600000000",
                "gugun": "2871000000",
                "dong": "2871025000"
            },
            "경상북도": {
                "sido": "4700000000",
                "gugun": "4831000000",
                "dong": "4831034000"
            },
            "경상남도": {
                "sido": "4800000000",
                "gugun": "4182000000",
                "dong": "4182025000"
            },
            "제주도": {
                "sido": "5000000000",
                "gugun": "4579000000",
                "dong": "4579031000"
            }
        }

        area_name = area_name.strip()

        if area_name in AREA_CODE_MAP:
            code = AREA_CODE_MAP[area_name]
            return f"http://www.weather.go.kr/weather/special/special_03_final.jsp?sido={code['sido']}&gugun={code['gugun']}&dong={code['dong']}"
        else:
            raise ValueError(f"'{area_name}' 지역은 지원되지 않습니다.")
