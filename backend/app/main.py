"""
FastAPI Main Application
"""
import logging
import traceback
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.api.v1 import router as api_router

# 로깅 설정 (중앙화된 설정 사용)
from app.utils.logger import setup_logging
setup_logging(level=settings.LOG_LEVEL)

logger = logging.getLogger(__name__)

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


# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """모든 요청을 로깅"""
    try:
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response: {request.method} {request.url.path} - {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing request {request.method} {request.url.path}: {e}", exc_info=True)
        raise

# 전역 예외 핸들러 추가
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러 - 모든 예외를 캐치하여 로깅"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.ENVIRONMENT == "development" else "An error occurred",
            "type": type(exc).__name__
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 오류 핸들러"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation error", "details": exc.errors()}
    )


# API Router 등록
try:
    app.include_router(api_router, prefix="/api/v1")
    logger.info("API router registered successfully")
except Exception as e:
    logger.error(f"Failed to register API router: {e}", exc_info=True)
    raise


@app.get("/")
async def root():
    """Health check endpoint - Railway uses this for health checks"""
    return {
        "message": "Recipe Recommendation API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/healthz")
async def healthz():
    """Alternative health check endpoint"""
    return {"status": "ok"}


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
