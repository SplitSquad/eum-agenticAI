# app/services/common/preprocessor.py

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
        
        # Extract and process JSON
        parse_start = time.time()
        
        # 정규식을 사용하여 JSON 부분 추출 시도
        json_pattern = r'```(?:json)?\s*({[\s\S]*?})\s*```'
        json_match = re.search(json_pattern, result)
        
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # JSON 코드 블록을 찾지 못한 경우, 일반 json 형태 찾기 시도
            json_pattern = r'({[\s\S]*?})' 
            json_match = re.search(json_pattern, result)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # 기존 로직으로 폴백
                json_str = result.strip().strip("```json").strip("```").strip()
        
        logger.debug(f"[Preprocess] Extracted JSON: {json_str}")
        
        try:
            data = json.loads(json_str)
            parse_time = time.time() - parse_start
            logger.info(f"[Preprocess] JSON parsing time: {parse_time:.2f} seconds")
            
            # Log the preprocessed result
            logger.info(f"[PREPROCESS] Translated query: {data['translated_query']}")
            logger.info(f"[PREPROCESS] Detected language: {data['lang_code']}")
            
            total_time = time.time() - start_time
            logger.info(f"[Preprocess] Total execution time: {total_time:.2f} seconds")
            
            return {
                "translated_query": data["translated_query"],
                "lang_code": data["lang_code"]
            }
        except json.JSONDecodeError as e:
            # 다시 시도: 가능한 문자열 치환을 통해 JSON 형식 수정
            logger.warning(f"[Preprocess] First JSON parsing attempt failed: {str(e)}")
            
            # 따옴표 문제 등을 처리하기 위한 추가 정제
            json_str = json_str.replace('""', '"')  # 중복 따옴표 제거
            json_str = re.sub(r'(?<!\\)"(?=\s*[,}])', '\\"', json_str)  # 닫는 따옴표 누락 수정
            
            try:
                data = json.loads(json_str)
                parse_time = time.time() - parse_start
                logger.info(f"[Preprocess] JSON parsing time after recovery: {parse_time:.2f} seconds")
                
                return {
                    "translated_query": data["translated_query"],
                    "lang_code": data["lang_code"]
                }
            except json.JSONDecodeError:
                # 결국 실패한 경우, 수동으로 필드 추출 시도
                translated_pattern = r'"translated_query"\s*:\s*"([^"]+)"'
                lang_pattern = r'"lang_code"\s*:\s*"([^"]+)"'
                
                translated_match = re.search(translated_pattern, json_str)
                lang_match = re.search(lang_pattern, json_str)
                
                if translated_match and lang_match:
                    return {
                        "translated_query": translated_match.group(1),
                        "lang_code": lang_match.group(1)
                    }
                
                # 여기까지 실패하면 원래 오류 발생
                raise
    except json.JSONDecodeError as e:
        logger.error(f"[Preprocess] Failed to parse translation response JSON: {str(e)}")
        logger.error(f"[Preprocess] Original response: {result}")
        raise ValueError(f"Translation response parsing error: {e}\nOriginal response: {result}")
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Preprocess] Error during translation processing: {str(e)} (Time elapsed: {elapsed:.2f} seconds)")
        raise ValueError(f"Error during translation processing: {str(e)}") 