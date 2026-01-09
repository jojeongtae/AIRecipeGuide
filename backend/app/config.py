"""
Application Configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import List


def get_cors_origins() -> List[str]:
    """환경에 따라 CORS origins 자동 설정"""
    # 환경 변수가 명시적으로 설정되어 있으면 우선 사용
    cors_env = os.getenv("CORS_ORIGINS")
    if cors_env:
        return [origin.strip() for origin in cors_env.split(",")]
    
    # 배포 환경 감지 (Railway, Heroku 등)
    # Railway는 RAILWAY_ENVIRONMENT를 설정하지 않을 수 있으므로, 
    # Railway URL 패턴이나 PORT 환경 변수로도 감지
    is_production = (
        os.getenv("RAILWAY_ENVIRONMENT") or 
        os.getenv("DYNO") or 
        os.getenv("ENVIRONMENT") == "production" or
        os.getenv("PORT")  # Railway는 PORT 환경 변수를 설정함
    )
    
    if is_production:
        # 배포 환경: 프론트엔드 배포 주소 (필요시 .env에서 설정)
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url:
            # 여러 URL이 쉼표로 구분되어 있을 수 있음
            origins = [url.strip() for url in frontend_url.split(",")]
            # Railway 배포 도메인도 포함
            railway_backend_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
            if railway_backend_domain and railway_backend_domain not in origins:
                origins.append(f"https://{railway_backend_domain}")
            return origins
        else:
            # FRONTEND_URL이 없으면 Railway 배포 도메인 확인 또는 모든 origin 허용
            import logging
            railway_backend_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
            if railway_backend_domain:
                logging.info(f"Railway 배포 도메인 사용: https://{railway_backend_domain}")
                return [f"https://{railway_backend_domain}", "*"]
            else:
                logging.warning("FRONTEND_URL 환경 변수가 설정되지 않았습니다. 모든 origin을 허용합니다.")
                return ["*"]  # 임시로 모든 origin 허용
    else:
        # 로컬 환경
        return ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    # 포트 설정: 배포 환경(Railway 등)에서는 $PORT 사용, 로컬에서는 5000 사용
    API_PORT: int = int(os.getenv("PORT", "5000"))
    # 프로덕션 환경에서는 reload 비활성화 (Railway 등)
    API_RELOAD: bool = not bool(os.getenv("PORT") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENVIRONMENT") == "production")
    
    # LLM Provider
    OPENAI_API_KEY: str = ""
    
    # Tavily Search API
    TAVILY_API_KEY: str = ""
    
    # CORS (환경에 따라 자동 설정)
    CORS_ORIGINS: List[str] = get_cors_origins()
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # 매칭 점수 설정
    MATCH_SCORE_THRESHOLD: float = 30.0  # 매칭 점수 최소 임계값 (30점 미만 제외) - 완화
    CRAWLER_PRIORITY_THRESHOLD: float = 30.0  # 크롤링 우선 선택 임계값
    LLM_GENERATION_THRESHOLD: float = 50.0  # LLM 생성 임계값
    QUALITY_SCORE_INCREMENT: float = 20.0  # 품질 점수 증가량
    
    # Database
    # Railway는 DATABASE_URL 환경 변수를 자동으로 제공합니다
    # 로컬 환경에서는 개별 환경 변수 사용
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "recipe_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    
    @property
    def database_url(self) -> str:
        # Railway나 다른 플랫폼에서 DATABASE_URL이 제공되면 우선 사용
        database_url_env = os.getenv("DATABASE_URL")
        if database_url_env:
            # Railway는 postgres://로 시작하지만 SQLAlchemy는 postgresql://를 요구
            if database_url_env.startswith("postgres://"):
                database_url_env = database_url_env.replace("postgres://", "postgresql://", 1)
            return database_url_env
        
        # Railway 환경 감지
        is_railway = bool(os.getenv("PORT") or os.getenv("RAILWAY_ENVIRONMENT"))
        if is_railway:
            # Railway 환경에서는 DATABASE_URL이 필수
            import logging
            logging.warning("Railway 환경에서 DATABASE_URL이 설정되지 않았습니다. PostgreSQL 서비스를 추가해주세요.")
        
        # 로컬 환경: 개별 환경 변수로 구성
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # .env에 정의되지 않은 필드 무시


settings = Settings()

