from typing import Dict, Optional, List
from pydantic import BaseModel
import googleapiclient.discovery
import os
from dotenv import load_dotenv
import logging
import sys
from pathlib import Path

# 21
# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 콘솔 핸들러
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# 파일 핸들러
file_handler = logging.FileHandler('job_search.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 핸들러 추가
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 환경 변수 로드
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.eee'
logger.info(f"환경 변수 파일 경로: {env_path}")
load_dotenv(dotenv_path=env_path)

# 환경 변수 확인
api_key = os.getenv('GOOGLE_SERACH_API_KEY')
search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

logger.info("환경 변수 로드 완료")
logger.info(f"API 키 존재 여부: {api_key is not None}")
logger.info(f"API 키 값: {api_key[:5]}..." if api_key else "None")
logger.info(f"검색 엔진 ID 존재 여부: {search_engine_id is not None}")
logger.info(f"검색 엔진 ID 값: {search_engine_id[:5]}..." if search_engine_id else "None")

class JobSearchState(BaseModel):
    """구직 정보 검색 상태를 관리하는 클래스"""
    is_active: bool = False
    search_keyword: Optional[str] = None
    search_results: List[Dict] = []

class JobSearchConversationState:
    """구직 검색 대화 상태 관리 클래스"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.job_keywords: Optional[str] = None
        self.search_results: List[Dict[str, str]] = []
        self.current_step = "start"

    def update_job_keywords(self, keywords: str):
        """구직 키워드 업데이트"""
        self.job_keywords = keywords
        self.current_step = "search_completed"

    def update_search_results(self, results: List[Dict[str, str]]):
        """검색 결과 업데이트"""
        self.search_results = results
        self.current_step = "results_shown"

async def start_job_search(user_id: str) -> JobSearchState:
    """
    구직 정보 검색을 시작합니다.
    
    Args:
        user_id (str): 사용자 ID
        
    Returns:
        JobSearchState: 구직 정보 검색 상태
    """
    logger.info(f"구직 검색 시작 - 사용자 ID: {user_id}")
    return JobSearchState(is_active=True)

async def process_job_search_response(state: JobSearchConversationState, response: str) -> Dict[str, str]:
    """구직 검색 응답 처리"""
    if state.current_step == "start":
        state.update_job_keywords(response)
        search_results = await search_jobs(response)
        
        return {
            "status": "search_completed",
            "message": "검색 결과를 보여드렸습니다. 자기소개서 작성을 도와드릴까요?",
            "search_results": search_results,
            "job_keywords": response
        }
    

    
    return {
        "status": "error",
        "message": "잘못된 응답입니다."
    }

def extract_keyword(response: str) -> Optional[str]:
    """
    사용자의 응답에서 검색 키워드를 추출합니다.
    
    Args:
        response (str): 사용자의 응답
        
    Returns:
        Optional[str]: 추출된 키워드
    """
    logger.info(f"키워드 추출 시도 - 응답: {response}")
    
    # 키워드 추출 로직
    # 예: "네 요리분야에서 일하고 싶어요" -> "요리"
    # 예: "네 개발자로 일하고 싶어요" -> "개발자"
    
    # 한국어 키워드 추출 패턴들
    patterns = [
        ("분야에서", "분야"),
        ("로 일", "로"),
        ("으로 일", "으로"),
        ("로서 일", "로서"),
        ("으로서 일", "으로서")
    ]
    # 위 키워드 추출은 llm 경량 모델 base로 분류 
    
    response = response.replace("네,", "네").replace("yes,", "yes")  # 쉼표 제거
    
    for pattern, suffix in patterns:
        if pattern in response:
            parts = response.split(pattern)
            if len(parts) > 1:
                keyword = parts[0].strip()
                # "네" 또는 "yes" 제거
                keyword = keyword.replace("네", "").replace("yes", "").strip()
                # 접미사 제거
                if keyword.endswith(suffix):
                    keyword = keyword[:-len(suffix)].strip()
                logger.info(f"한국어 키워드 추출 성공: {keyword}")
                return keyword
    
    # 영어 키워드 추출
    if "field" in response:
        parts = response.split("field")
        if len(parts) > 1:
            keyword = parts[0].strip()
            keyword = keyword.replace("yes", "").strip()
            logger.info(f"영어 키워드 추출 성공: {keyword}")
            return keyword
            
    logger.info("키워드 추출 실패")
    return None

async def search_job_listings(keyword: str) -> List[Dict]:
    """
    구글 검색 API를 사용하여 구직 정보를 검색합니다.
    
    Args:
        keyword (str): 검색 키워드
        
    Returns:
        List[Dict]: 검색 결과
    """
    try:
        # 구글 검색 API 설정
        api_key = os.getenv("GOOGLE_SERACH_API_KEY")  
        search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        logger.info(f"API 키 존재 여부: {api_key is not None}")
        logger.info(f"검색 엔진 ID 존재 여부: {search_engine_id is not None}")
        
        if not api_key or not search_engine_id:
            logger.error("API 키 또는 검색 엔진 ID가 설정되지 않았습니다.")
            return []
        
        logger.info("Google API 서비스 빌드 시작")
        service = googleapiclient.discovery.build(
            "customsearch", "v1", developerKey=api_key
        )
        
        # 검색 쿼리 구성
        query = f"{keyword} 구인구직 채용"
        logger.info(f"검색 쿼리: {query}")
        
        # 검색 실행
        logger.info("검색 API 호출 시작")
        result = service.cse().list(
            q=query,
            cx=search_engine_id,
            num=5  # 상위 5개 결과만 가져옴
        ).execute()
        
        logger.info(f"검색 결과: {result}")
        
        # 결과 처리
        search_results = []
        if 'items' in result:
            for item in result['items']:
                search_results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                })
            logger.info(f"검색 결과 처리 완료 - 결과 수: {len(search_results)}")
        else:
            logger.warning("검색 결과에 'items' 키가 없습니다.")
        
        return search_results
        
    except Exception as e:
        logger.error(f"구직 정보 검색 중 오류 발생: {str(e)}", exc_info=True)
        return [] 