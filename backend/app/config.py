"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 5000
    API_RELOAD: bool = True
    
    # LLM Provider
    OPENAI_API_KEY: str = ""
    
    # Tavily Search API
    TAVILY_API_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # 매칭 점수 설정
    MATCH_SCORE_THRESHOLD: float = 30.0  # 매칭 점수 최소 임계값 (30점 미만 제외) - 완화
    CRAWLER_PRIORITY_THRESHOLD: float = 30.0  # 크롤링 우선 선택 임계값
    LLM_GENERATION_THRESHOLD: float = 50.0  # LLM 생성 임계값
    QUALITY_SCORE_INCREMENT: float = 20.0  # 품질 점수 증가량
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # .env에 정의되지 않은 필드 무시


settings = Settings()

