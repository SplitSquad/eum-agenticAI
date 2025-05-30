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
# 환경 변수 설정
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ENV DISPLAY=:99
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=true
# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Playwright 및 브라우저 설치
RUN pip install --no-cache-dir playwright
RUN playwright install --with-deps chromium
# 브라우저 실행을 위한 권한 설정
RUN groupadd -r pptruser && useradd -r -g pptruser -G audio,video pptruser \
    && mkdir -p /home/pptruser/Downloads \
    && chown -R pptruser:pptruser /home/pptruser \
    && chown -R pptruser:pptruser /root/.cache/ms-playwright
# 애플리케이션 코드 복사
COPY . .
# 앱 디렉토리 권한 설정
RUN chown -R pptruser:pptruser /app
# 포트 노출
EXPOSE 8000
# 비root 사용자로 실행
USER pptruser
# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]