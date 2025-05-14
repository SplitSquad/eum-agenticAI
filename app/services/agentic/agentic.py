from typing import Dict, Any
from loguru import logger
from app.services.agentic.agentic_classifier import AgenticClassifier, AgenticType
from app.services.agentic.agentic_response_generator import AgenticResponseGenerator
from app.services.common.postprocessor import Postprocessor
from app.services.common.preprocessor import translate_query
from typing import Optional
import json

class Agentic:
    """에이전트 클래스 - 워크플로우 관리"""
    
    def __init__(self):
        self.classifier = AgenticClassifier()
        self.response_generator = AgenticResponseGenerator()
        self.postprocessor = Postprocessor()
        logger.info("[에이전트] 초기화 완료")
    
    async def get_response(self, query: str, uid: str, token: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """질의에 대한 응답을 생성합니다."""
        try:
            original_query = query
            agentic_type = AgenticType.GENERAL  # 기본값 설정
            translation_result = {"lang_code": "ko", "translated_query": query, "is_english": False}  # 기본값 설정
            
            logger.info("=" * 80)
            logger.info(f"[WORKFLOW START] User: {uid}")
            logger.info(f"[INPUT] Original Query: {query}")
            if token:
                masked_token = token[:6] + "..." + token[-4:]
                logger.info(f"[AUTH] Token: {masked_token}")
            logger.info(f"[STATE] Current State: {state}")
            
            # 1. 전처리 (언어 감지 및 번역)
            logger.info("\n" + "=" * 40)
            logger.info("[STEP 1] Preprocessing - Language Detection & Translation")
            logger.info(f"[LLM INPUT] Query for translation: {query}")
            
            translation_result = await translate_query(query)
            source_lang = translation_result["lang_code"]
            english_query = translation_result["translated_query"]
            is_english = translation_result.get("is_english", False)
            
            logger.info("[LLM OUTPUT] Translation Result:")
            logger.info(f"  - Source Language: {source_lang}")
            logger.info(f"  - Translated Query: {english_query}")
            logger.info(f"  - Is English: {is_english}")
            
            # 2. 기능 분류 (영어로 된 쿼리 사용)
            logger.info("\n" + "=" * 40)
            logger.info("[STEP 2] Query Classification")
            logger.info(f"[LLM INPUT] Query for classification: {english_query}")
            
            agentic_type = await self.classifier.classify(english_query)
            
            logger.info("[LLM OUTPUT] Classification Result:")
            logger.info(f"  - Agentic Type: {agentic_type.value}")
            
            # 3. 응답 생성 (영어로 된 쿼리 사용)
            logger.info("\n" + "=" * 40)
            logger.info("[STEP 3] Response Generation")
            logger.info("[LLM INPUT] Parameters for response generation:")
            logger.info(f"  - Original Query: {original_query}")
            logger.info(f"  - English Query: {english_query}")
            logger.info(f"  - Agentic Type: {agentic_type.value}")
            
            result = await self.response_generator.generate_response(
                original_query=original_query,  # 항상 원본 쿼리 사용
                english_query=english_query,
                agentic_type=agentic_type,
                uid=uid,
                token=token,
                state=state
            )
            
            logger.info("[LLM OUTPUT] Generated Response:")
            logger.info(f"  - Response: {result['response'][:200]}..." if len(result['response']) > 200 else f"  - Response: {result['response']}")
            logger.info(f"  - Metadata: {json.dumps(result.get('metadata', {}), indent=2, ensure_ascii=False)}")
            
            # 4. 후처리 (원문 언어로 번역)
            if not is_english and source_lang != "en":
                logger.info("\n" + "=" * 40)
                logger.info("[STEP 4] Postprocessing - Translation Back to Original Language")
                logger.info(f"[LLM INPUT] Text for translation: {result['response'][:200]}...")
                
                processed_response = await self.postprocessor.postprocess(result["response"], source_lang, "general")
                result["response"] = processed_response["response"]
                result["metadata"]["translated"] = True
                
                logger.info("[LLM OUTPUT] Final Translated Response:")
                logger.info(f"  - Response: {result['response'][:200]}...")
            
            # 5. 응답 데이터 구성
            response_data = {
                "response": result["response"],
                "metadata": {
                    "query": original_query,  # 원본 쿼리 사용
                    "english_query": english_query,
                    "source_lang": source_lang,
                    "agentic_type": agentic_type.value,
                    "uid": uid,
                    "state": result.get("metadata", {}).get("state", "general"),
                    "is_english": is_english
                }
            }
            
            # 메타데이터에 추가 정보가 있으면 병합
            if "metadata" in result:
                response_data["metadata"].update(result["metadata"])
            
            logger.info("\n" + "=" * 40)
            logger.info("[WORKFLOW COMPLETE] Response ready for delivery")
            logger.info("=" * 80 + "\n")
            
            return response_data
            
        except Exception as e:
            logger.error("\n" + "=" * 40)
            logger.error(f"[ERROR] Error in agentic workflow")
            logger.error(f"  - Error Type: {type(e).__name__}")
            logger.error(f"  - Error Message: {str(e)}")
            logger.error(f"  - Query: {query}")
            logger.error(f"  - User ID: {uid}")
            logger.error("=" * 80 + "\n")
            
            return {
                "response": "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.",
                "metadata": {
                    "query": original_query,  # 원본 쿼리 사용
                    "english_query": translation_result.get("translated_query", query),
                    "source_lang": translation_result.get("lang_code", "ko"),
                    "agentic_type": agentic_type.value,  # 분류된 타입 유지
                    "uid": uid,
                    "state": "error",
                    "error": str(e),
                    "is_english": translation_result.get("is_english", False)
                }
            } 