"""
FastAPI Main Application
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import router as api_router

# 로깅 설정 (중앙화된 설정 사용)
from app.utils.logger import setup_logging
setup_logging(level=settings.LOG_LEVEL)

app = FastAPI(
    title="Recipe Recommendation API",
    description="레시피 추천 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행되는 이벤트"""
    import os
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Application starting up...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"API Host: {settings.API_HOST}")
    logger.info(f"API Port: {settings.API_PORT}")
    logger.info(f"Database URL configured: {bool(os.getenv('DATABASE_URL'))}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info("=" * 80)

# CORS 설정
# Railway 환경에서는 FRONTEND_URL 또는 CORS_ORIGINS 환경 변수 설정 필요
cors_origins = settings.CORS_ORIGINS
# 빈 리스트이거나 "*"가 포함되어 있으면 모든 origin 허용
# 단, allow_credentials=True와 함께 "*"를 사용할 수 없으므로 주의
if not cors_origins:
    cors_origins = ["*"]
elif "*" in cors_origins:
    cors_origins = ["*"]

# allow_origins=["*"]와 allow_credentials=True는 함께 사용할 수 없음
# "*"를 사용할 때는 allow_credentials를 False로 설정
allow_credentials = "*" not in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router 등록
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Recipe Recommendation API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with DB connection test"""
    try:
        # DB 연결 테스트
        from sqlalchemy import text
        from app.database import SessionLocal
        
        if SessionLocal is None:
            return {
                "status": "ok",
                "database": "not_configured"
            }
        
        db = SessionLocal()
        try:
            # 간단한 쿼리로 연결 확인
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        finally:
            db.close()
        
        return {
            "status": "ok",
            "database": db_status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    
    # backend 디렉토리에서 실행되도록 경로 조정
    if os.path.basename(os.getcwd()) == "app":
        os.chdir("..")
        sys.path.insert(0, os.getcwd())
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level="info",  # uvicorn 로그 레벨 설정
        access_log=True,  # access log 활성화
    )
