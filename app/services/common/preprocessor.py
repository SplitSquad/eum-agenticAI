# app/services/common/preprocessor.py
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
import json
from langchain_openai import ChatOpenAI
from app.core.llm_client import get_langchain_llm
from loguru import logger


def translate_query(query: str): 
    llm = get_langchain_llm(is_lightweight=True)

    parser = JsonOutputParser(pydantic_object={
        "type": "object",
        "properties": {
            "lang_code": {"type": "string"},
            "translated_query": {"type": "string"}
        }
    })

    # 시스템 프롬프트 구성
    system_prompt = """
    You are an AI assistant that detects the language of the input and translates it into English.

    Your task is to:
    1. Detect the original language of the input query.
    2. Translate the input accurately into English.
    3. Return the result strictly in this JSON format:

    {{
    "translated_query": "<English translation of the input>",
    "lang_code": "<language code of the original input>"
    }}

    Supported language codes for "lang_code" are:
    - "ko": Korean
    - "en": English
    - "ja": Japanese
    - "zh": Chinese
    - "es": Spanish
    - "fr": French
    - "de": German
    - "ru": Russian

    ⚠️ Do not include any explanation, markdown, or comments. Return **only** the JSON object above.
    """



    
    logger.info("[TRANSLATE] System prompt: {}", system_prompt)
    logger.info("[TRANSLATE] User query: {}", query)

    # ChatPromptTemplate 생성
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ])

    # Chain 구성
    chain = prompt | llm | parser

    try:
        # chain 실행
        result = chain.invoke({})  # 입력이 이미 메시지에 포함되어 있으므로 빈 딕셔너리 전달
        logger.info("[TRANSLATE] Output: {}", result)
        return result
    except Exception as e:
        logger.error("[TRANSLATE] Error: {}", str(e))
        return {
            "translated_query": query,
            "lang_code": "en"  # 에러 발생시 기본값으로 영어 설정
        }

