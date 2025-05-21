
from loguru import logger
import json
import os
from app.core.llm_client import get_llm_client,get_langchain_llm
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_post_prompt import Prompt
from app.services.common.user_information_resume import User_Information_Resume
from app.services.common.user_information import User_Api
from app.services.common.user_pdf import UserPDF
from app.services.common.user_s3 import UserS3

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


class AgenticResume():
    def __init__(self):
        self.prompt = Prompt()  # ✅ 여기서 선언
        self.user_information = User_Information_Resume()
        self.llm = get_llm_client()
        self.user_api = User_Api()
        self.user_pdf = UserPDF()
        self.user_s3 = UserS3()

    async def save_user_data(self, uid: str, state: str, query: str):
        await self.user_information.store_user_data(uid,query,state)
    
    async def first_query(self,query,uid,token,state,source_lang) :
        logger.info("[first_query 함수 실행중...]")
        logger.info(f"[처음 state 상태] : {state}")

        
        if state == "initial" : 
            state = "education"
             
        logger.info(f"[initial처리후 state 상태] : {state}")    

        if state == "education":

            logger.info("[질문 만드는중...]")            
            result = await self.llm.generate(f" <Please translate it into {source_lang}>  Please tell me about your academic background. ")
            logger.info("[사용자에게 질문할 쿼리]", result)

            state = "certifications"
            return {
                "response": result,
                "metadata": {
                    "source": "default",
                    "state": state         # ✅ metadata 안에 포함
                },
                "url": None
            }

        
        elif state == "certifications":


            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f" <Please translate it into Korean> {query}")
            state="education"
            await self.save_user_data(uid, state, response_query)

            logger.info("[질문 만드는중...]") 
            result = await self.llm.generate(f" <Please translate it into {source_lang}>  Please tell me about the qualifications.")
            logger.info("[사용자에게 질문할 쿼리]", result)

            state = "career"
            return {
                "response": result,
                "metadata": {
                    "source": "default",
                    "state": state         # ✅ metadata 안에 포함
                },
                "url": None
            }
        
        elif state == "career":

            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f" <Please translate it into Korean> {query}")
            state="certifications"
            await self.save_user_data(uid, state, response_query)

            
            logger.info("[질문 만드는중...]") 
            result = await self.llm.generate(f" <Please translate it into {source_lang}> Please tell us about your career history.")
            logger.info("[사용자에게 질문할 쿼리]", result)

            state = "complete"
            return {
                "response": result,
                "metadata": {
                    "source": "default",
                    "state": state         # ✅ metadata 안에 포함
                },
                "url": None
            }
        
        elif state == "complete":


            logger.info("[사용자에게 받은 응답 저장하는중...]")
            response_query = await self.llm.generate(f" <Please translate it into Korean> {query}")
            state="career"
            await self.save_user_data(uid, state, response_query)

            logger.info("[질문 만드는중...]") 
            result = await self.llm.generate(f" <Please translate it into {source_lang}> Resume completed.")
            logger.info("[사용자에게 질문할 쿼리]", result)

            # html 반환
            # html = await self.make_html_ai(token,uid)

            # user_data ai가 생성
            user_data = await self.make_user_data(uid,token)

            # html 반환 생성중
            html = await self.user_pdf.pdf_html_form(user_data)

            # pdf 로변환
            pdf_path = await self.user_pdf.make_pdf(uid,html)

            # s3 저장
            url = await self.user_s3.upload_pdf(pdf_path)

            # json 데이터 정리
            await self.user_information.delete_user_data(uid)

            return {
                "response": result,
                "metadata": {
                    "source": "default",
                    "state": "initial"         # ✅ metadata 안에 포함
                },
                "url": url
            }

        else :
            logger.warning(f"[first_query] 알 수 없는 state: {state}")
            return {
                "response": "이력서를 다시 작성해주세요.",
                "metadata": {
                    "source": "default",
                    "state": "initial"         # ✅ metadata 안에 포함
                },
                "url": url
            }
        
    async def make_html_ai(self,token,uid):

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
            ("user", "{collected_user_data}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"collected_user_data": description})  # ✅ 이름 일치
            logger.info(f"[AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        
        collected_user_data = await self.user_information.all(uid)
        user_info= await self.user_api.user_api(token)
        preference_info=await self.user_api.user_prefer_api(token)

        description = f"""
        Collected user information : {collected_user_data} 
        Saved user information_1 : {user_info}  
        Saved user information_2 : {preference_info} """ # +  토큰 새로받으면 추가할로직
        logger.info(f"[수집한 정보] {description}")

        response = parse_product(description)

        return response["html"]
    
    async def make_user_data(self,uid,token):

        llm = get_langchain_llm(is_lightweight = False)

        parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "title": {"type":"string"},
            }
        })

        system_prompt = Prompt.make_user_data()

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])

        chain = prompt | llm | parser

        def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})  # ✅ 이름 일치
            logger.info(f"[AI가 반환한값] {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        
        collected_user_data = await self.user_information.all(uid)
        user_info= await self.user_api.user_api(token)
        preference_info=await self.user_api.user_prefer_api(token)

        description = f"""
        Collected user information : {collected_user_data} 
        Saved user information : {user_info} + {preference_info} 
        """ 
        
        logger.info(f"[수집한 정보] {description}")

        response = parse_product(description)

        return response


