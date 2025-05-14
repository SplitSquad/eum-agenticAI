from typing import Dict, Any
from loguru import logger
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json
import requests
from app.core.llm_client import get_langchain_llm

class AgenticPost:
    def __init__(self):
        logger.info("[게시글 에이전트 초기화]")
        
        # 카테고리 구조 정의
        self.categories = {
            "여행": ["관광/체험", "식도락/맛집", "교통/이동", "숙소/지역", "대사관/응급"],
            "주거": ["부동산/계약", "생활환경/편의", "문화/생활", "주거지 관리/유지"],
            "유학": ["학사/캠퍼스", "학업지원", "행정/비자/서류", "기숙사/주거"],
            "취업": ["이력/채용", "비자/법률/노동", "잡페어/네트워킹", "알바/파트타임"]
        }

    async def create_post(self, token: str, query: str):
        logger.info("[게시글 생성 시작]")
        logger.info(f"[사용자 입력]: {query}")

        try:
            llm = get_langchain_llm(is_lightweight=False)

            # 시스템 프롬프트 작성
            system_prompt = """당신은 한국에 거주하는 외국인들을 위한 커뮤니티 게시글 작성 및 분류를 돕는 AI 어시스턴트입니다.
사용자의 입력을 바탕으로 적절한 카테고리를 선택하고 게시글을 작성해주세요.

다음은 사용 가능한 카테고리 구조입니다:
{categories}

사용자의 입력을 분석하여:
1. 가장 적절한 대분류(main_category)를 선택하세요
2. 해당 대분류 내에서 가장 적절한 소분류(sub_category)를 선택하세요
3. 주제에 맞는 상세한 게시글 내용을 작성하세요

응답은 반드시 다음 JSON 형식을 따라야 합니다:
{{
    "main_category": "선택된 대분류",
    "sub_category": "선택된 소분류",
    "content": "작성된 게시글 내용"
}}

게시글 작성 시 주의사항:
- 한국에 거주하는 외국인의 관점에서 작성하세요
- 실용적이고 구체적인 정보를 포함하세요
- 예의 바르고 친근한 톤을 유지하세요
- 필요한 경우 관련 법률이나 절차에 대한 정보를 포함하세요"""

            # LLM 호출
            result = llm.invoke({
                "input": query,
                "categories": json.dumps(self.categories, ensure_ascii=False, indent=2)
            })

            # JSON 파싱
            response_text = result.content if hasattr(result, 'content') else str(result)
            response_data = json.loads(response_text)

            logger.info(f"[AI 응답] {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            # API 요청을 위한 데이터 준비
            post_data = {
                "content": response_data["content"],
                "mainCategory": response_data["main_category"],
                "tags": [response_data["sub_category"]]
            }
            
            # API 호출
            response = self._post_api(json.dumps(post_data), token)
            return response

        except Exception as e:
            logger.error(f"[게시글 생성 오류] {str(e)}")
            return None

    def _post_api(self, form_data: str, token: str):
        headers = {
            "Authorization": token
        }

        files = {
            "post": (None, form_data, "application/json")
        }

        logger.info(f"[headers] : {headers}")
        logger.info(f"[files] : {files}")

        try:
            response = requests.post(
                url="http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/community/post",
                headers=headers,
                files=files
            )

            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {response.text}")
            return response

        except Exception as e:
            logger.error(f"[API 요청 오류] {str(e)}")
            return None