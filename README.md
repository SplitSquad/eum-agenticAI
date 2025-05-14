# EUM Agentic AI Service

외국인을 위한 커뮤니티 서비스 EUM의 AI 기능을 담당하는 서비스입니다.

## 프로젝트 구조

```
app/
├── core/
│   ├── llm_client.py        # LLM 클라이언트 설정 (Groq, OpenAI)
│   └── llm_post_prompt.py   # 프롬프트 템플릿 관리
├── services/
│   └── agentic/
│       ├── agentic_post.py  # 게시글 생성 에이전트
│       ├── agentic_resume.py # 이력서 작성 에이전트
│       └── agentic_cover_letter.py # 자기소개서 작성 에이전트
└── tests/
    └── services/
        └── agentic/
            └── test_agentic_post.py # 게시글 에이전트 테스트
```

## 기능

### 1. 게시글 자동 생성 및 분류

사용자의 입력을 바탕으로 적절한 카테고리를 선택하고 게시글을 자동으로 작성합니다.

#### 카테고리 구조

- 여행
  - 관광/체험
  - 식도락/맛집
  - 교통/이동
  - 숙소/지역
  - 대사관/응급

- 주거
  - 부동산/계약
  - 생활환경/편의
  - 문화/생활
  - 주거지 관리/유지

- 유학
  - 학사/캠퍼스
  - 학업지원
  - 행정/비자/서류
  - 기숙사/주거

- 취업
  - 이력/채용
  - 비자/법률/노동
  - 잡페어/네트워킹
  - 알바/파트타임

### API 요청 구조

#### 게시글 생성 API

```python
POST /community/post
Headers:
  - Authorization: <token>

Request Body (multipart/form-data):
{
    "content": "게시글 내용",
    "mainCategory": "대분류",
    "tags": ["소분류"]
}

Response:
{
    "success": true
}
```

## 환경 설정

1. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
# .env 파일 생성
LIGHTWEIGHT_LLM_PROVIDER=groq  # or openai
GROQ_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key
```

## 테스트

테스트는 pytest를 사용하여 작성되었습니다.

```bash
# 전체 테스트 실행
python -m pytest

# 특정 테스트 실행
python -m pytest tests/services/agentic/test_agentic_post.py -v
```

### 테스트 작성 가이드

1. 새로운 테스트 파일 생성 시 `tests/` 디렉토리 내 동일한 구조로 생성
2. 테스트 함수는 `test_` 접두사로 시작
3. 비동기 테스트는 `@pytest.mark.asyncio` 데코레이터 사용
4. Mock 객체 사용 시 `unittest.mock` 활용

예시:
```python
@pytest.mark.asyncio
@patch('app.services.agentic.agentic_post.get_langchain_llm')
async def test_something(mock_get_llm):
    mock_llm = Mock()
    mock_get_llm.return_value = mock_llm
    mock_llm.invoke = Mock(return_value=Mock(content="..."))
    # 테스트 로직
```

## TODO

1. 이력서 생성 기능 리팩토링
   - `agentic_resume.py` 파일 구조 개선
   - 템플릿 기반 응답 구조화
   - 테스트 코드 작성

2. 자기소개서 생성 기능 리팩토링
   - `agentic_cover_letter.py` 파일 구조 개선
   - 맞춤형 프롬프트 템플릿 작성
   - 테스트 코드 작성

## 기여 가이드

1. 새로운 기능 개발 시 테스트 코드 필수 작성
2. PR 전 로컬에서 전체 테스트 통과 확인
3. 코드 스타일은 black 포맷터 사용
4. 문서화 주석 필수 작성