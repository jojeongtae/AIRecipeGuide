"""
중앙화된 로깅 설정
모든 모듈에서 일관된 로깅을 사용하도록 설정
"""
import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """
    애플리케이션 전체 로깅 설정
    
    Args:
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: 커스텀 포맷 문자열 (None이면 기본 포맷 사용)
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)  # 표준 출력으로 강제
        ],
        force=True  # 기존 핸들러 덮어쓰기
    )
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # uvicorn 로거도 설정
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 가져오기
    
    Args:
        name: 모듈 이름 (보통 __name__ 사용)
    
    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    # 로거가 이미 설정되어 있으면 그대로 반환
    # 중복 핸들러 추가 방지
    if not logger.handlers:
        # 부모 로거의 핸들러를 상속받도록 설정
        logger.propagate = True
    return logger

