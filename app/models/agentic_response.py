from enum import Enum


class AgentType(str, Enum):
    """에이전트 유형"""
    GENERAL = "general"
    CALENDAR = "calendar"
    RESUME = "resume"
    JOB_SEARCH = "job_search"
    COVER_LETTER = "cover_letter"
    POST = "post"
    LOCATION = "location"
    WEATHER = "weather"
    EVENT = "event"
    DOG = "dog"
    CAT = "cat"
    EUM = "eum"

# 게시판 카테고리 모델
# 대분류-소분류 형태
class PostCategory(str, Enum):
    """게시판 카테고리"""
    TRAVEL_EXPERIENCE = "여행-관광/체험"
    TRAVEL_FOOD = "여행-식도락/맛집"
    TRAVEL_REVIEW = "여행-교통/이동"
    TRAVEL_TIP = "여행-숙소/지역정보"
    TRAVEL_PHOTO = "여행-대사관/응급"
    
    RESIDENCE_REAL_ESTATE = "주거-부동산/계약"
    RESIDENCE_LIVING = "주거-생활환경/편의"
    RESIDENCE_CULTURE = "주거-문화/생활"
    RESIDENCE_MAINTENANCE = "주거-주거지 관리/유지"
    

    EDUCATION_ACADEMIC = "유학-학사/캠퍼스"
    EDUCATION_SUPPORT = "유학-학업지원/시설"
    EDUCATION_ADMINISTRATION = "유학-행정/비자/서류"
    EDUCATION_DORMITORY = "유학-기숙사/주거"
    
    EMPLOYMENT_RESUME = "취업-이력/채용준비"
    EMPLOYMENT_VISA = "취업-비자/법률/노동"
    EMPLOYMENT_JOB_FAIR = "취업-잡페어/네트워킹"
    EMPLOYMENT_PART_TIME = "취업-알바/파트타임"

    
    