from typing import Dict, Any
from loguru import logger
import json
from pydantic import BaseModel
from typing import TypedDict, List, Optional
from typing import Dict, List, Any, Optional


class ResumeRequest(BaseModel):
    """이력서 생성 요청 모델"""
    response: str

class EducationInfo(TypedDict):
    period: str
    school: str
    major: str
    degree: str

class MilitaryInfo(TypedDict):
    period: str
    branch: str
    rank: str
    discharge: str

class CertificationInfo(TypedDict):
    period: str
    name: str
    issuer: str
    grade: str

class CareerInfo(TypedDict):
    period: str
    company: str
    position: str
    description: str

# 필요한 정보 목록
REQUIRED_FIELDS = {
    'birth_date': '생년월일',
    'education': '학력',
    'military_service': '병역',
    'certifications': '자격사항',
    'career': '경력사항'
}

async def process_resume_response(*args, **kwargs):
    return {"message": "이력서 응답 처리 성공"}

async def test_resume_generation():
    """이력서 생성 테스트 함수"""
    try:
        # 1. HTML 생성
        pdf_form = await make_pdf("test", TEST_USER_DATA)
        
        # 2. 출력 디렉토리 생성
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. PDF 저장
        output_path = os.path.join(output_dir, "test_resume.pdf")
        await save_html_to_pdf(pdf_form, output_path)
        
        logger.info(f"✅ 테스트 이력서가 생성되었습니다: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {str(e)}")
        raise

