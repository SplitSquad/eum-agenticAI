from typing import Dict, Any
from loguru import logger
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json
import re
import requests

class AgenticPost:
    def __init__(self):
        logger.info("[게시글 에이전트 초기회]")
        
    # 단계에 맞는 함수 생성
    async def first_query(self, token , query , state) : 

        logger.info("[카테고리 반환 단계]")
        logger.info(f"[넘어온정보]: {token} {query} {state}]")

        llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.7
        )

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "title": {"type":"string"},
            }
        })
        system_prompt = f"""
        1. User wants to create a post.
        2. Please answer as in the example. ( Please return it like output )
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        input: "게시글을 생성해줘"
        output:
            title: null
            tags : null

        input: "홍보글을 생성해줘"
        output:
            title: null
            tags : null        
        ----------------------------------------------------
        input: "한국 관광지 추천 글을 써볼게"
        output: 
            title: 여행
            tags: 관광/체험

        input: "전통 문화 체험 소개하려고 해"
        output: 
            title: 여행
            tags: 관광/체험

            
        input: "서울 음식점 정리해봤어"
        output: 
            title: 여행
            tags: 식도락/맛집

        input: "맛집 리스트 공유할게"
        output: 
            title: 여행
            tags: 식도락/맛집


        input: "지하철 이용법 설명할게"
        output: 
            title: 여행
            tags: 교통/이동

        input: "공항 환승 노하우 정리했어"
        output: 
            title: 여행
            tags: 교통/이동


        input: "호텔 예약 팁 알려줄게"
        output: 
            title: 여행
            tags: 숙소/지역정보

        input: "지역 숙소 후기 써볼게"
        output: 
            title: 여행
            tags: 숙소/지역정보


        input: "대사관 연락처 정리했어"
        output: 
            title: 여행
            tags: 대사관/응급

        input: "약국 찾는 방법 알려줄게"
        output: 
            title: 여행
            tags: 대사관/응급

        ----------------------------------------------------
        input: "수업 듣는 꿀팁 알려줄게"
        output: 
            title: 유학
            tags: 학사/캠퍼스

        input: "캠퍼스 건물 위치 정리해봤어"
        output: 
            title: 유학
            tags: 학사/캠퍼스


        input: "튜터링 프로그램 이용 후기야"
        output: 
            title: 유학
            tags: 학업지원/시설

        input: "장학금 신청하는 방법 공유할게"
        output: 
            title: 유학
            tags: 학업지원/시설


        input: "학생비자 갱신 절차 설명해줄게"
        output: 
            title: 유학
            tags: 행정/비자/서류

        input: "출입국 서류 준비 방법 알려줄게"
        output: 
            title: 유학
            tags: 행정/비자/서류


        input: "기숙사 신청 절차 알려줄게"
        output: 
            title: 유학
            tags: 기숙사/주거

        input: "기숙사 규칙 정리했어"
        output: 
            title: 유학
            tags: 기숙사/주거
        ----------------------------------------------------
        input: "이력서 양식 추천해줄 수 있어?"
        output: 
            title: 취업
            tags: 이력/채용준비

        input: "면접 준비 어떻게 하는지 공유할게"
        output: 
            title: 취업
            tags: 이력/채용준비


        input: "워킹비자 신청 팁 알려줄게"
        output: 
            title: 취업
            tags: 비자/법률/노동

        input: "근로계약서에서 주의할 점이 있어"
        output: 
            title: 취업
            tags: 비자/법률/노동


        input: "멘토링 프로그램 추천할게"
        output: 
            title: 취업
            tags: 잡페어/네트워킹

        input: "업계 소식 공유합니다"
        output: 
            title: 취업
            tags: 잡페어/네트워킹


        input: "외국인 알바 구직 사이트 소개해줄게"
        output: 
            title: 취업
            tags: 알바/파트타임

        input: "단기 알바 후기 남길게"
        output: 
            title: 취업
            tags: 알바/파트타임
        ----------------------------------------------------
        input: "서울에서 집 구할 때 꿀팁 알려줄게"
        output: 
            title: 주거
            tags: 부동산/계약

        input: "원룸 계약 시 주의사항을 정리했어"
        output: 
            title: 주거
            tags: 부동산/계약


        input: "생활비랑 병원 정보 공유할게"
        output: 
            title: 주거
            tags: 생활환경/편의

        input: "통신사 비교해봤어"
        output: 
            title: 주거
            tags: 생활환경/편의


        input: "동네 소모임 참여 후기 남깁니다"
        output: 
            title: 주거
            tags: 문화/생활

        input: "우리 동네 축제 소개할게"
        output: 
            title: 주거
            tags: 문화/생활


        input: "고장 난 에어컨 수리 후기"
        output: 
            title: 주거
            tags: 주거지 관리/유지

        input: "관리비 아끼는 팁 알려줄게"
        output: 
            title: 주거
            tags: 주거지 관리/유지
        ----------------------------------------------------
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
        ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
        ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
        ⚠️ Do NOT include any explanation or message. ONLY return a valid JSON object. No natural language.
        """

        prompt=system_prompt

        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
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
        llm = ChatGroq(
                model_name="llama-3.3-70b-versatile",
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
        ----------------------------------------------------------------------------------------------------
        input : 제주도 관광지 추천 게시물을 만들고 싶어 , "category": "여행" , "tags": [관광/체험]
        output :  
            "post":  
                "title": "제주도 여행 추천",  
                "content": "제주도에서 꼭 가봐야 할 명소들을 정리해봤어요! 성산일출봉, 협재 해수욕장, 우도까지 여유로운 여행을 즐겨보세요.",  
                "category": "여행",  
                "language": "KO",  
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
        input : 파리 박물관 투어 모임 만들고 싶어 , "category": "여행" , "tags": [관광/체험]  
        output :  
            "post":  
                "title": "파리 문화 탐방",  
                "content": "루브르, 오르세, 로댕 미술관 투어 함께 하실 분 모집해요. 프랑스 예술에 관심 있는 분 환영합니다!",  
                "category": "여행",  
                "language": "KO",  
                "tags": ["관광/체험"],  
                "postType": "모임",  
                "address": "프랑스 파리"  
        ----------------------------------------------------------------------------------------------------
        input : 서울 교통편 정리한 게시글을 쓰고 싶어 ,"category": "여행" , "tags": [교통/이동 ] 
        output :  
            "post":  
                "title": "서울 교통 꿀팁",  
                "content": "서울에서 지하철과 버스를 쉽게 타는 법, 환승 팁과 티머니 사용법을 공유합니다.",  
                "category": "여행",  
                "language": "KO",  
                "tags": ["교통/이동"],  
                "postType": "자유",  
                "address": "자유"  
        ----------------------------------------------------------------------------------------------------
        input : 외국인을 위한 약국 정보 글 써볼게 , "category": "여행" , tags": [대사관/응급]  
        output :  
            "post":  
                "title": "외국인을 위한 약국 이용 팁",  
                "content": "외국인도 쉽게 갈 수 있는 약국 정보, 처방전 없이 살 수 있는 기본 상비약 정리했습니다.",  
                "category": "여행",  
                "language": "KO",  
                "tags": ["대사관/응급"] ,  
                "postType": "자유",  
                "address": "자유"  
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