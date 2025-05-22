from googleapiclient.discovery import build
from dotenv import load_dotenv
from loguru import logger
from app.core.llm_client import get_llm_client
import os

load_dotenv()  # .env 파일을 읽어서 환경변수로 등록

class agentic_job_search():
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SERACH_WEATHER_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

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


    async def google_search(self, query):
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
                        "state": "initial",        # ✅ metadata 안에 포함
                        "results": "default"
                    },
                "url": None
                }
    
    async def Trim(self, items: list) -> list:
        """검색 결과를 프론트엔드용으로 정제"""
        trimmed = []
        for item in items:
            result = {
                "title": item.get("title"),
                "link": item.get("link")
            }


            trimmed.append(result)

        return trimmed



