# EUM Chatbot

이음 챗봇은 외국인을 위한 종합 정보 제공 챗봇 서비스입니다. 다양한 도메인의 전문 지식을 제공하며, RAG(Retrieval-Augmented Generation) 기술을 활용하여 정확하고 신뢰할 수 있는 정보를 제공합니다.

## 주요 기능

- 다국어 지원 (한국어, 영어 등)
- 도메인별 전문 지식 제공
  - 비자/법률 (VISA_LAW)
  - 사회보장제도 (SOCIAL_SECURITY)
  - 세금/금융 (TAX_FINANCE)
  - 의료/건강 (MEDICAL_HEALTH)
  - 취업 (EMPLOYMENT)
  - 일상생활 (DAILY_LIFE)
- RAG 기반 정확한 정보 제공
- 추론 기반 복잡한 질문 처리

## 프로젝트 구조

```
eum-chatbot/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── chatbot.py      # 챗봇 API 엔드포인트
│   │       └── agentic.py      # 에이전트 API 엔드포인트
│   ├── core/
│   │   └── llm_client.py       # LLM 클라이언트
│   ├── services/
│   │   ├── chatbot/            # 챗봇 관련 서비스
│   │   │   ├── chatbot.py
│   │   │   ├── chatbot_classifier.py
│   │   │   └── chatbot_rag_service.py
│   │   ├── agentic/            # 에이전트 관련 서비스
│   │   │   ├── agentic.py
│   │   │   └── agentic_classifier.py
│   │   └── common/             # 공통 서비스
│   │       ├── preprocessor.py
│   │       └── postprocessor.py
│   ├── config/
│   │   └── rag_config.py       # RAG 설정
│   └── main.py                 # FastAPI 애플리케이션
├── tests/                      # 테스트 코드
├── logs/                       # 로그 파일
├── .env                        # 환경 변수
└── requirements.txt            # 의존성 목록
```

## 개발 환경 설정

### 1. Python 환경 설정

```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. Ollama 설정

Ollama는 LLM 모델을 로컬에서 실행하기 위한 도구입니다.

```bash
# Ollama 설치 (Mac)
brew install ollama

# Ollama 서버 실행
ollama serve

# 필요한 모델 다운로드
ollama pull gemma3:1b  # 경량 모델
ollama pull gemma3:12b  # 고성능 모델
```

### 3. 서버 실행

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일을 수정하여 필요한 설정을 입력

# 서버 실행
PYTHONPATH=$PYTHONPATH:. uvicorn app.main:app --reload
```

## API 엔드포인트

### 챗봇 API

```
POST /api/v1/chatbot
Content-Type: application/json

{
    "query": "건강보험 자격 취득은 어떻게 하나요?",
    "uid": "user_id"
}
```

### 에이전트 API

```
POST /api/v1/agentic
Content-Type: application/json

{
    "query": "건강보험 자격 취득은 어떻게 하나요?",
    "uid": "user_id"
}
```

## 코드 컨벤션

### 1. 디렉토리 구조
- `app/`: 애플리케이션 코드
  - `api/`: API 엔드포인트
  - `core/`: 핵심 기능
  - `services/`: 비즈니스 로직
    - `chatbot/`: 챗봇 관련 서비스
    - `agentic/`: 에이전트 관련 서비스
    - `common/`: 공통 서비스
  - `config/`: 설정 파일

### 2. 파일 명명 규칙
- Python 파일: snake_case.py
- 클래스: PascalCase
- 함수/변수: snake_case
- 상수: UPPER_SNAKE_CASE

### 3. 코드 스타일
- PEP 8 준수
- 타입 힌트 사용
- docstring 작성
- 로깅 활용

### 4. 로깅
- `loguru` 라이브러리 사용
- 로그 레벨: DEBUG, INFO, WARNING, ERROR
- 로그 포맷: `[모듈명] 메시지`

## 테스트

```bash
# 테스트 실행
pytest tests/
```

## 서버 실행 방법

```bash
# 백그라운드 실행
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/uvicorn.log 2>&1 &

# 서버 종료
ps aux | grep uvicorn      # 실행 중인 프로세스 확인
kill -9 [PID]              # 프로세스 종료
```

서버 실행 중 로그는 `logs/` 디렉토리에서 확인할 수 있습니다.