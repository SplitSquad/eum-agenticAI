from typing import List, Optional, Dict
from loguru import logger
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from app.config.rag_config import RAGConfig
from app.services.chatbot.chatbot_classifier import RAGType

class RAGService:
    """RAG 서비스"""
    
    def __init__(self):
        self.config = RAGConfig()
        self.embeddings = SentenceTransformer(self.config.EMBEDDING_MODEL)
        logger.info(f"[RAG] 임베딩 모델 사용: {self.config.EMBEDDING_MODEL}")
        
        # 도메인별 ChromaDB 클라이언트 초기화
        self.clients: Dict[RAGType, chromadb.PersistentClient] = {}
        self.collections: Dict[RAGType, chromadb.Collection] = {}
        
        for rag_type, config in self.config.DOMAIN_CONFIGS.items():
            try:
                # 도메인별 ChromaDB 클라이언트 생성
                client = chromadb.PersistentClient(
                    path=config["vectorstore_path"],
                    settings=Settings(allow_reset=True)
                )
                self.clients[rag_type] = client
                
                # 도메인별 컬렉션 초기화
                try:
                    self.collections[rag_type] = client.get_collection(config["collection_name"])
                except ValueError:
                    self.collections[rag_type] = client.create_collection(config["collection_name"])
                
                logger.info(f"[RAG] {rag_type.value} 도메인 초기화 완료: {config['vectorstore_path']}")
            except Exception as e:
                logger.error(f"[RAG] {rag_type.value} 도메인 초기화 중 오류 발생: {str(e)}")
    
    def add_documents(self, rag_type: RAGType, documents: List[str]) -> None:
        """
        특정 도메인의 문서를 벡터 DB에 추가합니다.
        
        Args:
            rag_type: RAG 유형
            documents: 추가할 문서 리스트
        """
        try:
            logger.info(f"[RAG] {rag_type.value} 도메인에 문서 추가 시작: {len(documents)}개")
            
            # 문서 임베딩 생성
            embeddings = self.embeddings.encode(documents)
            
            # 문서 ID 생성
            doc_ids = [f"doc_{i}" for i in range(len(documents))]
            
            # 컬렉션에 문서 추가
            self.collections[rag_type].add(
                embeddings=embeddings.tolist(),
                documents=documents,
                ids=doc_ids
            )
            
            logger.info(f"[RAG] {rag_type.value} 도메인에 {len(documents)}개의 문서가 추가되었습니다.")
        except Exception as e:
            logger.error(f"문서 추가 중 오류 발생: {str(e)}")
            raise
    
    async def search(self, rag_type: RAGType, query: str) -> List[str]:
        """
        특정 도메인에서 질의와 관련된 문서를 검색합니다.
        
        Args:
            rag_type: RAG 유형
            query: 검색 질의
            
        Returns:
            List[str]: 검색된 문서 리스트
        """
        try:
            logger.info(f"[RAG] {rag_type.value} 도메인에서 문서 검색 시작: {query}")
            
            # 질의 임베딩 생성
            query_embedding = self.embeddings.encode([query])[0]
            
            # 유사도 검색
            results = self.collections[rag_type].query(
                query_embeddings=[query_embedding.tolist()],
                n_results=self.config.SEARCH_K
            )
            
            # 임계값 이상의 문서만 반환
            filtered_docs = []
            for doc, score in zip(results['documents'][0], results['distances'][0]):
                if score >= self.config.SEARCH_THRESHOLD:
                    filtered_docs.append(doc)
            
            logger.info(f"[RAG] {rag_type.value} 도메인에서 {len(filtered_docs)}개의 문서가 검색되었습니다.")
            for i, doc in enumerate(filtered_docs):
                logger.info(f"[RAG] 문서 {i+1}: {doc[:100]}...")
            
            return filtered_docs
        except Exception as e:
            logger.error(f"문서 검색 중 오류 발생: {str(e)}")
            return []
    
    async def get_context(self, rag_type: RAGType, query: str) -> str:
        """
        특정 RAG 유형에서 질의에 대한 컨텍스트를 생성합니다.
        
        Args:
            rag_type: RAG 유형
            query: 질의
            
        Returns:
            str: 생성된 컨텍스트
        """
        try:
            logger.info(f"[RAG] {rag_type.value} 유형에서 컨텍스트 생성 시작")
            
            if rag_type == RAGType.NONE:
                logger.info("[RAG] RAG 유형이 NONE이므로 컨텍스트를 생성하지 않습니다.")
                return ""
            
            # 관련 문서 검색
            docs = await self.search(rag_type, query)
            
            if not docs:
                logger.info("[RAG] 관련 문서가 없습니다.")
                return ""
            
            # 컨텍스트 생성
            context = "\n\n".join(docs)
            logger.info(f"[RAG] 컨텍스트 생성 완료: {len(context)}자")
            
            return context
        except Exception as e:
            logger.error(f"컨텍스트 생성 중 오류 발생: {str(e)}")
            return "" 