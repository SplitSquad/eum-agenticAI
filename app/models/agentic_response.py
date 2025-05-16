from enum import Enum


class AgentType(str, Enum):
    """에이전트 유형"""
    GENERAL = "general"
    CALENDAR = "calendar"
    RESUME = "resume"
    JOB_SEARCH = "job_search"
    COVER_LETTER = "cover_letter"
    POST = "post"