class ResumeConversationState:
    """이력서 생성 대화 상태 관리 클래스 (대화형)"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_step: str = "start"  # start -> edu_cert -> career -> completed
        self.edu_cert_input: Optional[str] = None
        self.career_input: Optional[str] = None
        self.education: Optional[list] = None
        self.certifications: Optional[list] = None
        self.career: Optional[list] = None
        self.is_completed: bool = False
        self.user_data: Optional[Dict[str, Any]] = None

    async def initialize(self, authorization: str, user_email: str, request: ResumeRequest) -> None:
        """사용자 프로필 정보 초기화"""
        try:
            # 사용자 프로필 정보 가져오기
            logger.info("[ 사용자 프로필 정보 백으로 api 요청중...] ")
            self.user_data = await get_user_profile(user_email)
            
            # 필요한 정보 요청
            logger.info("[ 필요한 프로필 정보 백으로 api 요청중...] ")
            missing_fields = await check_missing_info(self.user_data)
            
            if missing_fields:
                for field in missing_fields:
                    question = await ask_for_missing_info(field)
                    response = request.response
                    result = await process_user_response(field, response)
                    self.user_data[field] = result
            
        except Exception as e:
            logger.error(f"초기화 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"초기화 실패: {str(e)}"
            )

    async def missing_info(self, authorization: str, user_email: str, request: ResumeRequest) -> None:
        """필요한 정보 요청"""
        try:
            # 필요한 정보 요청
            logger.info("[ 필요한 프로필 정보 백으로 api 요청중...] ")
            missing_fields = await check_missing_info(self.user_data)
            
            if missing_fields:
                for field in missing_fields:
                    question = await ask_for_missing_info(field)
                    response = request.response
                    result = await process_user_response(field, response)
                    self.user_data[field] = result
            
        except Exception as e:
            logger.error(f"필요한 정보 요청 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"필요한 정보 요청 실패: {str(e)}"
            )

async def start_resume_conversation(user_id: str) -> ResumeConversationState:
    state = ResumeConversationState(user_id)
    return state

async def get_resume_question(state: ResumeConversationState) -> str:
    if state.current_step == "start":
        state.current_step = "edu_cert"
        return "학력과 자격사항을 한 번에 입력해 주세요.\n예시: 2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격"
    elif state.current_step == "edu_cert":
        return "학력과 자격사항을 한 번에 입력해 주세요.\n예시: 2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격"
    elif state.current_step == "career":
        return "경력사항을 모두 입력해 주세요.\n예시: 2016-2018 네이버 소프트웨어 엔지니어(검색 엔진 개발), 2018-2020 카카오 시니어 개발자(메시징 플랫폼 개발)"
    else:
        return "이력서 정보가 모두 입력되었습니다."

async def process_resume_conversation_response(state: ResumeConversationState, response: str) -> dict:
    """사용자 응답 처리 및 상태 전이"""
    if state.current_step == "edu_cert":
        state.edu_cert_input = response
        # OpenAI 파싱
        result = await parse_edu_cert_with_openai(response)
        state.education = result.get("education", [])
        state.certifications = result.get("certifications", [])
        state.current_step = "career"
        return {"message": "경력사항을 모두 입력해 주세요. 예시: 2016-2018 네이버 소프트웨어 엔지니어(검색 엔진 개발)", "state": state}
    elif state.current_step == "career":
        state.career_input = response
        # OpenAI 파싱
        result = await parse_career_with_openai(response)
        state.career = result
        state.current_step = "completed"
        state.is_completed = True
        return {"message": "이력서 정보가 모두 입력되었습니다.", "state": state}
    else:
        return {"message": "이미 이력서 정보가 모두 입력되었습니다.", "state": state}

async def get_user_profile(user_id: str) -> Dict[str, str]:
    """실제 백엔드 API를 통해 사용자 프로필 정보를 가져옵니다."""
    try:
        # 테스트용 데이터 사용
        user_data = {
            'userId': 'test123',
            'email': 'test@test.com',
            'name': '홍길동',
            'nation': '대한민국',
            'gender': '남자',
            'language': '한국어',
            'purpose': '취업',
            'birth_date': '1990-01-01',
            'phone': '010-1234-5678',
            'address': '서울시 강남구'
        }
        return user_data
            
    except Exception as e:
        logger.error(f"🚨 사용자 프로필 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사용자 프로필 조회 중 오류 발생: {str(e)}"
        )

async def check_missing_info(user_data: Dict[str, str]) -> List[str]:
    """부족한 정보를 확인합니다."""
    missing_fields = []
    for field, description in REQUIRED_FIELDS.items():
        if not user_data.get(field):
            missing_fields.append(description)
    return missing_fields

async def ask_for_missing_info(field: str) -> str:
    """AI가 부족한 정보에 대해 질문하고 응답을 받습니다."""
    client = get_llm_client(is_lightweight=True)
    
    field_prompts = {
        'education': """
        사용자의 학력 정보가 필요합니다.
        다음 정보를 순서대로 물어보세요:
        1. 기간 (입학년월 ~ 졸업년월)
        2. 학교명
        3. 전공
        4. 학위
        """,
        'military_service': """
        사용자의 병역 정보가 필요합니다.
        다음 정보를 순서대로 물어보세요:
        1. 기간 (입대년월 ~ 전역년월)
        2. 군종
        3. 계급
        4. 전역사유
        """,
        'certifications': """
        사용자의 자격사항 정보가 필요합니다.
        다음 정보를 순서대로 물어보세요:
        1. 취득일
        2. 자격증명
        3. 발급기관
        4. 등급
        """,
        'career': """
        사용자의 경력사항 정보가 필요합니다.
        다음 정보를 순서대로 물어보세요:
        1. 기간 (입사년월 ~ 퇴사년월)
        2. 회사명
        3. 직위
        4. 담당업무
        """
    }
    
    prompt = field_prompts.get(field, f"""
    사용자의 {field} 정보가 필요합니다.
    사용자에게 {field}에 대해 자연스럽게 질문해주세요.
    질문은 한 문장으로 간단하게 작성해주세요.
    """)
    
    question = await client.generate(prompt)
    return question.strip()

async def process_user_response(field: str, response: str) -> Dict[str, Any]:
    """사용자의 응답을 처리하고 구조화된 데이터로 변환합니다."""
    client = get_llm_client(is_lightweight=True)
    
    field_prompts = {
        '학력': f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "period": "2018.03 ~ 2022.02",
            "school": "서울대학교",
            "major": "컴퓨터공학과",
            "degree": "학사"
        }}
        """,
        '병역': f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "period": "2022.03 ~ 2023.12",
            "branch": "육군",
            "rank": "병장",
            "discharge": "만기제대"
        }}
        """,
        '자격사항': f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "period": "2022.03",
            "name": "정보처리기사",
            "issuer": "한국산업인력공단",
            "grade": "합격"
        }}
        """,
        '경력사항': f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "period": "2024.01 ~ 현재",
            "company": "삼성전자",
            "position": "선임연구원",
            "description": "AI 알고리즘 개발"
        }}
        """
    }
    
    prompt = field_prompts.get(field)
    if not prompt:
        prompt = f"""
        다음 응답을 분석하여 JSON 형식으로 변환해주세요:
        {response}

        다음 JSON 형식으로만 응답해주세요:
        {{
            "{field}": "구조화된 데이터"
        }}
        """
    
    try:
        llm_response = await client.generate(prompt)
        logger.info(f"📝 LLM 응답: {llm_response}")
        
        # JSON 문자열에서 실제 JSON 부분만 추출
        import re, json
        json_match = re.search(r'\{[^}]*\}', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # 작은따옴표를 큰따옴표로 변환
            json_str = json_str.replace("'", '"')
            # 줄바꿈과 공백 제거
            json_str = re.sub(r'\s+', '', json_str)
            try:
                data = json.loads(json_str)
                logger.info(f"✅ {field} 데이터 구조화 완료: {data}")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 오류: {str(e)}")
                logger.error(f"❌ 원본 JSON 문자열: {json_str}")
                # 기본값 반환
                return {field: response}
        else:
            logger.error(f"❌ JSON 형식의 응답을 찾을 수 없음: {llm_response}")
            # 기본값 반환
            return {field: response}
    except Exception as e:
        logger.error(f"🚨 응답 처리 중 오류 발생: {str(e)}")
        # 기본값 반환
        return {field: response}

########################################################## 이력서 추가정보

########################################################## """이력서 생성 대화 시작"""
async def start_resume_conversation(authotization, user_email, request) -> ResumeConversationState:
    
    state = ResumeConversationState(user_email)

    # 1. 사용자 프로필 정보 가져오기
    logger.info("[ 사용자 프로필 정보 백으로 api 요청중...] ")
    await state.initialize(authotization, user_email, request)
    logger.info(f"[ 📊 사용자 프로필 정보 ] {state.user_data} ")
    
    # 2. 필요한 정보 요청
    logger.info("[ 필요한 프로필 정보 백으로 api 요청중...] ")
    await state.missing_info(authotization, user_email, request)
    logger.info(f"[ 📊 추가된 프로필 정보 ] {state.user_data} ")
    
    return state
########################################################## """이력서 생성 대화 시작"""

########################################################## job_resume조건문
async def job_resume(query: str, uid: str, state: str, token: str) -> Dict[str, Any]:
    authotization = token
    user_email = uid
    pre_state = state
    logger.info(f"[job_resume parameter] : {authotization} , {user_email} , {pre_state}")

    ## 첫번째 응답 - 학력/자격사항 질문
    if pre_state == "first":
        logger.info("[first_response] - 학력/자격사항 질문")
        return {
            "response": "학력과 자격사항을 입력해주세요.\n예시: 2010-2014 서울대학교 컴퓨터공학과 학사, 2015 정보처리기사(한국산업인력공단) 합격",
            "state": "second"
        }
    
    ## 두번째 응답 - 경력사항 질문
    elif pre_state == "second":
        logger.info("[second_response] - 경력사항 질문")
        request = ResumeRequest(response=query)
        try:
            # 이력서 생성 초기화
            logger.info("[이력서 생성 초기화]")
            resume_state = await start_resume_conversation(authotization, user_email, request)
            
            # 학력/자격사항 파싱
            edu_cert_result = await parse_edu_cert_with_openai(query)
            resume_state.user_data['education'] = edu_cert_result.get('education', [])
            resume_state.user_data['certifications'] = edu_cert_result.get('certifications', [])
            
            # 상태 저장
            conversation_states[user_email] = resume_state
            
            return {
                "response": "경력사항을 입력해주세요.\n예시: 2016-2018 네이버 소프트웨어 엔지니어(검색 엔진 개발), 2018-2020 카카오 시니어 개발자(메시징 플랫폼 개발)",
                "state": "third"
            }
            
        except Exception as e:
            logger.error(f"이력서 생성 시작 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    
    ## 세번째 응답 - 이력서 생성 및 S3 업로드
    elif pre_state == "third":
        logger.info("[third_response] - 이력서 생성 및 S3 업로드")
        try:
            # 저장된 상태 가져오기
            resume_state = conversation_states.get(user_email)
            if not resume_state:
                raise HTTPException(
                    status_code=400,
                    detail="이력서 생성 세션이 만료되었습니다. 처음부터 다시 시작해주세요."
                )
            
            # 경력사항 파싱
            career_result = await parse_career_with_openai(query)
            resume_state.user_data['career'] = career_result
            
            # 이력서 PDF 생성
            logger.info("[AI가 이력서 PDF 만드는중...]")
            pdf_form = await make_pdf(resume_state, resume_state.user_data)

            output_dir = os.path.join(os.getcwd(), "app/services/agentic/resume")
            os.makedirs(output_dir, exist_ok=True)

            # 저장할 파일 전체 경로
            output_path = os.path.join(output_dir, "resume.pdf")
            await save_html_to_pdf(pdf_form, output_path)

            # S3 업로드
            logger.info("[upload_to_s3] 파일 업로드 시작")
            s3_url = upload_to_s3(output_path, "pdfs/resume.pdf")
            logger.info(f"[S3 업로드] : {s3_url}")

            # 상태 제거
            del conversation_states[user_email]

            return {
                "response": "이력서가 생성되었습니다.",
                "state": "first",
                "message": "PDF가 업로드되었습니다.",
                "download_url": s3_url     
            }
            
        except Exception as e:
            logger.error(f"이력서 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    else:
        logger.error("잘못된 상태입니다.")
        return {
            "response": "잘못된 상태입니다.",
            "state": "error"
        }
########################################################## job_resume조건문

########################################################## 이력서 생성 환경설정
from pydantic import BaseModel    
class ResumeResponse(BaseModel):
    """이력서 생성 응답 모델"""
    status: str
    message: Optional[str] = None
    question: Optional[str] = None
    field: Optional[str] = None
    pdf_path: Optional[str] = None

# 대화 상태 저장소 (실제 프로덕션에서는 Redis나 DB를 사용해야 함)
conversation_states: Dict[str, ResumeConversationState] = {}
########################################################## 이력서 생성 환경설정

########################################################## 이력서 작성 시작 API
async def start_resume(state: str) -> Dict[str, str]:
    """이력서 생성 대화 시작"""
    logger.info("[사용자에게 이력서 요청을 보냄...] ")

    response = "본인을 어필해주세요 (사용 가능한 기술 , 수상경력 , 성격 등 )"
    new_state = "second"

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