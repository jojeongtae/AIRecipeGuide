"""
SQLAlchemy Database Models
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ARRAY, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class Recipe(Base):
    """레시피 테이블"""
    __tablename__ = "recipes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    source_type = Column(String(20), nullable=False)  # 'crawler', 'llm', etc.
    source_url = Column(Text, nullable=True)
    ingredients = Column(JSONB, nullable=False)
    steps = Column(JSONB, nullable=False)
    cooking_time = Column(Integer, nullable=True)
    difficulty = Column(String(10), nullable=True)
    category = Column(String(50), nullable=True)
    serving_size = Column(Integer, nullable=True)
    image_url = Column(Text, nullable=True)
    nutrition_info = Column(JSONB, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    quality_score = Column(Float, nullable=True)
    validation_passed = Column(Boolean, nullable=True)
    nutrition_accuracy = Column(Float, nullable=True)
    step_completeness = Column(Float, nullable=True)
    view_count = Column(Integer, nullable=True)
    select_count = Column(Integer, nullable=True)
    avg_match_score = Column(Float, nullable=True)
    avg_rating = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=True)
    
    __table_args__ = (
        Index('idx_recipes_source_type', 'source_type'),
        Index('idx_recipes_category', 'category'),
        Index('idx_recipes_difficulty', 'difficulty'),
        Index('idx_recipes_quality_score', 'quality_score'),
        Index('idx_recipes_created_at', 'created_at'),
    )


class RecipeSearchCache(Base):
    """레시피 검색 결과 캐시 테이블"""
    __tablename__ = "recipe_search_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_hash = Column(String(64), nullable=False, unique=True)
    ingredients = Column(ARRAY(String), nullable=False)
    recipe_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    match_scores = Column(JSONB, nullable=True)
    filters = Column(JSONB, nullable=True)
    search_timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=True)
    expires_at = Column(TIMESTAMP, nullable=False)
    hit_count = Column(Integer, nullable=True, default=0)
    
    __table_args__ = (
        Index('idx_cache_ingredient_hash', 'ingredient_hash'),
        Index('idx_cache_expires_at', 'expires_at'),
    )


class UserSearchHistory(Base):
    """사용자 검색 히스토리 테이블"""
    __tablename__ = "user_search_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    ingredients = Column(ARRAY(String), nullable=False)
    filters = Column(JSONB, nullable=True)
    persona = Column(String(20), nullable=True)
    selected_recipe_id = Column(UUID(as_uuid=True), nullable=True)
    match_score = Column(Float, nullable=True)
    search_timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=True)
    
    __table_args__ = (
        Index('idx_history_user_id', 'user_id'),
        Index('idx_history_session_id', 'session_id'),
        Index('idx_history_timestamp', 'search_timestamp'),
    )


class IngredientMatchingCache(Base):
    """재료 매칭 캐시 테이블"""
    __tablename__ = "ingredient_matching_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_ingredient = Column(String(255), nullable=False)
    recipe_ingredient = Column(String(255), nullable=False)
    match_result = Column(JSONB, nullable=False)
    substitution_possible = Column(Boolean, nullable=True)
    llm_reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=True)
    hit_count = Column(Integer, nullable=True, default=0)
    
    __table_args__ = (
        Index('idx_matching_user_ingredient', 'user_ingredient'),
        Index('idx_matching_recipe_ingredient', 'recipe_ingredient'),
    )

