from typing import Dict, Any
from loguru import logger
from app.services.agentic.agentic_classifier import AgenticClassifier, AgenticType
from app.services.agentic.agentic_response_generator import AgenticResponseGenerator
from app.services.common.postprocessor import Postprocessor
from app.services.common.preprocessor import translate_query


class Agentic:
    """에이전트 클래스 - 워크플로우 관리"""
    
    def __init__(self):
        self.classifier = AgenticClassifier()
        self.response_generator = AgenticResponseGenerator()
        self.postprocessor = Postprocessor()
        logger.info("[에이전트] 초기화 완료")
    
    async def get_response(self, query: str, uid: str) -> Dict[str, Any]:
        """질의에 대한 응답을 생성합니다."""
        try:
            logger.info(f"[WORKFLOW] ====== Starting agentic workflow for user {uid} ======")
            logger.info(f"[WORKFLOW] Original query: {query}")
            
            # 1. 전처리 (언어 감지 및 번역)
            logger.info(f"[WORKFLOW] Step 1: Preprocessing (language detection and translation)")
            translation_result = await translate_query(query)
            source_lang = translation_result["lang_code"]
            english_query = translation_result["translated_query"]
            logger.info(f"[에이전트] 언어 감지 완료 - 소스 언어: {source_lang}, 영어 번역: {english_query}")
            
            # 2. 기능 분류
            logger.info(f"[WORKFLOW] Step 2: Classification")
            agentic_type = await self.classifier.classify(english_query)
            logger.info(f"[에이전트] 에이전틱 유형: {agentic_type.value}")
            
            # 3. 응답 생성
            logger.info(f"[WORKFLOW] Step 3: Response generation")
            result = await self.response_generator.generate_response(english_query, agentic_type, uid)
            logger.info("[에이전트] 응답 생성 완료")
            
            # 4. 후처리 (원문 언어로 번역)
            logger.info(f"[WORKFLOW] Step 4: Postprocessing (translation back to original language)")
            if source_lang != "en":
                processed_response = await self.postprocessor.postprocess(result["response"], source_lang, "general")
                result["response"] = processed_response["response"]
                result["metadata"]["translated"] = True
            
            # 5. 응답 데이터 구성
            response_data = {
                "response": result["response"],
                "metadata": {
                    "query": query,
                    "english_query": english_query,
                    "source_lang": source_lang,
                    "agentic_type": agentic_type.value,
                    "uid": uid,
                    "state": result.get("metadata", {}).get("state", "general")
                }
            }
            
            # 메타데이터에 추가 정보가 있으면 병합
            if "metadata" in result:
                response_data["metadata"].update(result["metadata"])
                
            logger.info(f"[WORKFLOW] ====== Agentic workflow completed for user {uid} ======")
            return response_data
            
        except Exception as e:
            logger.error(f"응답 생성 중 오류 발생: {str(e)}")
            logger.error(f"[WORKFLOW] ====== Error in agentic workflow: {str(e)} ======")
            return {
                "response": "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.",
                "metadata": {
                    "query": query,
                    "state": "error",
                    "uid": uid,
                    "error": str(e)
                }
            } 