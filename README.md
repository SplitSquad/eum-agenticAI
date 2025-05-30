## 📘 EUM Agentic
EUM Agentic은 외국인을 대상으로 다양한 편리한 서비스를 에이전틱(Agentic) 방식으로 제공하는 스마트 챗봇입니다.

## ✨ 주요 기능
1. 일반 질의 응답
외국인이 궁금해하는 다양한 질문에 대해 친절하고 신속하게 답변합니다.

2. 이력서 생성
간편한 입력만으로 이력서(Resume)를 자동으로 생성하고 편집할 수 있습니다.

3. 캘린더 일정 등록
대화형으로 일정을 받아 Google Calendar에 바로 등록할 수 있습니다.

4. 게시판 글 작성
게시판에 필요한 글을 작성하고 업로드하는 기능을 지원합니다.


## 프로젝트 구조

```
eum-chatbot/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── agentic.py      # 에이전트 API 엔드포인트
│   ├── core/
│   │   └── llm_client.py       # LLM 클라이언트
│   ├── services/   
│   │   ├── agentic/            # 에이전트 관련 서비스
│   │   │   ├── agentic_calendar.py
│   │   │   ├── agentic_classifier.py
│   │   │   ├── agentic_response_generator.py
│   │   │   ├── agentic.py
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

# 의존성 설치 ( + 윈도우의 경우 의존성 설치전 c++ build tool을 설치해야합니다. | visual studio )
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
uvicorn app.main:app --reload 

mac,linux ( 백그라운드 실행 ) 
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/uvicorn.log 2>&1 &

윈도우( 개발모드 )
uvicorn app.main:app --reload

서버 종료
ps aux | grep uvicorn      # 실행 중인 프로세스 확인
kill -9 [PID]              # 프로세스 종료
```
```

## API 엔드포인트


✅ api 명세서
| 엔드포인트           | 메서드 | 설명             | 요청 파라미터                         | 응답 데이터 (예상)                      |
|---------------------|--------|------------------|---------------------------------------|----------------------------------------|
| `/api/v1/agentic`    | POST   | 에이전트 응답 생성 | `{ "query": "string", "uid": "string" }` | `{ "response": "string", "metadata": { ... } }` |


✅ 요청 예시

{
    "query":"건강보험 자격 취득은 어떻게 하나요?",
    "uid":"user_id"
}


✅ 응답 예시

{
    "response": "건강보험 자격 취득은 사업장 가입자는 입사일 기준으로 자동 등록됩니다.",
    "metadata": {
        "query": "건강보험 자격 취득은 어떻게 하나요?",
        "state": "general",
        "uid": "user_id",
        "error": ""
    }
}

## 코드 컨벤션

### 1. 디렉토리 구조
- `app/`: 애플리케이션 코드
  - `api/`: API 엔드포인트
  - `core/`: 핵심 기능
  - `services/`: 비즈니스 로직
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
mac,linux ( 백그라운드 실행 ) 
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/uvicorn.log 2>&1 &

윈도우( 개발모드 )
uvicorn app.main:app --reload

# 서버 종료
ps aux | grep uvicorn      # 실행 중인 프로세스 확인
kill -9 [PID]              # 프로세스 종료
```

서버 실행 중 로그는 `logs/` 디렉토리에서 확인할 수 있습니다.