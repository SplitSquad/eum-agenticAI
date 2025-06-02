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
    wget \
    curl \
    gnupg \
    libatk-bridge2.0-0 \
    libnss3 \
    libnspr4 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    fonts-liberation \
    libappindicator1 \
    lsb-release \
    libgbm1 \
    libglib2.0-0 \
    libdrm2 \
    libxkbcommon0 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# 브라우저 실행을 위한 사용자 생성 (root로 Playwright 설치 후 권한 이전)
RUN groupadd -r pptruser && useradd -r -g pptruser -G audio,video pptruser \
    && mkdir -p /home/pptruser/Downloads \
    && mkdir -p /home/pptruser/.cache

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 및 브라우저 설치 (root 권한으로)
RUN pip install --no-cache-dir playwright
RUN playwright install --with-deps chromium

# Playwright 브라우저를 사용자 홈으로 복사하고 권한 설정
RUN cp -r /root/.cache/ms-playwright /home/pptruser/.cache/ \
    && chown -R pptruser:pptruser /home/pptruser/.cache \
    && chmod -R 755 /home/pptruser/.cache

# 환경 변수 설정 (사용자 홈 경로로 변경)
ENV PLAYWRIGHT_BROWSERS_PATH=/home/pptruser/.cache/ms-playwright
ENV DISPLAY=:99

# 애플리케이션 코드 복사
COPY . .

# data 디렉토리 미리 생성 및 권한 설정
RUN mkdir -p /app/data \
    && chown -R pptruser:pptruser /app \
    && chmod -R 755 /app/data

# 포트 노출
EXPOSE 8000

# 비root 사용자로 실행
USER pptruser

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
