from typing import Dict, Any
from loguru import logger
import json


def merge_user_metadata(user_dict: dict, prefer_dict: dict) -> dict:
    return {
        "name": user_dict.get("name"),
        "birth_date": user_dict.get("birthday"),
        "phone": user_dict.get("phoneNumber"),
        "email": user_dict.get("email"),
        "address": user_dict.get("address"),
        "nation": prefer_dict.get("nation")
    }

class AgenticResume():
    def __init__(self):

        # 2. 백엔드에서 api 요청해서 필요한 정보 불러오기
        ## 일단은 더미데이터를 불러옴
        self.user_data: Dict[str, Dict[str, str]] = {}

        # 더미 사용자 정보 파싱 (추후엔 API로 교체)
        user = """{
        "userId": 1,
        "email": "example@email.com",
        "name": "홍길동",
        "phoneNumber" : "010-4017-2871",
        "birthday" : "1999-10-02",
        "profileImagePath": "https://path.to/profile.jpg",
        "address": "서울특별시 강남구",
        "signedAt": "2025-04-28T12:00:00",
        "isDeactivate": false,
        "role": "ROLE_USER"
        }
        """
    
        user_prefer = """{
        "preferenceId": 1,
        "userId": 1,
        "nation": "KOREA",
        "language": "KO",
        "gender": "MALE",
        "visitPurpose": "Travel",
        "period": "1 month",
        "onBoardingPreference": "{}",
        "isOnBoardDone": true,
        "createdAt": "2025-04-28T11:02:25.150532",
        "updatedAt": "2025-04-28T17:17:28.062318"
        }"""

        parsed_user = json.loads(user)
        parsed_prefer = json.loads(user_prefer)

        self.default_user_info = merge_user_metadata(parsed_user, parsed_prefer)    

    # 1. 사용자 입력 수집
    async def collect_user_input(self, query: str, state: str, uid: str) -> Dict[str, Any]:
        if uid not in self.user_data:
            self.user_data[uid] = {}
        data = self.user_data[uid]

        ### 학력 및 자격사항 수집 (최대 5개)
        if state.startswith("ask_edu"):
            state = "ask_edu_0"
            try:
                idx_str = state.split("_")[-1]
                idx = int(idx_str)
            except ValueError:
                logger.error(f"[STATE 파싱 실패] state: '{state}' → 인덱스를 추출할 수 없습니다.")
                return {
                    "response": "상태 정보에 문제가 발생했습니다. 다시 시도해 주세요.",
                    "state": "error",
                }

            if "education" not in data:
                data["education"] = []

            if query.strip().lower() == "없음":
                next_state = "ask_career_0"
                data["certifications"] = []
                message = "경력사항이 있다면 기간을 입력해 주세요. (또는 '없음')"
            else:
                while len(data["education"]) <= idx:
                    data["education"].append({})
                current = data["education"][idx]

                if "period" not in current:
                    current["period"] = query
                    next_state = f"ask_edu_{idx}_school"
                    message = "학교명 또는 자격증명을 입력해 주세요."
                elif "school" not in current:
                    current["school"] = query
                    next_state = f"ask_edu_{idx}_major"
                    message = "전공을 입력해 주세요. (없으면 '없음')"
                elif "major" not in current:
                    current["major"] = query
                    next_state = f"ask_edu_{idx}_degree"
                    message = "학위 또는 자격 정보를 입력해 주세요. (없으면 '없음')"
                elif "degree" not in current:
                    current["degree"] = query
                    next_state = f"ask_edu_{idx}_issuer"
                    message = "발급 기관 또는 학교를 입력해 주세요. (없으면 '없음')"
                elif "issuer" not in current:
                    current["issuer"] = query
                    next_state = f"ask_edu_{idx}_grade"
                    message = "성적 또는 점수를 입력해 주세요. (없으면 '없음')"
                elif "grade" not in current:
                    current["grade"] = query
                    if idx < 4:
                        next_state = f"ask_edu_{idx + 1}"
                        message = "다음 학력/자격사항의 기간을 입력해 주세요. (없으면 '없음')"
                    else:
                        next_state = "ask_career_0"
                        message = "경력사항이 있다면 기간을 입력해 주세요. (또는 '없음')"

        ### 경력사항 수집 (최대 5개)
        elif state.startswith("ask_career_"):
            try:
                idx_str = state.split("_")[-1]
                idx = int(idx_str)
            except ValueError:
                logger.error(f"[STATE 파싱 실패] state: '{state}' → 인덱스를 추출할 수 없습니다.")
                return {
                    "response": "상태 정보에 문제가 발생했습니다. 다시 시도해 주세요.",
                    "state": "error",
                }

            if "career" not in data:
                data["career"] = []

            if query.strip().lower() == "없음":
                next_state = "complete"
                message = "입력해주셔서 감사합니다. 이력서를 생성 중입니다."
            else:
                while len(data["career"]) <= idx:
                    data["career"].append({})
                current = data["career"][idx]

                if "period" not in current:
                    current["period"] = query
                    next_state = f"ask_career_{idx}_company"
                    message = "근무하신 회사명을 입력해 주세요."
                elif "company" not in current:
                    current["company"] = query
                    next_state = f"ask_career_{idx}_position"
                    message = "직책을 입력해 주세요."
                elif "position" not in current:
                    current["position"] = query
                    next_state = f"ask_career_{idx}_description"
                    message = "업무 내용을 간단히 적어 주세요."
                elif "description" not in current:
                    current["description"] = query
                    if idx < 4:
                        next_state = f"ask_career_{idx + 1}"
                        message = "다음 경력사항의 기간을 입력해 주세요. (없으면 '없음')"
                    else:
                        next_state = "complete"
                        message = "입력해주셔서 감사합니다. 이력서를 생성 중입니다."

        else:
            logger.error(f"[STATE 오류] 잘못된 state가 전달되었습니다: {state}")
            return {
                "response": "상태 오류입니다. 다시 시도해 주세요.",
                "state": "error",
                "data": data,
                "url": None
            }



        logger.info(f"[현재까지 저장된 데이터 for {uid}] : {json.dumps(data, ensure_ascii=False, indent=2)}")

        return {
            "response": message,
            "state": next_state,
            "data": data,
            "url": None  # 혹은 "" 로 해도 무방
        }

    
        

    # 3 ai에게 정보 가공해달라고하기.

    # 4. html 코드에 알맞게 붙히기

    # 5. pdf로 만들기

    # 6. S3로 넘김

    # 7. 반환해주기 