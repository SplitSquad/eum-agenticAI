from typing import Dict, Any
from loguru import logger
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
import json
import re
import requests
import os
from dotenv import load_dotenv
from app.core.llm_post_prompt import Prompt
from langchain_openai import ChatOpenAI
from app.core.llm_client import get_langchain_llm
from app.models.agentic_response import PostCategory
from app.services.common.user_information import User_Api
from app.services.common.search_location import search_location

load_dotenv()  # .env 파일 자동 로딩

# 환경변수에서 API URL 가져오기
COMMUNITY_API_URL = os.getenv("COMMUNITY_API_URL", "https://api.eum-friends.com/community/post")

if not COMMUNITY_API_URL:
    raise ValueError("COMMUNITY_API_URL 환경변수가 설정되지 않았습니다.")

class AgenticPost:
    def __init__(self):
        logger.info("[게시글 에이전트 초기화]")
        self.user_information_data = ""
        self.user_information = User_Api()
        self.search_live_location = search_location()
        
    async def first_query(self, token, query): 
        logger.info("[카테고리 반환 단계]")
        logger.info(f"[user token]: {token}")
        logger.info(f"[user query]: {query}")

        llm = get_langchain_llm(is_lightweight=False)

        # 대분류, 소분류 json으로 반환하는 파서
        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": [cat.value.split('-')[0] for cat in PostCategory]
                },
                "tags": {
                    "type": "string",
                    "enum": [cat.value.split('-')[1] for cat in PostCategory]
                }
            },
            "required": ["category", "tags"]
        })

        json_format = '''
        {{
            "category": "여행/주거/유학/취업 중 하나",
            "tags": "해당 카테고리의 태그 중 하나"
        }}
        '''

        valid_categories = "\n".join([f"- {cat.value}" for cat in PostCategory])

        system_prompt = f"""
        분석할 게시글의 카테고리와 태그를 결정하는 assistant입니다.
        사용자의 입력을 분석하여 가장 적절한 카테고리와 태그를 선택하세요.

        다음 JSON 형식으로만 응답하세요:
        {json_format}

        사용 가능한 카테고리-태그 조합:
        {valid_categories}

        주의사항:
        1. 반드시 위 목록에 있는 카테고리와 태그만 사용하세요
        2. 카테고리는 하이픈(-) 앞부분만 사용
        3. 태그는 하이픈(-) 뒷부분만 사용
        4. JSON 형식만 반환하고 다른 설명은 포함하지 마세요
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            
            logger.info(f"[입력으로 전달된 변수] : {description}")
            logger.info(f"[입력으로 전달된 변수 type] : {type(description)}")
            
            logger.info(f"[템플릿이 요구하는 변수] : {prompt.input_variables}")
            result = chain.invoke({"input": description})
            logger.info(f"[AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            logger.info(f"[AI가 반환한값 type] {type(result)}")
            return result

        response = parse_product(query)

        # 예외처리: category 또는 tags가 누락되었거나 비어 있을 경우 기본값 설정
        valid_category_values = [cat.value.split('-')[0] for cat in PostCategory]
        valid_tag_values = [cat.value.split('-')[1] for cat in PostCategory]

        if 'category' not in response or response['category'] not in valid_category_values:
            logger.warning("[WARNING] 'category' is missing or invalid. Defaulting to '여행'.")
            response['category'] = '여행'

        if 'tags' not in response or response['tags'] not in valid_tag_values:
            logger.warning("[WARNING] 'tags' is missing or invalid. Defaulting to '관광'.")
            response['tags'] = '관광'
            
        return response

    async def second_query(self, token, query, category, tags,live_location):

        #####유저정보
        # 유저 위치 정보 수집
        logger.info("[유저 위치 정보 수집...]")
        logger.info(f"[live_location] : {live_location}")
        if live_location is None or not (live_location.latitude and live_location.longitude):
            self.user_information_data = await self.user_information.user_api(token)
            if self.user_information_data.get("address") is None:
                self.user_information_data["address"] = "부산 동구" 
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

        logger.info(f" [back_user_data] : {back_user_data} ")
        #####유저정보

        logger.info(f"[게시판 생성 단계] 카테고리 : {category}")
        logger.info(f"[게시판 생성 단계] 태그 : {tags}")
        logger.info(f"[게시판 생성 단계] 입력값 : {query}")

        llm = get_langchain_llm(is_lightweight=False)

        # LangChain에서 템플릿 변수로 오인되지 않도록 중괄호 이스케이프 처리 필요 없음
        json_example = f'''
        "title": "Post title",
        "content": "Post body",
        "category": "{category}",
        "language": "KO",
        "tags": ["{tags}"],
        "postType": "자유",
        "address": "자유"
        '''

        system_prompt = f"""
        [ROLE]
        - You are an assistant who writes posts to be posted on the bulletin board based on user input.
        - Write your posts in the following JSON format:

        [FORMAT]
        ```json
        {json_example}
        

        [INSTRUCTION]
        - Below, you will be given the user's background information along with their request (input_query).
        - Based on this information, write a realistic and natural post in strict JSON format.
        - Feel free to incorporate the user's age, purpose of visit, interests, travel country or city, and other relevant details.
        - Most importantly, reflect the user's intent as expressed in the "input_query".

        1. The "title" should clearly reflect the user's intent in a short and concise way. (e.g., "Looking for a travel buddy in Seoul")
        2. The "content" should sound natural and friendly, incorporating the user's purpose, schedule, location, and motivation.
        3. The "category" must be set to "{category}". Do not change this value.
        4. The "tags" must be provided in the format ["{tags}"]. Use a JSON array with one or more string values.
        5. Always set "language" to "KO".
        6. Always set "postType" and "address" to "자유" (Korean word meaning "Free").
        7. Do not include the user's real name in the post. Write the content anonymously.
        8. Write all values such as "title" and "content" in Korean language.
        9. The response must contain **only** a JSON object. Do not include any extra text, comments, markdown, or explanations.


         """

        # 프롬프트 직접 조합
        full_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
            ])
        
        parser = JsonOutputParser(pydantic_object={
                "type": "object",
                "properties": {
                "post": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "category": {"type": "string"},
                            "language": {"type": "string", "enum": ["KO", "EN", "JA", "ZH", "DE", "FR", "ES", "RU"]},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "postType": {"type": "string", "enum": ["자유"]},
                            "address": {"type": "string", "enum": ["자유"]}
                            },
                        "required": ["title", "content", "category", "language", "tags", "postType", "address"]
                    }
                },
                "required": ["post"]
            })

        chain = full_prompt | llm | parser

        def parse_product(user_input: str) -> dict:
            logger.info(f"[입력으로 전달된 변수] : {user_input}")
            result = chain.invoke({"input": user_input})
            logger.info(f"[게시판 생성 AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        input_query = f"""
        [userdata]
        {back_user_data}

        [input_query]
        {query}
        """
        logger.info(f"[input_query] {input_query}")

        response_data = parse_product(input_query)
        
        logger.info(f"[response_data] : {response_data}")
        logger.info(f"[response_data type] : {type(response_data)}")
        
        response_json = json.dumps(response_data, indent=2, ensure_ascii=False)
        
        logger.info(f"[response 반환값] : {response_json}")
        logger.info(f"[response_json type] : {type(response_json)}")

        post_api(response_json, token)
        return response_json


##################################################################### 게시판 api 요청

def post_api(form_data: str, token: str):
    
    
    logger.info(f"[POST API 호출] : {COMMUNITY_API_URL}")
    logger.info(f"[form_data] : {form_data}")
    logger.info(f"[form_data type] : {type(form_data)}")
    
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
            url=f"{COMMUNITY_API_URL}",
            headers=headers,
            files=files
        )

        print("Status Code:", response.status_code)
        print("Response:", response.text)

    except Exception as e:
        logger.error(f"게시글 API 호출 중 오류 발생: {str(e)}")
        return "응답 생성 중 오류 발생"
    
    return response

##################################################################### 게시판 api 요청