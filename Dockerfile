FROM python:3.10-slim
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Dockerfile 내부에 반드시 포함
RUN apt-get update && \
    apt-get install -y wget curl gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 libxshmfence1 libxss1 libgtk-3-0 && \
    npm ci && \
    npx playwright install --with-deps

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 애플리케이션 코드 복사
COPY . .
# 포트 노출
EXPOSE 8000
# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]