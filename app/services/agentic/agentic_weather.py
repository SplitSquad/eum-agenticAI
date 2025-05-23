from googleapiclient.discovery import build
from dotenv import load_dotenv
from loguru import logger
from app.core.llm_client import get_llm_client
from app.services.common.user_information import User_Api
import os
import requests
from bs4 import BeautifulSoup
load_dotenv()  # .env 파일을 읽어서 환경변수로 등록

class Weather():
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SERACH_WEATHER_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_WEATHER_ENGINE_ID")
        self.user_information = User_Api()

    async def weather_google_search(self, query,token):
        logger.info("[구글 서치중...]")
        service = build("customsearch", "v1", developerKey=self.api_key)


        user_information = await self.user_information.user_api(token)
        if user_information.get("address") is None:
            user_information["address"] = "부산 동구"
    

        # ai가 쿼리문 다듬어줌.

        # LLM 클라이언트 인스턴스 가져오기
        llm_client = get_llm_client(is_lightweight=False)

        # 프롬프트 구성
        prompt = f"""
        Extract the region name from the user's input and match it to one of the following values:
        [서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종, 경기도, 강원도, 충청북도, 충청남도, 전라북도, 전라남도, 경상북도, 경상남도, 제주도]

        1. If the user's input contains a region, return the matching region name.
        2. If no region is found, use the user's address information <{user_information['address']}> to determine the most appropriate region.
        3. PRIORTIZE FIRST INSTRUCTION.
        4. RESPONSE MUST BE VALUE, NOT NATURAL LANGUAGE.

        """

        # 직접 호출 (클라이언트마다 방식 다를 수 있음)
        response_query = await llm_client.generate(prompt)
        logger.info(f"[ai가 검색할 문장] : {response_query}")

        text = response_query

        url = await self.get_special_weather_url(text)
        logger.info(f"[ai가 검색할 url] : {url}")

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        print(f"[soup] : {soup}")
        
        # 크롤링
        if not url:
            return {"response": "기상청 정보를 찾지 못했습니다.", "url": None}

        html_data = await self.Crawling(url)
        return {
            "response": html_data,
            "metadata": {
                "source": "kma.go.kr",
                "state": "parsed",
                "results": "html"
            },
            "url": url
        }

    async def Crawling(self, url: str, city_name: str = "부산"):
        logger.info(f"[HTML 크롤링 중] : {url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return "페이지를 불러오지 못했습니다."

            soup = BeautifulSoup(response.text, "html.parser")

            # ✅ 1. 날짜 헤더 추출
            table = soup.select_one("table.table_midterm")
            if not table:
                return "날씨 테이블을 찾지 못했습니다."

            headers = [th.text.strip() for th in table.select("thead tr th")[2:]]

            # ✅ 2. '부산'이 포함된 행 찾기
            for row in table.select("tbody tr"):
                ths = row.find_all("th")
                if len(ths) >= 2 and city_name == ths[1].text.strip():
                    tds = row.find_all("td")
                    forecast = []

                    for i in range(min(len(headers), len(tds))):
                        td = tds[i]
                        weather_img = td.find("img")
                        weather = weather_img["alt"] if weather_img else "정보 없음"

                        spans = td.find_all("span")
                        if len(spans) >= 2:
                            low = spans[0].text.strip()
                            high = spans[1].text.strip()
                            forecast.append(f"🗓️ {headers[i]}: {weather}, {low}℃ / {high}℃")
                        else:
                            forecast.append(f"🗓️ {headers[i]}: {weather}, 정보 없음")

                    return f"📍 {city_name} 날씨 정보\n" + "\n".join(forecast)

            return f"{city_name} 지역 정보를 찾을 수 없습니다."

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
