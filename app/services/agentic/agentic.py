from typing import Dict, Any
from loguru import logger
from app.services.agentic.agentic_classifier import AgenticClassifier
from app.services.agentic.agentic_response_generator import AgenticResponseGenerator
from app.services.common.postprocessor import Postprocessor
from app.services.common.preprocessor import translate_query
# from app.api.v1.agentic import Location
from typing import Optional

class Agentic:
    """에이전트 클래스 - 워크플로우 관리"""
    
    def __init__(self):
        self.classifier = AgenticClassifier()
        self.response_generator = AgenticResponseGenerator()
        self.postprocessor = Postprocessor()
        logger.info("[에이전트] 초기화 완료")
    
    async def get_response(self, query: str, uid: str, token: Optional[str] = None, state: Optional[str] = None, location: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """질의에 대한 응답을 생성합니다."""
        try:
            original_query=query
            logger.info(f"[live_location] {location}")
            logger.info(f"[WORKFLOW] ====== Starting agentic workflow for user {uid} ======")
            logger.info(f"[WORKFLOW] Original query: {query}")
            logger.info(f"[WORKFLOW] Original state: {state}")
            
            # 1. 전처리 (언어 감지 및 번역)  > 수정 완료
            logger.info(f"[WORKFLOW] Step 1: Preprocessing (language detection and translation)")
            translation_result = translate_query(query)
            source_lang = translation_result["lang_code"]
            english_query = translation_result["translated_query"]
            logger.info(f"[에이전트] 언어 감지 완료 - 소스 언어: {source_lang}, 영어 번역: {english_query}")
            
            # 2. 기능 분류 > 수정 완료
            logger.info(f"[WORKFLOW] Step 2: Classification")
            agentic_type = await self.classifier.classify(english_query)
            
            logger.info(f"[에이전트] 에이전틱 유형: {agentic_type}")
            
            # 3. 응답 생성
            logger.info(f"[WORKFLOW] Step 3: Response generation")

            logger.info(f"[응답 생성 live_location] : {location}")

            result = await self.response_generator.generate_response(original_query, english_query, agentic_type, uid, token, state,source_lang,location)

            logger.info(f"[에이전트] 응답 생성 완료 : {result}")

            # result["url"] 예외처리
            if "url" not in result or result["url"] is None:
                result["url"] = "None"

            # state 예외처리
            if result["metadata"].get("state") in [None , "general", "calendar", "post"]:
                result["metadata"]["state"] = "initial"


            
            # 4. 후처리 (원문 언어로 번역)
            logger.info(f"[WORKFLOW] Step 4: Postprocessing (translation back to original language)")
            processed_response = await self.postprocessor.postprocess(result["response"], source_lang, "general")
            result["response"] = processed_response["response"]
            result["metadata"]["translated"] = True
            
            # 5. 응답 데이터 구성

            logger.info(f"[WORKFLOW] 응답 데이터 구성 시작")
            response_data = {
                "response": result["response"],
                "metadata": {
                    "english_query": english_query,
                    "source_lang": source_lang,
                    "agentic_type": agentic_type,
                    "uid": uid,
                    "state": result.get("metadata", {}).get("state", "general")
                },
                "state": result.get("metadata", {}).get("state", "general"),
                "url": result["url"]
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
                    "english_query": english_query,
                    "agentic_type": agentic_type,
                    "state": "error",
                    "uid": uid,
                    "error": str(e)
                }
            } 