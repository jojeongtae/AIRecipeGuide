"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLAlchemy 엔진 생성
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 연결 유효성 검사
    echo=False  # SQL 쿼리 로깅 (개발 시 True로 변경 가능)
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모델들이 상속받을 클래스)
Base = declarative_base()


def get_db():
    """
    FastAPI 의존성으로 사용할 DB 세션 생성 함수
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

