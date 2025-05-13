from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import time
from loguru import logger
from app.config.app_config import settings, LLMProvider

class BaseLLMClient(ABC):
    """LLM 클라이언트의 기본 추상 클래스"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """프롬프트를 기반으로 텍스트를 생성합니다."""
        pass
    
    @abstractmethod
    async def check_connection(self) -> bool:
        """LLM 서버 연결 상태를 확인합니다."""
        pass

class GroqClient(BaseLLMClient):
    """Groq API 클라이언트"""
    
    def __init__(self, is_lightweight: bool = True):
        self.is_lightweight = is_lightweight
        self.api_key = settings.GROQ_API_KEY
        
        if is_lightweight:
            self.model = settings.GROQ_LIGHTWEIGHT_MODEL
            self.timeout = 30  # 경량 모델 기본 타임아웃
            logger.info(f"[GroqClient] 경량 모델 초기화 완료: MODEL={self.model}, TIMEOUT={self.timeout}초")
        else:
            self.model = settings.GROQ_HIGHPERFORMANCE_MODEL
            self.timeout = 60  # 고성능 모델 기본 타임아웃
            logger.info(f"[GroqClient] 고성능 모델 초기화 완료: MODEL={self.model}, TIMEOUT={self.timeout}초")
        
        self.base_url = "https://api.groq.com/openai/v1"
        
        if not self.api_key:
            raise ValueError("Groq API 키가 설정되지 않았습니다.")
    
    async def check_connection(self) -> bool:
        """Groq 서버 연결 상태를 확인합니다."""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(f"{self.base_url}/models", headers=headers)
                response.raise_for_status()
                elapsed = time.time() - start_time
                model_type = "경량" if self.is_lightweight else "고성능"
                logger.info(f"[Groq {model_type}] 연결 확인 시간: {elapsed:.2f}초")
                return True
        except Exception as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[Groq {model_type}] 서버 연결 실패: {str(e)} (소요 시간: {elapsed:.2f}초)")
            return False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Groq API를 사용하여 텍스트를 생성합니다."""
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                request_start = time.time()
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                request_time = time.time() - request_start
                model_type = "경량" if self.is_lightweight else "고성능"
                logger.info(f"[Groq {model_type}] API 요청 시간: {request_time:.2f}초")
                
                response.raise_for_status()
                result = response.json()["choices"][0]["message"]["content"]
                
                total_time = time.time() - start_time
                logger.info(f"[Groq {model_type}] 전체 생성 시간: {total_time:.2f}초")
                return result
        except httpx.TimeoutException as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[Groq {model_type}] 요청 타임아웃: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise TimeoutError(f"Groq 서버 응답 시간 초과 (타임아웃: {self.timeout}초)")
        except httpx.RequestError as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[Groq {model_type}] 요청 실패: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise ConnectionError(f"Groq 서버 요청 실패: {str(e)}")
        except Exception as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[Groq {model_type}] 예상치 못한 오류: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise ValueError(f"Groq 처리 중 오류 발생: {str(e)}")

