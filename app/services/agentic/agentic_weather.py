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
            user_information["address"] = "서울 강남"
    

        # ai가 쿼리문 다듬어줌.

        # LLM 클라이언트 인스턴스 가져오기
        llm_client = get_llm_client(is_lightweight=False)

        # 프롬프트 구성
        prompt = f"""
        You are an AI assistant that extracts the location from a user's question in order to generate a weather-related search query.

        🎯 Your task is as follows:
        1. If the user's input contains a location (city, region, etc.), use it.
        2. If there is no location mentioned, use the default location: "{user_information["address"]}".
        3. The output must follow this exact format:
        👉 <location> weather (e.g., Seoul weather, Daejeon weather)

        🚫 Do NOT explain anything.  
        🚫 Do NOT include quotes or additional text.  
        ✅ Output ONLY the final search query, in a single line.

        ---

        [Examples]
        User input: "What's the weather like in Daejeon?"  
        Output: Daejeon weather

        User input: "How's the weather today?"  
        Output: {user_information["address"]} weather

        User input: "Tell me the temperature in Seoul"  
        Output: Seoul weather

        User input: "Is it going to rain?"  
        Output: {user_information["address"]} weather

        ---

        Now convert the following user input into a weather search query:
        {query}
        """

        # 직접 호출 (클라이언트마다 방식 다를 수 있음)
        # response_query = await llm_client.generate(prompt)
        # logger.info(f"[ai가 검색할 문장] : {response_query}")

        res = service.cse().list(
            q="서울 날씨",
            cx=self.search_engine_id,
            num=3,
            dateRestrict='d1',
            siteSearch='kma.go.kr'  # 기상청으로 도메인 제한
        ).execute()

        logger.info(f"[구글 서치결과] : {res}")

        # 기상청 url 접속
        url = await self.Meteorological_Administration(res)
        # table = soup.select_one("table.table-col")  # 테이블 클래스명 확인 필요
        
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

    
    async def Meteorological_Administration(self, res):
        logger.info("[기상청 URL 추출 중...]")
        for item in res.get("items", []):
            link = item.get("link", "")
            if "kma.go.kr" in link:
                logger.info(f"[기상청 URL 찾음] : {link}")
                return link
        logger.warning("기상청 URL을 찾지 못했습니다.")
        return None

    async def Crawling(self, url):
        logger.info(f"[HTML 크롤링 중] : {url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # ✅ 테이블 선택
                table = soup.select_one("table.table-col")  # class 확인 필요

                if not table:
                    return "테이블을 찾지 못했습니다."

                # ✅ 특정 지역(예: 서울)의 날씨 정보 추출
                rows = table.find_all("tr")
                for row in rows:
                    city = row.find("th")
                    if city and "서울" in city.text:
                        cells = row.find_all("td")
                        weather = cells[0].text.strip()
                        temperature = cells[4].text.strip()  # 현재기온 (보통 5번째 <td>)
                        humidity = cells[8].text.strip()    # 습도
                        wind_dir = cells[9].text.strip()    # 풍향
                        wind_speed = "1.2 m/s"  # JS로 렌더링되어 있어 수동으로 넣거나 무시

                        return f"📍 서울\n날씨: {weather}\n기온: {temperature}℃\n습도: {humidity}%\n풍향: {wind_dir}\n풍속: {wind_speed}"

                return "서울 지역 정보를 찾을 수 없습니다."
            else:
                logger.error(f"요청 실패: {response.status_code}")
                return "페이지를 불러오지 못했습니다."
        except Exception as e:
            logger.exception("크롤링 실패")
            return f"크롤링 오류: {e}"



