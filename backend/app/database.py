"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLAlchemy 엔진 생성
# Railway 환경에서는 연결 실패 시 재시도 로직 추가
is_railway = bool(os.getenv("PORT") or os.getenv("RAILWAY_ENVIRONMENT"))
database_url = None
engine = None

try:
    # Railway 환경에서 DATABASE_URL 검증
    database_url = settings.database_url
    
    if is_railway and not os.getenv("DATABASE_URL"):
        import logging
        logging.error("=" * 80)
        logging.error("Railway 환경에서 DATABASE_URL 환경 변수를 찾을 수 없습니다.")
        logging.error("")
        logging.error("해결 방법:")
        logging.error("1. Railway 대시보드 → 백엔드 서비스 → Variables 탭 확인")
        logging.error("2. PostgreSQL 서비스가 추가되어 있는지 확인")
        logging.error("3. 백엔드 서비스에서 PostgreSQL의 DATABASE_URL을 Variable Reference로 연결")
        logging.error("   (백엔드 서비스 Variables → New Variable → {} 아이콘 클릭 → PostgreSQL 서비스 선택)")
        logging.error("=" * 80)
        raise ValueError("DATABASE_URL environment variable is required in Railway environment. Please add PostgreSQL service and link DATABASE_URL via Variable Reference.")
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # 연결 유효성 검사
        echo=False,  # SQL 쿼리 로깅 (개발 시 True로 변경 가능)
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,  # 1시간마다 연결 재생성
    )
except ValueError as e:
    # Railway 환경에서 DATABASE_URL이 없을 때는 명확한 에러 메시지와 함께 raise
    import logging
    logging.error(str(e))
    raise
except Exception as e:
    import logging
    logging.error(f"Database engine creation failed: {e}")
    if database_url:
        logging.error(f"Database URL (masked): {database_url[:20]}...")
    else:
        logging.error("Database URL: None")
    # Railway 환경에서는 앱 시작을 막기 위해 raise
    if is_railway:
        logging.error("Railway 환경에서 DB 연결 실패 시 앱이 시작되지 않습니다.")
        raise
    # 로컬 환경에서는 경고만 출력하고 계속 진행 (선택사항)
    logging.warning(f"Database connection failed, but continuing in development mode: {e}")
    engine = None

# 세션 팩토리 (engine이 None일 수 있으므로 조건부 생성)
if engine is not None:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

# Base 클래스 (모델들이 상속받을 클래스)
Base = declarative_base()


def get_db():
    """
    FastAPI 의존성으로 사용할 DB 세션 생성 함수
    """
    if SessionLocal is None:
        raise RuntimeError("Database is not configured. Please set DATABASE_URL environment variable.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