class OllamaClient(BaseLLMClient):
    """Ollama API 클라이언트"""
    
    def __init__(self, is_lightweight: bool = True):
        self.is_lightweight = is_lightweight
        if is_lightweight:
            self.base_url = settings.LIGHTWEIGHT_OLLAMA_URL
            self.model = settings.LIGHTWEIGHT_OLLAMA_MODEL
            self.timeout = settings.LIGHTWEIGHT_OLLAMA_TIMEOUT
            logger.info(f"[OllamaClient] 경량 모델 초기화 완료: URL={self.base_url}, MODEL={self.model}, TIMEOUT={self.timeout}초")
        else:
            self.base_url = settings.HIGH_PERFORMANCE_OLLAMA_URL
            self.model = settings.HIGH_PERFORMANCE_OLLAMA_MODEL
            self.timeout = settings.HIGH_PERFORMANCE_OLLAMA_TIMEOUT
            logger.info(f"[OllamaClient] 고성능 모델 초기화 완료: URL={self.base_url}, MODEL={self.model}, TIMEOUT={self.timeout}초")
        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"
    
    async def check_connection(self) -> bool:
        """Ollama 서버 연결 상태를 확인합니다."""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.tags_url)
                response.raise_for_status()
                elapsed = time.time() - start_time
                model_type = "경량" if self.is_lightweight else "고성능"
                logger.info(f"[Ollama {model_type}] 연결 확인 시간: {elapsed:.2f}초")
                return True
        except Exception as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[Ollama {model_type}] 서버 연결 실패: {str(e)} (소요 시간: {elapsed:.2f}초)")
            return False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Ollama API를 사용하여 텍스트를 생성합니다."""
        start_time = time.time()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                request_start = time.time()
                response = await client.post(self.generate_url, json=payload)
                request_time = time.time() - request_start
                model_type = "경량" if self.is_lightweight else "고성능"
                logger.info(f"[Ollama {model_type}] API 요청 시간: {request_time:.2f}초")
                
                response.raise_for_status()
                result = response.json()["response"]
                
                total_time = time.time() - start_time
                logger.info(f"[Ollama {model_type}] 전체 생성 시간: {total_time:.2f}초")
                return result
        except httpx.TimeoutException as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[Ollama {model_type}] 요청 타임아웃: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise TimeoutError(f"Ollama 서버 응답 시간 초과 (타임아웃: {self.timeout}초)")
        except httpx.RequestError as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[Ollama {model_type}] 요청 실패: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise ConnectionError(f"Ollama 서버 요청 실패: {str(e)}")
        except Exception as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[Ollama {model_type}] 예상치 못한 오류: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise ValueError(f"Ollama 처리 중 오류 발생: {str(e)}")

class OpenAIClient(BaseLLMClient):
    """OpenAI API 클라이언트"""
    
    def __init__(self, is_lightweight: bool = True):
        self.is_lightweight = is_lightweight
        if is_lightweight:
            self.api_key = settings.LIGHTWEIGHT_OPENAI_API_KEY
            self.model = settings.LIGHTWEIGHT_OPENAI_MODEL
            self.timeout = settings.LIGHTWEIGHT_OPENAI_TIMEOUT
        else:
            self.api_key = settings.HIGH_PERFORMANCE_OPENAI_API_KEY
            self.model = settings.HIGH_PERFORMANCE_OPENAI_MODEL
            self.timeout = settings.HIGH_PERFORMANCE_OPENAI_TIMEOUT
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
    
    async def check_connection(self) -> bool:
        """OpenAI 서버 연결 상태를 확인합니다."""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(f"{self.base_url}/models", headers=headers)
                response.raise_for_status()
                elapsed = time.time() - start_time
                model_type = "경량" if self.is_lightweight else "고성능"
                logger.info(f"[OpenAI {model_type}] 연결 확인 시간: {elapsed:.2f}초")
                return True
        except Exception as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[OpenAI {model_type}] 서버 연결 실패: {str(e)} (소요 시간: {elapsed:.2f}초)")
            return False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """OpenAI API를 사용하여 텍스트를 생성합니다."""
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                request_start = time.time()
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                request_time = time.time() - request_start
                model_type = "경량" if self.is_lightweight else "고성능"
                logger.info(f"[OpenAI {model_type}] API 요청 시간: {request_time:.2f}초")
                
                response.raise_for_status()
                result = response.json()["choices"][0]["message"]["content"]
                
                total_time = time.time() - start_time
                logger.info(f"[OpenAI {model_type}] 전체 생성 시간: {total_time:.2f}초")
                return result
        except httpx.TimeoutException as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[OpenAI {model_type}] 요청 타임아웃: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise TimeoutError(f"OpenAI 서버 응답 시간 초과 (타임아웃: {self.timeout}초)")
        except httpx.RequestError as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[OpenAI {model_type}] 요청 실패: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise ConnectionError(f"OpenAI 서버 요청 실패: {str(e)}")
        except Exception as e:
            elapsed = time.time() - start_time
            model_type = "경량" if self.is_lightweight else "고성능"
            logger.error(f"[OpenAI {model_type}] 예상치 못한 오류: {str(e)} (소요 시간: {elapsed:.2f}초)")
            raise ValueError(f"OpenAI 처리 중 오류 발생: {str(e)}")

def get_llm_client(is_lightweight: bool = True) -> BaseLLMClient:
    """
    설정된 LLM 프로바이더에 따라 적절한 클라이언트를 반환합니다.
    
    Args:
        is_lightweight (bool): 경량 모델 사용 여부 (기본값: True)
    """
    provider = settings.LIGHTWEIGHT_LLM_PROVIDER if is_lightweight else settings.HIGH_PERFORMANCE_LLM_PROVIDER
    
    if provider == LLMProvider.OLLAMA:
        return OllamaClient(is_lightweight=is_lightweight)
    elif provider == LLMProvider.OPENAI:
        return OpenAIClient(is_lightweight=is_lightweight)
    elif provider == LLMProvider.GROQ:
        return GroqClient(is_lightweight=is_lightweight)
    else:
        raise ValueError(f"지원하지 않는 LLM 프로바이더: {provider}") 