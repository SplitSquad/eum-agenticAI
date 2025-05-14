
from typing import Dict
import json
import time
import re
from loguru import logger
from app.core.llm_client import get_llm_client

PROMPT_TEMPLATE = """
Detect the language of the following query, then translate it to English.

Return the result ONLY in this JSON format:

```json
{{
  "translated_query": "...",
  "lang_code": "..."
}}
Query: "{query}" """

async def translate_query(query: str) -> Dict[str, str]:
    """
    Translates the given query to English and returns language code.

    Args:
        query (str): The query text to translate

    Returns:
        Dict[str, str]: Dictionary containing 'translated_query' and 'lang_code'
                        - 'translated_query': Query translated to English
                        - 'lang_code': IETF language code of original language (e.g., 'ko' for Korean)

    Raises:
        ValueError: When translation response cannot be parsed
    """
    start_time = time.time()
    result = None
    
    try:
        # Log original query
        logger.info(f"[PREPROCESS] Original query: {query}")
        
        # Initialize lightweight model client
        init_start = time.time()
        llm_client = get_llm_client(is_lightweight=True)
        init_time = time.time() - init_start
        logger.info(f"[Preprocess] Client initialization time: {init_time:.2f} seconds")
        logger.info(f"[Preprocess] Model used: {llm_client.model}")
        
        # Check server connection
        conn_start = time.time()
        if not await llm_client.check_connection():
            raise ConnectionError("Failed to connect to LLM server")
        conn_time = time.time() - conn_start
        logger.info(f"[Preprocess] Server connection check time: {conn_time:.2f} seconds")
        
        # Translation request
        gen_start = time.time()
        result = await llm_client.generate(
            prompt=PROMPT_TEMPLATE.format(query=query)
        )
        gen_time = time.time() - gen_start
        logger.info(f"[Preprocess] LLM generation time: {gen_time:.2f} seconds")
        
        # Extract and process response
        parse_start = time.time()
        
        # 1. JSON 형식으로 파싱 시도
        try:
            # 정규식을 사용하여 JSON 부분 추출
            json_pattern = r'```(?:json)?\s*({[\s\S]*?})\s*```'
            json_match = re.search(json_pattern, result)
            
            if json_match:
                json_str = json_match.group(1).strip()
                data = json.loads(json_str)
                return {
                    "translated_query": data["translated_query"],
                    "lang_code": data["lang_code"]
                }
        except (json.JSONDecodeError, AttributeError):
            logger.warning("[Preprocess] JSON parsing failed, trying text extraction")
        
        # 2. 텍스트에서 번역 정보 추출
        try:
            # 번역된 쿼리 추출
            translated_pattern = r'Translated to English:\s*"([^"]+)"'
            translated_match = re.search(translated_pattern, result, re.IGNORECASE)
            
            # 언어 코드 추출
            lang_pattern = r'language of the query is (\w+)'
            lang_match = re.search(lang_pattern, result, re.IGNORECASE)
            
            if translated_match and lang_match:
                translated_query = translated_match.group(1)
                lang = lang_match.group(1).lower()
                
                # 언어 코드 매핑
                lang_code_map = {
                    "korean": "ko",
                    "english": "en",
                    "japanese": "ja",
                    "chinese": "zh",
                    "vietnamese": "vi",
                    "thai": "th"
                }
                
                lang_code = lang_code_map.get(lang, "en")  # 기본값은 영어
                
                return {
                    "translated_query": translated_query,
                    "lang_code": lang_code
                }
        except Exception as e:
            logger.warning(f"[Preprocess] Text extraction failed: {str(e)}")
        
        # 3. 최후의 수단: 원본 쿼리를 그대로 사용하고 한국어로 가정
        logger.warning("[Preprocess] Falling back to original query")
        return {
            "translated_query": query,
            "lang_code": "ko"
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Preprocess] Error during translation processing: {str(e)} (Time elapsed: {elapsed:.2f} seconds)")
        raise ValueError(f"Error during translation processing: {str(e)}") 