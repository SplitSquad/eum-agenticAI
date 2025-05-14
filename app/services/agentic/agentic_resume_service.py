from loguru import logger
import json
import os
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
        pass

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
        
    async def make_pdf(original_query,query,uid,token,intention,state):

        return

    