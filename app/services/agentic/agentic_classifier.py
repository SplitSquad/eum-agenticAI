from typing import Dict, Any, Tuple
from enum import Enum
from loguru import logger
from app.core.llm_client import get_llm_client
from app.models.agentic_response import AgentType, ActionType
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()  # .env 파일 자동 로딩
import os
# ✅ .env 파일의 절대 경로 지정
dotenv_path = os.path.join(os.path.dirname(__file__), '../../../.env')
load_dotenv(dotenv_path)
# ✅ 환경변수 읽기
groq_api_key = os.getenv("GROQ_API_KEY")
import json
# 기존: from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

class RAGType(str, Enum):
    """RAG 도메인 유형"""
    VISA_LAW = "visa_law"  # 비자/법률
    SOCIAL_SECURITY = "social_security"  # 사회보장제도
    TAX_FINANCE = "tax_finance"  # 세금/금융
    MEDICAL_HEALTH = "medical_health"  # 의료/건강
    EMPLOYMENT = "employment"  # 취업
    DAILY_LIFE = "daily_life"  # 일상생활

class AgenticType(str, Enum):
    """에이전틱 기능 유형"""
    GENERAL = "general"  # 일반 대화
    SCHEDULE = "schedule"  # 일정 관리
    TODO = "todo"  # 할 일 관리
    MEMO = "memo"  # 메모 관리
    CALENDAR = "calendar"  # 캘린더 관리
    REMINDER = "reminder"  # 알림 관리
    RESUME = "resume" # 이력서 기능
    POST = "post" # 게시판기능

