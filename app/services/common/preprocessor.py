from typing import Dict
import json
import time
import re
from loguru import logger
from app.core.llm_client import get_llm_client
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """You are a language detection and translation expert. You MUST:
1. Return ONLY valid JSON
2. Use the exact format specified
3. Never include any other text or explanation
4. Never use markdown formatting or code blocks
5. Always translate non-English text to English
6. If input is English, return it as is"""

USER_PROMPT = """Detect the language of this query and translate it to English if it's not English.

Input query: "{query}"

Return ONLY this JSON structure:
{{
  "translated_query": "query in English (keep as is if already English)",
  "lang_code": "two-letter code (ko/en/ja/zh)",
  "is_english": true/false
}}"""

async def translate_query(query: str) -> Dict[str, str]:
    """
    Translates the given query to English and returns language code.

    Args:
        query (str): The query text to translate

    Returns:
        Dict[str, str]: Dictionary containing:
                        - 'translated_query': Query translated to English (or original if English)
                        - 'lang_code': IETF language code of original language (e.g., 'ko' for Korean)
                        - 'is_english': Boolean indicating if original query was English
    """
    start_time = time.time()
    
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
        
        # Prepare prompt
        prompt = f"{SYSTEM_PROMPT}\n\n{USER_PROMPT.format(query=query)}"
        
        # Translation request
        gen_start = time.time()
        result = await llm_client.generate(prompt=prompt)
        gen_time = time.time() - gen_start
        logger.info(f"[Preprocess] LLM generation time: {gen_time:.2f} seconds")
        
        # Log raw response for debugging
        logger.info("=" * 50)
        logger.info("[Preprocess] Raw LLM response:")
        logger.info(result)
        logger.info("=" * 50)
        
        try:
            # Clean and extract JSON
            result = result.strip()
            json_pattern = r'\{[^{}]*\}'
            json_match = re.search(json_pattern, result)
            
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                # Validate required fields
                if not all(key in data for key in ["translated_query", "lang_code", "is_english"]):
                    raise ValueError("Missing required fields in JSON response")
                
                response = {
                    "translated_query": data["translated_query"].strip(),
                    "lang_code": data["lang_code"].lower().strip(),
                    "is_english": data.get("is_english", False)
                }
                
                logger.info(f"[Preprocess] Successful translation: {response}")
                return response
            else:
                raise ValueError("No JSON object found in response")
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"[Preprocess] Error parsing response: {str(e)}")
            logger.error(f"[Preprocess] Raw response: {result}")
            
            # If the input looks like English, return it as is
            if re.match(r'^[a-zA-Z\s\'",.!?-]+$', query):
                return {
                    "translated_query": query,
                    "lang_code": "en",
                    "is_english": True
                }
            # Otherwise, assume Korean
            return {
                "translated_query": query,
                "lang_code": "ko",
                "is_english": False
            }
            
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Preprocess] Error during translation: {str(e)} (Time: {elapsed:.2f}s)")
        
        # If the input looks like English, return it as is
        if re.match(r'^[a-zA-Z\s\'",.!?-]+$', query):
            return {
                "translated_query": query,
                "lang_code": "en",
                "is_english": True
            }
        # Otherwise, assume Korean
        return {
            "translated_query": query,
            "lang_code": "ko",
            "is_english": False
        } 