import logging
import os
import sys
from pathlib import Path

from loguru import logger

# 로그 디렉토리 생성
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 로그 파일 경로
LOG_FILE_APP = LOG_DIR / "app.log"
LOG_FILE_SERVER = LOG_DIR / "server.log"
LOG_FILE_ERROR = LOG_DIR / "error.log"
LOG_FILE_ACCESS = LOG_DIR / "access.log"

# 로그 포맷
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
LOG_FORMAT_ERROR = "<red>{time:YYYY-MM-DD HH:mm:ss.SSS}</red> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>\n{exception}"
LOG_FORMAT_ACCESS = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {extra[client_ip]} | {extra[method]} | {extra[endpoint]} | {extra[status_code]} | {message}"


class InterceptHandler(logging.Handler):
    """
    표준 라이브러리 로깅용 인터셉트 핸들러
    표준 라이브러리 로깅을 로구루로 리디렉션합니다.
    """

    def emit(self, record):
        # 내부 메시지 스킵
        if record.name.startswith("uvicorn."):
            return

        # LogRecord.getMessage() 실행
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 로구루로 기록
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # 적절한 로거를 찾아 메시지 기록
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    """
    애플리케이션 로깅 설정
    """
    # 로구루 설정 초기화
    logger.remove()

    # 콘솔 로거 추가 (에러만)
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level="INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 애플리케이션 로그 파일
    logger.add(
        LOG_FILE_APP,
        format=LOG_FORMAT,
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        backtrace=True,
        diagnose=True,
    )

    # 에러 로그 파일
    logger.add(
        LOG_FILE_ERROR,
        format=LOG_FORMAT_ERROR,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        backtrace=True,
        diagnose=True,
    )

    # 서버 로그 파일
    logger.add(
        LOG_FILE_SERVER,
        format=LOG_FORMAT,
        level="DEBUG",
        filter=lambda record: "uvicorn" in record["name"],
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )

    # 액세스 로그 파일
    logger.add(
        LOG_FILE_ACCESS,
        format=LOG_FORMAT_ACCESS,
        level="INFO",
        filter=lambda record: record["extra"].get("access") is True,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )

    # 표준 로깅 모듈을 로구루로 리디렉션
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 다양한 라이브러리를 로구루로 리디렉션
    for log_name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging.getLogger(log_name).handlers = [InterceptHandler()]
        logging.getLogger(log_name).propagate = False

    # 로거 객체 반환
    return logger 