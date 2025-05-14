from loguru import logger
import json
import os
from app.core.llm_client import get_llm_client,get_langchain_llm
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_post_prompt import Prompt
# ✅ 사용자에게 물어봐야 할 항목 목록
# 1. 기본 인적 사항
# name: 성명
# birth_date: 생년월일 (예: 1990-01-01)
# phone: 전화번호
# nation: 국적 (예: 대한민국, 일본 등)
# address: 현 주소
# email: 이메일
# 2. 가족사항 (최대 3명)
# 3. 학력 사항 (education) (최대 5개)
# 4. 자격증 사항 (certifications) (최대 5개, 학력과 합쳐서 총 5개만 출력)
# 5. 경력 사항 (career) (최대 5개)

USER_DATA_DIR = "user_data"
os.makedirs(USER_DATA_DIR, exist_ok=True)

class AgenticResume():
    def __init__(self):
        self.prompt = Prompt()  # ✅ 여기서 선언


    def save_user_data(self, uid: str, state: str, query: str):
        file_path = os.path.join(USER_DATA_DIR, f"{uid}.json")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        data[state] = query

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"[저장 완료] 사용자 {uid} → {state}: {query}")

    def get_user_data(self, uid: str):
        file_path = os.path.join(USER_DATA_DIR, f"{uid}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    async def first_query(self,original_query,query,uid,token,intention,state) :
        logger.info("[first_query 함수 실행중...]")
        logger.info(f"[처음 state 상태] : {state}")

        # 사용자 응답 저장
        if state != "initial":
            self.save_user_data(uid, state, query)
        
        if state == "initial" : 
            state = "family"
             

        logger.info(f"[initial처리후 state 상태] : {state}")    

        if state == "family":
            text = "가족사항에대해 입력해주세요."
            state = "education"
            return {
                "ask_query" : text,
                "state" : state
            }
        
        elif state == "education":
            text = "학력사항에대해 알려주세요."
            state = "certifications"
            return {
                "ask_query" : text,
                "state" : state
            }
        
        elif state == "certifications":
            text = "자격증에대해 알려주세요."
            state = "career"
            return {
                "ask_query" : text,
                "state" : state
            }
        
        elif state == "career":
            text = "경력 사항에대해 알려주세요"
            state = "complete"
            return {
                "ask_query" : text,
                "state" : state
            }

        else :
            logger.warning(f"[first_query] 알 수 없는 state: {state}")
            return {
                "ask_query": "이력서 항목을 알 수 없습니다.",
                "state": "error"
            }
        
    async def make_pdf(self, original_query, query, uid, token, intention, state):
        user_data = self.get_user_data(uid)

        user_info = await self.fetch_user_data(uid, token)
        preference_info = await self.fetch_user_preference(uid, token)

        # 예시 로그 출력
        logger.info(f"[make_pdf] 수집된 사용자 데이터: {json.dumps(user_data, ensure_ascii=False, indent=2)}")
        logger.info(f"[make_pdf] 사용자 정보: {json.dumps(user_info, ensure_ascii=False, indent=2)}")
        logger.info(f"[make_pdf] 사용자 선호도: {json.dumps(preference_info, ensure_ascii=False, indent=2)}")

        collected_user_data = {json.dumps(user_data, ensure_ascii=False, indent=2)}
        
        # ai 에게 정보 보내준다음 html 반환받음
        ai_response = await self.make_html_ai(collected_user_data,user_info,preference_info)

        logger.info(f"[ai_response] : {ai_response}")

        # pdf로 변환

        # s3에 저장


        return
    
    async def fetch_user_data(self, uid, token):
        return {
            "userId": 1,
            "email": "example@email.com",
            "name": "홍길동",
            "phoneNumber": "010-4017-2871",
            "birthday": "1999-10-02",
            "profileImagePath": "https://path.to/profile.jpg",
            "address": "서울특별시 강남구",
            "signedAt": "2025-04-28T12:00:00",
            "isDeactivate": False,
            "role": "ROLE_USER"
        }

    async def fetch_user_preference(self, uid, token):
        return {
            "preferenceId": 1,
            "userId": 1,
            "nation": "KOREA",
            "language": "KO",
            "gender": "MALE",
            "visitPurpose": "Travel",
            "period": "1 month",
            "onBoardingPreference": "{}",
            "isOnBoardDone": True,
            "createdAt": "2025-04-28T11:02:25.150532",
            "updatedAt": "2025-04-28T17:17:28.062318"
        }

    async def make_html_ai(self,collected_user_data,user_info,preference_info):

        llm = get_langchain_llm(is_lightweight = False)

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "title": {"type":"string"},
            }
        })

        system_prompt = Prompt.make_html_ai_prompt()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            logger.info(f"[AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        description = f"""{collected_user_data} + {user_info} + {preference_info}"""

        response = parse_product(description)

        return response

    