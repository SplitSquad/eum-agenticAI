from enum import Enum

class RAGType(str, Enum):
    """RAG 유형"""
    NONE = "none"
    DOMAIN_SPECIFIC = "domain_specific"
    GENERAL = "general"

class ResponseType(str, Enum):
    """응답 유형"""
    GENERAL = "general"  # 일반 LLM 응답
    REASONING = "reasoning"  # 추론이 필요한 응답
    WEB_SEARCH = "web_search"  # 웹 검색이 필요한 응답
    RAG = "rag"  # RAG 기반 응답

class QueryType(str, Enum):
    """질의 유형"""
    GENERAL = "general"  # 일반 질문
    REASONING = "reasoning"  # 추론이 필요한 질문
    SEARCH = "search"  # 검색이 필요한 질문
    DOMAIN_SPECIFIC = "domain_specific"  # 특정 도메인 관련 질문 