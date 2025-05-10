from typing import Dict, Any
from loguru import logger
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json
import re
import requests
from app.core.llm_prompt import Prompt
# 기존: from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

class AgenticPost:
    def __init__(self):
        logger.info("[게시글 에이전트 초기화]")
        
    # 단계에 맞는 함수 생성
    async def first_query(self, token , query , state) : 

        logger.info("[카테고리 반환 단계]")
        logger.info(f"[넘어온정보]: {token} {query} {state}]")

        llm = ChatOpenAI(
            model="gpt-4-turbo",
            temperature=0.7
        )

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "title": {"type":"string"},
            }
        })

        system_prompt = Prompt.post_prompt()

        print(" [system_prompt] ",system_prompt)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            logger.info(f"[AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        description = query

        response = parse_product(description)

        return response
    #####################################################################


    #####################################################################
    async def second_query(self, token , query , state, title, tags) : 
        logger.info("[게시판 생성 단계]")
        category = title
        llm = ChatOpenAI(
            model="gpt-4-turbo",
            temperature=0.7
        )
        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "category" : {"type" : "string"},
                "language": { "type": "string"},
                "tags" : {"type": "string"},
                "postType":{ "type": "string"},
                "address":{ "type": "string"}
            }
        })
        system_prompt = f"""
        1. Please create a post creation json.
        2. Please make it like the example (tags is list)

        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        !!! if postType is "자유" then address is "자유"
        language example : {"KO", "EN", "JA", "ZH", "DE", "FR", "ES", "RU"}
        ----------------------------------------------------------------------------------------------------
        input : I want to create a post recommending tourist attractions in Jeju Island. , "category": "여행" , "tags": [관광/체험]
        output :  
            "post":  
                "title": "Jeju Island travel recommendations",  
                "content": "We've compiled a list of must-see attractions in Jeju Island! Enjoy a leisurely trip to Seongsan Ilchulbong, Hyeopjae Beach, and Udo.",  
                "category": "여행",  
                "language": "EN",  
                "tags": ["관광/체험"] ,  
                "postType": "자유",  
                "address": "자유"  
        ----------------------------------------------------------------------------------------------------
        input : 일본 맛집 탐방 후기 작성할래 , "category": "여행" , "tags": [식도락/맛집] 
        output :  
            "post":  
                "title": "오사카 맛집 리스트",  
                "content": "돈카츠, 타코야끼, 오코노미야끼 등 오사카에서 먹어야 할 음식과 위치를 정리해봤어요. 여행 전 참고해보세요!",  
                "category": "여행",  
                "language": "KO",  
                "tags": "[식도락/맛집]",  
                "postType": "자유",  
                "address": "자유"  
        ----------------------------------------------------------------------------------------------------
        input : パリ博物館ツアー会議をしたい , "category": "여행" , "tags": [관광/체험]  
        output :  
            "post":  
                "title": "パリ文化を訪れる",  
                "content": "ルーヴル、オルセ、ロダン美術館ツアー一緒にいただく方募集します。フランス芸術に興味のある方歓迎します！",  
                "category": "여행",  
                "language": "JA",  
                "tags": ["관광/체험"],  
                "postType": "모임",  
                "address": "프랑스 파리"  
        ----------------------------------------------------------------------------------------------------
        input : 我想写一篇总结首尔交通的文章。 ,"category": "여행" , "tags": [교통/이동 ] 
        output :  
            "post":  
                "title": " 首尔交通提示",  
                "content": "我们分享如何在首尔轻松乘坐地铁和公交车、换乘技巧以及如何使用T-money的技巧。",  
                "category": "여행",  
                "language": "ZH",  
                "tags": ["교통/이동"],  
                "postType": "자유",  
                "address": "자유"  
        ----------------------------------------------------------------------------------------------------
        input : Ich werde einen Artikel über Apothekeninformationen für Ausländer schreiben. , "category": "여행" , tags": [대사관/응급]  
        output :  
            "post":  
                "title": "Tipps zur Apothekennutzung für Ausländer",  
                "content": "Wir haben Informationen zu für Ausländer leicht zugänglichen Apotheken und grundlegenden rezeptfreien Medikamenten zusammengestellt.",  
                "category": "여행",  
                "language": "DE",  
                "tags": ["대사관/응급"] ,  
                "postType": "자유",  
                "address": "자유"  
        ----------------------------------------------------------------------------------------------------
        input : Je veux partager des conseils pour utiliser le métro à Séoul. , "category": "여행" , "tags": [교통/이동]
        output :  
            "post":  
                "title": "Se déplacer à Séoul en métro",  
                "content": "Découvrez comment utiliser facilement le métro de Séoul, acheter une carte T-money, et naviguer entre les lignes principales.",  
                "category": "여행",  
                "language": "FR",  
                "tags": ["교통/이동"],  
                "postType": "자유",  
                "address": "Corée du Sud, Séoul"  
        ----------------------------------------------------------------------------------------------------
        input : Quiero escribir una publicación sobre mi experiencia gastronómica en México. , "category": "여행" , "tags": [식도락/맛집]
        output :  
            "post":  
                "title": "Comida callejera que debes probar en México",  
                "content": "Desde tacos y elotes hasta tamales y aguas frescas, comparto mis experiencias y lugares favoritos en la Ciudad de México.",  
                "category": "여행",  
                "language": "ES",  
                "tags": ["식도락/맛집"],  
                "postType": "자유",  
                "address": "Ciudad de México, México"  
        ----------------------------------------------------------------------------------------------------
        input : Хочу поделиться местами, которые стоит посетить в Санкт-Петербурге. , "category": "여행" , "tags": [관광/체험]
        output :  
            "post":  
                "title": "Лучшие туристические места Санкт-Петербурга",  
                "content": "Эрмитаж, Исаакиевский собор и прогулки по Неве — вот что обязательно стоит включить в свой маршрут!",  
                "category": "여행",  
                "language": "RU",  
                "tags": ["관광/체험"],  
                "postType": "자유",  
                "address": "Россия, Санкт-Петербург"  
        ----------------------------------------------------------------------------------------------------

        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

                
        ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.

        """

        prompt=system_prompt
        logger.info(f"[system_prompt] : {prompt}")

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            logger.info(f"[게시판 생성 AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        description = f"{query}, category: {category}, tags: {tags}"

        response = parse_product(description)
        response = response["post"]
        response = json.dumps(response, indent=2, ensure_ascii=False)
        logger.info(f"[response 반환값] : {response}")

        post_api(response, token)
        
        return response
    #####################################################################

##################################################################### 게시판 api 요청


def post_api(form_data: str, token: str):
    

    headers = {
        "Authorization": token
    }

    files = {
        "post": (None, form_data, "application/json")
    }

    logger.info(f"[headers] : {headers}")
    logger.info(f"[files] : {files}")

    response = requests.post(
        url = "http://af9c53d0f69ea45c793da25cdc041496-1311657830.ap-northeast-2.elb.amazonaws.com/community/post",
        headers = headers,
        files = files
    )

    print("Status Code:", response.status_code)
    print("Response:", response.text)

    return response

##################################################################### 게시판 api 요청