class AgentClassifier:
    """에이전트 분류기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=True)
        logger.info(f"[분류기] 경량 모델 사용: {self.llm_client.model}")
    
    async def classify(self, query: str) -> Dict[str, Any]:
        """
        에이전트 유형, 액션 유형, 도메인을 분류합니다.
        
        Args:
            query: 입력 질의
            
        Returns:
            Dict[str, Any]: 분류 결과
        """
        logger.info(f"[분류기] 질의 분류 시작: {query}")
        
        # 에이전트 유형 분류
        agent_type = await self._classify_agent_type(query)
        logger.info(f"[분류기] 에이전트 유형: {agent_type.value}")
        
        # 필요한 액션 분류
        action_type = await self._classify_action_type(query)
        logger.info(f"[분류기] 액션 유형: {action_type.value}")
        
        # 도메인 분류
        rag_type = await self._classify_rag_type(query)
        logger.info(f"[분류기] RAG 유형: {rag_type.value}")
        
        result = {
            "agent_type": agent_type,
            "action_type": action_type,
            "rag_type": rag_type
        }
        
        logger.info(f"[분류기] 분류 완료: {result}")
        return result
    
    async def _classify_agent_type(self, query: str) -> AgentType:
        """에이전트 유형을 분류합니다."""
        prompt = f"""
        다음 질문을 처리하기 위해 어떤 유형의 에이전트가 필요한지 판단해주세요.
        질문: {query}
        
        다음 중 하나만 답변해주세요:
        - general
        - task
        - domain
        """
        
        try:
            logger.info(f"[분류기] 에이전트 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip().lower()
            logger.info(f"[분류기] 에이전트 유형 분류 결과: {response}")
            
            # 응답에서 키워드 추출
            if "task" in response:
                return AgentType.TASK
            elif "domain" in response:
                return AgentType.DOMAIN
            else:
                return AgentType.GENERAL
                
        except Exception as e:
            logger.error(f"에이전트 유형 분류 중 오류 발생: {str(e)}")
            return AgentType.GENERAL
    
    async def _classify_action_type(self, query: str) -> ActionType:
        """필요한 액션 유형을 분류합니다."""
        prompt = f"""
        다음 질문을 처리하기 위해 어떤 유형의 액션이 필요한지 판단해주세요.
        질문: {query}
        
        다음 중 하나만 답변해주세요:
        - inform
        - execute
        - decide
        """
        
        try:
            logger.info(f"[분류기] 액션 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip().lower()
            logger.info(f"[분류기] 액션 유형 분류 결과: {response}")
            
            # 응답에서 키워드 추출
            if "execute" in response:
                return ActionType.EXECUTE
            elif "decide" in response:
                return ActionType.DECIDE
            else:
                return ActionType.INFORM
                
        except Exception as e:
            logger.error(f"액션 유형 분류 중 오류 발생: {str(e)}")
            return ActionType.INFORM
    
    async def _classify_rag_type(self, query: str) -> RAGType:
        """RAG 유형을 분류합니다."""
        prompt = f"""
        다음 질문이 어떤 도메인에 속하는지 판단해주세요.
        질문: {query}
        
        다음 중 하나만 답변해주세요:
        - visa_law: 비자/법률 관련 질문
        - social_security: 사회보장제도 관련 질문
        - tax_finance: 세금/금융 관련 질문
        - medical_health: 의료/건강 관련 질문
        - employment: 취업 관련 질문
        - daily_life: 일상생활 관련 질문
        """
        
        try:
            logger.info(f"[분류기] RAG 유형 분류 시작")
            response = await self.llm_client.generate(prompt)
            response = response.strip().lower()
            logger.info(f"[분류기] RAG 유형 분류 결과: {response}")
            
            # 응답에서 도메인 추출
            for rag_type in RAGType:
                if rag_type.value in response:
                    return rag_type
            
            # 기본값으로 일상생활 도메인 반환
            return RAGType.DAILY_LIFE
                
        except Exception as e:
            logger.error(f"RAG 유형 분류 중 오류 발생: {str(e)}")
            return RAGType.DAILY_LIFE

class AgenticClassifier:
    """에이전틱 분류기"""
    
    def __init__(self):
        self.llm_client = get_llm_client(is_lightweight=True)
        logger.info(f"[에이전틱 분류] 경량 모델 사용: {self.llm_client.model}")
    
    async def classify(self, query: str) -> AgenticType:
        """
        질의를 분류합니다.
        
        Args:
            query: 사용자 질의
            
        Returns:
            AgenticType: 에이전틱 기능 유형
        """
        try:
            logger.info(f"[에이전틱 분류] 질의 분류 시작: {query}")
            
            # 질의 유형 분류
            agentic_type = await self._classify_agentic_type(query)
            logger.info(f"[에이전틱 분류] 기능 유형: {agentic_type.value}")
            
            return agentic_type
            
        except Exception as e:
            logger.error(f"분류 중 오류 발생: {str(e)}")
            return AgenticType.GENERAL
    
    async def _classify_agentic_type(self, query: str) -> AgenticType:
        """에이전틱 기능 유형을 분류합니다."""
        try:
            # TODO: LLM을 활용한 기능 유형 분류 구현
            # 임시로 모든 질의를 일반 대화로 분류
            # LLM을 통해 카테고리 분류
            category_json = Category_Classification(query)
            category_dict = json.loads(category_json)  # JSON 문자열을 dict로 변환
            category = category_dict["output"]  # output 필드 추출
            
            logger.info(f"[에이전틱 분류] 기능 유형: {category}")

            return AgenticType(category)
        except Exception as e:
            logger.error(f"기능 유형 분류 중 오류 발생: {str(e)}")
            return AgenticType.GENERAL 

################################################### LLM을 활용한 기능 유형 분류 구현     
def Category_Classification(query):
    llm = ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0.7
    )

    parser = JsonOutputParser(pydantic_object={
            "type": "object",
            "properties": {
                "input": {"type": "string"},
                "output": {"type": "string"},
            }
    })
    prompt = ChatPromptTemplate.from_messages([
    ("system", """
    1. Its role is to inform the category.
    2. Here is a few-shot example.
    ----------------------- 
    input : 일정 추가해줘  
    output : calendar

    input : 내일 약속 생겼어  
    output : calendar

    input : 오후 3시에 회의 잡아줘  
    output : calendar

    input : 스케줄 등록해줄래?  
    output : calendar

    input : 약속 변경하고 싶어  
    output : calendar

    input : 내일 점심약속 생겼어  
    output : calendar

    input : 이번 주 금요일에 회식 있어  
    output : calendar

    input : 내 스케줄 확인해줘  
    output : calendar

    input : 새로운 일정 추가하고 싶어  
    output : calendar

    input : 오후 일정 정리해줘  
    output : calendar
    -----------------------
    input : 이력서 작성 부탁해  
    output : resume

    input : 경력사항입니다  
    output : resume

    input : 자기소개는 이렇게 작성했어요  
    output : resume

    input : 학력 정보 추가해줘  
    output : resume

    input : 아래 내용 기반으로 이력서 만들어줘  
    output : resume

    input : 이력서에 기술 스택도 포함해줘  
    output : resume

    input : 내 경력에 맞춰 이력서 구성해줘  
    output : resume

    input : 기본 이력서 양식으로 작성해줘  
    output : resume

    input : 프로젝트 경험을 넣고 싶어  
    output : resume

    input : 이력서 항목 중 자격증도 추가해줘  
    output : resume
    -----------------
    input : 게시글 작성해줘  
    output : post

    input : 블로그 글 하나 올리고 싶어  
    output : post

    input : 새로운 게시물 작성할게  
    output : post

    input : 글쓰기 시작할게  
    output : post

    input : 포스트 등록하고 싶어  
    output : post

    input : 게시판에 글 남길게  
    output : post

    input : 아래 내용을 게시글로 만들어줘  
    output : post

    input : 게시판에 올릴 글입니다  
    output : post

    input : 짧은 글 하나 올릴게요  
    output : post

    input : 사용자 공지 작성 부탁해  
    output : post
    ----------------------- 
    input : 일정 추가해줘  
    output : calendar

    input : 내일 약속 생겼어  
    output : calendar

    input : 오후 3시에 회의 잡아줘  
    output : calendar

    input : 스케줄 등록해줄래?  
    output : calendar

    input : 약속 변경하고 싶어  
    output : calendar

    input : 내일 점심약속 생겼어  
    output : calendar

    input : 이번 주 금요일에 회식 있어  
    output : calendar

    input : 내 스케줄 확인해줘  
    output : calendar

    input : 새로운 일정 추가하고 싶어  
    output : calendar

    input : 오후 일정 정리해줘  
    output : calendar
    -----------------------
    input : 이력서 작성 부탁해  
    output : resume

    input : 경력사항입니다  
    output : resume

    input : 자기소개는 이렇게 작성했어요  
    output : resume

    input : 학력 정보 추가해줘  
    output : resume

    input : 아래 내용 기반으로 이력서 만들어줘  
    output : resume

    input : 이력서에 기술 스택도 포함해줘  
    output : resume

    input : 내 경력에 맞춰 이력서 구성해줘  
    output : resume

    input : 기본 이력서 양식으로 작성해줘  
    output : resume

    input : 프로젝트 경험을 넣고 싶어  
    output : resume

    input : 이력서 항목 중 자격증도 추가해줘  
    output : resume
    -----------------
    input : 게시글 작성해줘  
    output : post

    input : 블로그 글 하나 올리고 싶어  
    output : post

    input : 새로운 게시물 작성할게  
    output : post

    input : 글쓰기 시작할게  
    output : post

    input : 포스트 등록하고 싶어  
    output : post

    input : 게시판에 글 남길게  
    output : post

    input : 아래 내용을 게시글로 만들어줘  
    output : post

    input : 게시판에 올릴 글입니다  
    output : post

    input : 짧은 글 하나 올릴게요  
    output : post

    input : 사용자 공지 작성 부탁해  
    output : post
    ----------------------- 
    input : 일정 추가해줘  
    output : calendar

    input : 내일 약속 생겼어  
    output : calendar

    input : 오후 3시에 회의 잡아줘  
    output : calendar

    input : 스케줄 등록해줄래?  
    output : calendar

    input : 약속 변경하고 싶어  
    output : calendar

    input : 내일 점심약속 생겼어  
    output : calendar

    input : 이번 주 금요일에 회식 있어  
    output : calendar

    input : 내 스케줄 확인해줘  
    output : calendar

    input : 새로운 일정 추가하고 싶어  
    output : calendar

    input : 오후 일정 정리해줘  
    output : calendar
    -----------------------
    input : 이력서 작성 부탁해  
    output : resume

    input : 경력사항입니다  
    output : resume

    input : 자기소개는 이렇게 작성했어요  
    output : resume

    input : 학력 정보 추가해줘  
    output : resume

    input : 아래 내용 기반으로 이력서 만들어줘  
    output : resume

    input : 이력서에 기술 스택도 포함해줘  
    output : resume

    input : 내 경력에 맞춰 이력서 구성해줘  
    output : resume

    input : 기본 이력서 양식으로 작성해줘  
    output : resume

    input : 프로젝트 경험을 넣고 싶어  
    output : resume

    input : 이력서 항목 중 자격증도 추가해줘  
    output : resume
    -----------------
    input : 게시글 작성해줘  
    output : post

    input : 블로그 글 하나 올리고 싶어  
    output : post

    input : 새로운 게시물 작성할게  
    output : post

    input : 글쓰기 시작할게  
    output : post

    input : 포스트 등록하고 싶어  
    output : post

    input : 게시판에 글 남길게  
    output : post

    input : 아래 내용을 게시글로 만들어줘  
    output : post

    input : 게시판에 올릴 글입니다  
    output : post

    input : 짧은 글 하나 올릴게요  
    output : post

    input : 사용자 공지 작성 부탁해  
    output : post
    ----------------------- 
    input : 일정 추가해줘  
    output : calendar

    input : 내일 약속 생겼어  
    output : calendar

    input : 오후 3시에 회의 잡아줘  
    output : calendar

    input : 스케줄 등록해줄래?  
    output : calendar

    input : 약속 변경하고 싶어  
    output : calendar

    input : 내일 점심약속 생겼어  
    output : calendar

    input : 이번 주 금요일에 회식 있어  
    output : calendar

    input : 내 스케줄 확인해줘  
    output : calendar

    input : 새로운 일정 추가하고 싶어  
    output : calendar

    input : 오후 일정 정리해줘  
    output : calendar
    -----------------------
    input : 이력서 작성 부탁해  
    output : resume

    input : 경력사항입니다  
    output : resume

    input : 자기소개는 이렇게 작성했어요  
    output : resume

    input : 학력 정보 추가해줘  
    output : resume

    input : 아래 내용 기반으로 이력서 만들어줘  
    output : resume

    input : 이력서에 기술 스택도 포함해줘  
    output : resume

    input : 내 경력에 맞춰 이력서 구성해줘  
    output : resume

    input : 기본 이력서 양식으로 작성해줘  
    output : resume

    input : 프로젝트 경험을 넣고 싶어  
    output : resume

    input : 이력서 항목 중 자격증도 추가해줘  
    output : resume
    -----------------
    input : 게시글 작성해줘  
    output : post

    input : 블로그 글 하나 올리고 싶어  
    output : post

    input : 새로운 게시물 작성할게  
    output : post

    input : 글쓰기 시작할게  
    output : post

    input : 포스트 등록하고 싶어  
    output : post

    input : 게시판에 글 남길게  
    output : post

    input : 아래 내용을 게시글로 만들어줘  
    output : post

    input : 게시판에 올릴 글입니다  
    output : post

    input : 짧은 글 하나 올릴게요  
    output : post

    input : 사용자 공지 작성 부탁해  
    output : post
    ----------------------- 
    input : 일정 추가해줘  
    output : calendar

    input : 내일 약속 생겼어  
    output : calendar

    input : 오후 3시에 회의 잡아줘  
    output : calendar

    input : 스케줄 등록해줄래?  
    output : calendar

    input : 약속 변경하고 싶어  
    output : calendar

    input : 내일 점심약속 생겼어  
    output : calendar

    input : 이번 주 금요일에 회식 있어  
    output : calendar

    input : 내 스케줄 확인해줘  
    output : calendar

    input : 새로운 일정 추가하고 싶어  
    output : calendar

    input : 오후 일정 정리해줘  
    output : calendar
    -----------------------
    input : 이력서 작성 부탁해  
    output : resume

    input : 경력사항입니다  
    output : resume

    input : 자기소개는 이렇게 작성했어요  
    output : resume

    input : 학력 정보 추가해줘  
    output : resume

    input : 아래 내용 기반으로 이력서 만들어줘  
    output : resume

    input : 이력서에 기술 스택도 포함해줘  
    output : resume

    input : 내 경력에 맞춰 이력서 구성해줘  
    output : resume

    input : 기본 이력서 양식으로 작성해줘  
    output : resume

    input : 프로젝트 경험을 넣고 싶어  
    output : resume

    input : 이력서 항목 중 자격증도 추가해줘  
    output : resume
    -----------------
    input : 게시글 작성해줘  
    output : post

    input : 블로그 글 하나 올리고 싶어  
    output : post

    input : 새로운 게시물 작성할게  
    output : post

    input : 글쓰기 시작할게  
    output : post

    input : 포스트 등록하고 싶어  
    output : post

    input : 게시판에 글 남길게  
    output : post

    input : 아래 내용을 게시글로 만들어줘  
    output : post

    input : 게시판에 올릴 글입니다  
    output : post

    input : 짧은 글 하나 올릴게요  
    output : post

    input : 사용자 공지 작성 부탁해  
    output : post                         
    ----------------------- 
    input : 일정 추가해줘  
    output : calendar

    input : 내일 약속 생겼어  
    output : calendar

    input : 오후 3시에 회의 잡아줘  
    output : calendar

    input : 스케줄 등록해줄래?  
    output : calendar

    input : 약속 변경하고 싶어  
    output : calendar

    input : 내일 점심약속 생겼어  
    output : calendar

    input : 이번 주 금요일에 회식 있어  
    output : calendar

    input : 내 스케줄 확인해줘  
    output : calendar

    input : 새로운 일정 추가하고 싶어  
    output : calendar

    input : 오후 일정 정리해줘  
    output : calendar
    -----------------------
    input : 이력서 작성 부탁해  
    output : resume

    input : 경력사항입니다  
    output : resume

    input : 자기소개는 이렇게 작성했어요  
    output : resume

    input : 학력 정보 추가해줘  
    output : resume

    input : 아래 내용 기반으로 이력서 만들어줘  
    output : resume

    input : 이력서에 기술 스택도 포함해줘  
    output : resume

    input : 내 경력에 맞춰 이력서 구성해줘  
    output : resume

    input : 기본 이력서 양식으로 작성해줘  
    output : resume

    input : 프로젝트 경험을 넣고 싶어  
    output : resume

    input : 이력서 항목 중 자격증도 추가해줘  
    output : resume
    -----------------
    input : 게시글 작성해줘  
    output : post

    input : 블로그 글 하나 올리고 싶어  
    output : post

    input : 새로운 게시물 작성할게  
    output : post

    input : 글쓰기 시작할게  
    output : post

    input : 포스트 등록하고 싶어  
    output : post

    input : 게시판에 글 남길게  
    output : post

    input : 아래 내용을 게시글로 만들어줘  
    output : post

    input : 게시판에 올릴 글입니다  
    output : post

    input : 짧은 글 하나 올릴게요  
    output : post

    input : 사용자 공지 작성 부탁해  
    output : post
    -----------------
    input : all Other query
    output : general
    -----------------
     
    3. Please output it like output



    default.Respond only in JSON format
    
    """),
        ("user", "{input}")
    ])

    def parse_product(description: str) -> dict:
            result = chain.invoke({"input": description})
            
            return json.dumps(result, indent=2,ensure_ascii=False)
    
    

    chain = prompt | llm | parser
    Category = parse_product(query)
    print("[Category] ",Category)
    return Category
################################################### LLM을 활용한 기능 유형 분류 구현